# booking/views.py
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from bookings.models import Booking
from bookings.permissions import IsOwnerOrAdmin, IsOwnerOrLandlordOrAdmin, IsAdminOrOwnerOrLandlordOrAdmin
from bookings.permissions import IsAdminOrOwnerOrLandlord
from bookings.serializers import BookingSerializer
from bookings.tasks import send_booking_notification
from listings.models import AvailabilitySlot
from users.models import User
from users.permissions import IsTenant
from django.utils.decorators import method_decorator
from django.utils.decorators import decorator_from_middleware
from django_ratelimit.middleware import RatelimitMiddleware
from django_ratelimit.core import is_ratelimited



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAdminOrOwnerOrLandlord]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Booking.objects.all().order_by("-created_at")

        if user.role == "LANDLORD":
            return Booking.objects.filter(listing__user=user).order_by("-created_at")

        if user.role == "TENANT":
            return Booking.objects.filter(user=user).order_by("-created_at")

        return Booking.objects.none()

    def perform_create(self, serializer):
        # Получаем user из тела запроса для админа
        user_id = self.request.data.get('user')
        if self.request.user.role == 'ADMIN' and user_id:
            user = User.objects.get(id=user_id)
        else:
            user = self.request.user

        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()

        # Разрешаем админу всё
        if request.user.role == 'ADMIN':
            return super().destroy(request, *args, **kwargs)

        # Только владелец или админ может удалять
        if request.user.role == 'TENANT' and booking.user != request.user:
            return Response(
                {"detail": "Not allowed."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)

    def get_user_role(self):
        return getattr(self.request.user, "role", None)

    def get_permissions(self):
        # ВАЖНО: нужно добавить этот метод обратно, но с правильной логикой.
        if self.action == "create":
            # Только Tenant может создавать бронирования
            return [permissions.IsAuthenticated(), IsTenant()]

        # Для всех остальных действий (GET, PUT, PATCH, DELETE, custom actions)
        # будет использоваться класс IsAdminOrOwnerOrLandlord
        return [IsAdminOrOwnerOrLandlord()]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        # ✅ Rate limit check
        was_limited = is_ratelimited(
            request=request,
            group='confirm-booking',  # 👈 обязательно укажи group
            key='user_or_ip',
            rate='100/m',
            method='POST',
            increment=True
        )
        if was_limited:
            return Response({"error": "Too many requests"}, status=429)

        booking = self.get_object()
        if not (
                (self.get_user_role() == "LANDLORD" and booking.listing.user == request.user)
                or self.get_user_role() == "ADMIN"
        ):
            raise PermissionDenied(
                _("Only the landlord of this listing or admin can confirm this booking.")
            )
        if booking.status != "PENDING":
            return Response(
                {"error": _("Only pending bookings can be confirmed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "CONFIRMED"
        booking.save()
        send_booking_notification.delay(booking.id, "Confirmed")
        serializer = self.get_serializer(booking)
        return Response({"data": serializer.data})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        # ✅ Rate limiting
        was_limited = is_ratelimited(
            request=request,
            group='cancel-booking',
            key='user_or_ip',
            rate='100/m',
            method='POST',
            increment=True
        )
        if was_limited:
            return Response({"error": "Too many requests"}, status=429)

        booking = self.get_object()
        role = self.get_user_role()

        if not (
                booking.user == request.user
                or (role == "LANDLORD" and booking.listing.user == request.user)
                or role == "ADMIN"
        ):
            raise PermissionDenied(_("You are not authorized to cancel this booking."))

        if booking.start_date < (timezone.now().date() + timedelta(days=2)):
            return Response(
                {"error": _("Cannot cancel within 48 hours of start date.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.status == "CANCELLED":
            return Response(
                {"error": _("Booking is already cancelled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        listing = booking.listing
        current_date = booking.start_date
        while current_date < booking.end_date:
            slot, created = AvailabilitySlot.objects.get_or_create(
                listing=listing,
                date=current_date,
                defaults={'is_available': True}
            )
            slot.is_available = True
            slot.save()
            current_date += timedelta(days=1)

        booking.status = "CANCELLED"
        booking.save()
        send_booking_notification.delay(booking.id, "Cancelled")
        serializer = self.get_serializer(booking)
        return Response({"data": serializer.data})
