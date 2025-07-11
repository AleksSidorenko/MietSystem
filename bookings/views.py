### `booking/views.py`

from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from bookings.models import Booking
from bookings.permissions import IsOwnerOrLandlordOrAdmin
from bookings.serializers import BookingSerializer
from bookings.tasks import send_booking_notification


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BookingViewSet(ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete"]
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_user_role(self):
        return getattr(self.request.user, "role", None)

    def get_queryset(self):
        user = self.request.user
        role = self.get_user_role()
        if user.is_staff or user.is_superuser or role == "ADMIN":
            return Booking.objects.all()
        elif role == "TENANT":
            return Booking.objects.filter(user=user)
        elif role == "LANDLORD":
            return Booking.objects.filter(listing__user=user)
        return Booking.objects.none()

    def get_permissions(self):
        if self.action == "create":
            if self.get_user_role() != "TENANT":
                self.permission_denied(
                    self.request, message=_("Only tenants can create bookings.")
                )
            return [IsAuthenticated()]
        elif self.action in [
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            "confirm",
            "cancel",
        ]:
            return [IsAuthenticated(), IsOwnerOrLandlordOrAdmin()]
        elif self.action == "list":
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        if self.get_user_role() != "TENANT":
            raise PermissionDenied(_("Only tenants can create bookings."))

        booking = serializer.save(user=user)
        listing = booking.listing

        current_date = booking.start_date
        while current_date < booking.end_date:
            date_str = current_date.isoformat()
            if date_str in listing.availability:
                listing.availability[date_str] = False
            current_date += timedelta(days=1)
        listing.save()

        send_booking_notification.delay(booking.id, "Created")

    def format_response(self, booking, status_code=status.HTTP_200_OK):
        serializer = self.get_serializer(booking)
        return Response({"data": {"booking": serializer.data}}, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        return self.format_response(self.get_object())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self.format_response(
            serializer.instance, status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self.format_response(serializer.instance)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"data": response.data}, status=response.status_code)

    @action(detail=True, methods=["post"])
    @ratelimit(group="ip", rate="100/m")
    def confirm(self, request, pk=None):
        booking = self.get_object()

        if not (
            self.get_user_role() == "LANDLORD" and booking.listing.user == request.user
        ):
            raise PermissionDenied(
                _("Only the landlord of this listing can confirm this booking.")
            )

        if booking.status != "PENDING":
            return Response(
                {"error": _("Only pending bookings can be confirmed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "CONFIRMED"
        booking.save()
        send_booking_notification.delay(booking.id, "Confirmed")
        return self.format_response(booking)

    @action(detail=True, methods=["post"])
    @ratelimit(group="ip", rate="100/m")
    def cancel(self, request, pk=None):
        booking = self.get_object()
        role = self.get_user_role()

        if not (
            booking.user == request.user
            or (role == "LANDLORD" and booking.listing.user == request.user)
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
            date_str = current_date.isoformat()
            if date_str in listing.availability:
                listing.availability[date_str] = True
            current_date += timedelta(days=1)
        listing.save()

        booking.status = "CANCELLED"
        booking.save()
        send_booking_notification.delay(booking.id, "Cancelled")
        return self.format_response(booking)


# from datetime import timedelta
#
# from django.utils import timezone
# from django.utils.translation import gettext_lazy as _
# from django_ratelimit.decorators import ratelimit
#
# from rest_framework.viewsets import ModelViewSet
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from rest_framework.pagination import PageNumberPagination
# from rest_framework.permissions import IsAuthenticated
#
# from bookings.models import Booking
# from bookings.serializers import BookingSerializer
# from bookings.tasks import send_booking_notification
# from bookings.permissions import IsOwnerOrLandlordOrAdmin
# from bookings.permissions import IsBookingOwnerOrLandlordOrAdmin
#
#
# ## Настройки пагинации
# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100
#
# class BookingViewSet(ModelViewSet):
#     http_method_names = ['get', 'post', 'put', 'patch', 'delete']
#     queryset = Booking.objects.all()
#     permission_classes = [IsAuthenticated]
#     serializer_class = BookingSerializer
#
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role == 'ADMIN'):
#             return Booking.objects.all()
#         elif hasattr(user, 'role') and user.role == 'TENANT':
#             return Booking.objects.filter(user=user)
#         elif hasattr(user, 'role') and user.role == 'LANDLORD':
#             return Booking.objects.filter(listing__user=user)
#         return Booking.objects.none()
#
#     def get_permissions(self):
#         if self.action == 'create':
#             if not self.request.user.is_authenticated or self.request.user.role != 'TENANT':
#                 self.permission_denied(self.request, message="Only tenants can create bookings.")
#             return [IsAuthenticated()]
#         elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'confirm', 'cancel']:
#             return [IsAuthenticated(), IsOwnerOrLandlordOrAdmin()]
#         elif self.action == 'list':
#             return [IsAuthenticated()]
#         return super().get_permissions()
#
#     def perform_create(self, serializer):
#         user = self.request.user
#         if not user.is_authenticated or getattr(user, 'role', None) != 'TENANT':
#             raise permissions.PermissionDenied(_("Only tenants can create bookings."))
#
#         booking = serializer.save(user=user)  # 🔥 исправлено
#
#         listing = booking.listing
#         current_date = booking.start_date
#         while current_date < booking.end_date:
#             date_str = current_date.isoformat()
#             if date_str in listing.availability:
#                 listing.availability[date_str] = False
#             current_date += timedelta(days=1)
#         listing.save()
#         send_booking_notification.delay(booking.id, 'Created')
#
#     @action(detail=True, methods=['post'])
#     @ratelimit(group='ip', rate='100/m')
#     def confirm(self, request, pk=None):
#         """
#         Подтверждает бронирование. Доступно только арендодателю, владеющему объявлением,
#         и только если статус бронирования 'PENDING'.
#         """
#         booking = self.get_object()  # get_object() уже применяет разрешения
#
#         # Дополнительная проверка, чтобы убедиться, что арендодатель является владельцем именно этого объявления
#         if not (request.user.role == 'LANDLORD' and booking.listing.user == request.user):
#             return Response({"error": _("Only the landlord of this listing can confirm this booking.")},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         if booking.status != 'PENDING':
#             return Response({"error": _("Only pending bookings can be confirmed.")}, status=status.HTTP_400_BAD_REQUEST)
#
#         booking.status = 'CONFIRMED'
#         booking.save()
#         send_booking_notification.delay(booking.id, 'Confirmed')
#         return Response({"message": _("Booking confirmed.")}, status=status.HTTP_200_OK)
#
#     @action(detail=True, methods=['post'])
#     @ratelimit(group='ip', rate='100/m')
#     def cancel(self, request, pk=None):
#         """
#         Отменяет бронирование. Доступно владельцу бронирования или арендодателю.
#         Невозможно отменить за 48 часов до даты начала.
#         """
#         booking = self.get_object()  # get_object() уже применяет разрешения
#
#         # Проверка, кто может отменить: владелец бронирования ИЛИ арендодатель объявления
#         if not (booking.user == request.user or \
#                 (request.user.role == 'LANDLORD' and booking.listing.user == request.user)):
#             return Response({"error": _("You are not authorized to cancel this booking.")},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         if booking.start_date < (timezone.now().date() + timedelta(days=2)):
#             return Response({"error": _("Cannot cancel within 48 hours of start date.")},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         if booking.status == 'CANCELLED':
#             return Response({"error": _("Booking is already cancelled.")}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Возвращаем доступность дат при отмене бронирования
#         listing = booking.listing
#         current_date = booking.start_date
#         while current_date < booking.end_date:
#             date_str = current_date.isoformat()
#             if date_str in listing.availability:  # Проверяем, существует ли дата в availability
#                 listing.availability[date_str] = True  # Делаем дату снова доступной
#             current_date += timedelta(days=1)
#         listing.save()  # Сохраняем изменения в доступности объявления
#
#         booking.status = 'CANCELLED'
#         booking.save()
#         send_booking_notification.delay(booking.id, 'Cancelled')
#         return Response({"message": _("Booking cancelled.")}, status=status.HTTP_200_OK)
#
#     def format_response(self, booking, status_code=status.HTTP_200_OK):
#         serializer = self.get_serializer(booking)
#         return Response({"data": {"booking": serializer.data}}, status=status_code)
#
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         return self.format_response(instance)
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return self.format_response(serializer.instance, status_code=status.HTTP_201_CREATED)
#
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return self.format_response(serializer.instance)
#
#     def partial_update(self, request, *args, **kwargs):
#         kwargs['partial'] = True
#         return self.update(request, *args, **kwargs)
#
#     def list(self, request, *args, **kwargs):
#         response = super().list(request, *args, **kwargs)
#         return Response({"data": response.data}, status=response.status_code)
