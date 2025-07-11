### `reviews/serializers.py`

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from utils.translation import TranslationSerializerMixin

from .models import Review


class ReviewSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "booking",
            "rating",
            "comment",
            "is_approved",
            "created_at",
        ]
        read_only_fields = ["id", "user", "is_approved", "created_at"]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(_("Rating must be between 1 and 5"))
        return value

    def validate(self, data):
        booking = data["booking"]
        if booking.status != "CONFIRMED":
            raise serializers.ValidationError(
                _("Review can only be created for confirmed bookings")
            )
        if booking.user != self.context["request"].user:
            raise serializers.ValidationError(
                _("Only the booking owner can create a review")
            )
        if booking.end_date > timezone.now().date():
            raise serializers.ValidationError(
                _("Review can only be created after the booking end date")
            )
        return data

    def validate_comment(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError(
                _("Comment must be less than 1000 characters")
            )
        return value


# from rest_framework import serializers
# from .models import Review
#
# class ReviewSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Review
#         fields = ['id', 'user', 'booking', 'rating', 'comment', 'is_approved', 'created_at']
#         read_only_fields = ['is_approved', 'created_at']
#
#     def validate_rating(self, value):
#         if not 1 <= value <= 5:
#             raise serializers.ValidationError("Rating must be between 1 and 5")
#         return value
#
#     def validate(self, data):
#         if data['booking'].status != 'CONFIRMED':
#             raise serializers.ValidationError("Review can only be created for confirmed bookings")
#         return data
