# reviews/views.py
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from users.permissions import ReviewPermissions
from .models import Review
from .serializers import ReviewSerializer


@method_decorator(ratelimit(key='ip', rate='100/m', method='POST', block=True), name='create')
@method_decorator(ratelimit(key='ip', rate='100/m', method='POST', block=True), name='approve')
@method_decorator(csrf_protect, name='create')
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermissions]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role in ["ADMIN", "LANDLORD"]:
            return Review.objects.all().order_by('-created_at')

        approved_reviews = Review.objects.filter(is_approved=True)
        user_reviews = Review.objects.filter(user=user)
        return (approved_reviews | user_reviews).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "TENANT":
            return Response({"error": _("Only tenants can create reviews.")}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[ReviewPermissions])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save()
        return Response({"message": _("Review approved")}, status=status.HTTP_200_OK)
