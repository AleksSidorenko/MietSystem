# tests/models/test_reviews.py
import pytest
from django.core.exceptions import ValidationError
from reviews.models import Review

@pytest.mark.django_db
def test_review_creation(review):
    assert review.rating == 4
    assert review.comment == "Nice place to stay!"
    assert review.history.exists()

@pytest.mark.django_db
def test_review_unique_per_booking(booking, tenant_user):
    booking.status = "COMPLETED"
    booking.save()
    from reviews.models import Review as ReviewModel
    ReviewModel.objects.create(booking=booking, user=tenant_user, rating=4, comment="Good")
    with pytest.raises(ValidationError):
        ReviewModel(booking=booking, user=tenant_user, rating=5, comment="Again").full_clean()

@pytest.mark.django_db
def test_review_invalid_rating(booking, tenant_user):
    booking.status = "COMPLETED"
    booking.save()
    review = Review(booking=booking, user=tenant_user, rating=6, comment='Invalid')
    with pytest.raises(ValidationError, match='between 1 and 5'):
        review.full_clean()
    # review = Review(booking=booking, user=tenant_user, rating=6, comment="Invalid")
    # with pytest.raises(ValidationError):
    #     review.full_clean()
