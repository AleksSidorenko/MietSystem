### `reviews/views.py`

from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin, IsAuthenticated

from .models import Review
from .permissions import IsReviewOwnerOrAdmin
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_approved", "user", "booking__listing"]

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        serializer_class.Meta.swagger_schema_fields = {
            "description": "API for managing reviews of bookings"
        }
        return serializer_class

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            return self.queryset
        return self.queryset.filter(user=self.request.user) | self.queryset.filter(
            is_approved=True
        )

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if self.request.user.role != "TENANT":
            raise serializers.ValidationError(_("Only tenants can create reviews"))
        serializer.save(user=self.request.user)

        send_review_notification.delay(review.id)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "approve"]:
            return [IsAuthenticated(), IsReviewOwnerOrAdmin()]
        return super().get_permissions()

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin]
    )
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save()
        return Response({"message": _("Review approved")}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def export_csv(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="reviews_{timezone.now().date()}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                _("Review ID"),
                _("User"),
                _("Listing"),
                _("Rating"),
                _("Comment"),
                _("Is Approved"),
                _("Created At"),
            ]
        )
        reviews = Review.objects.select_related("user", "booking__listing").all()
        for review in reviews:
            writer.writerow(
                [
                    review.id,
                    review.user.email,
                    review.booking.listing.title,
                    review.rating,
                    review.comment,
                    review.is_approved,
                    review.created_at,
                ]
            )
        return response
