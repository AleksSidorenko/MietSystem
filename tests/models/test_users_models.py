# tests/models/test_users_models.py
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from users.models import User, VerificationToken


@pytest.mark.django_db
def test_user_creation_required_fields():
    # Проверяем, что без first_name и last_name валидация падает
    with pytest.raises(ValidationError, match='first_name.*last_name'):
        User.objects.create(email='test@example.com').full_clean()


@pytest.mark.django_db
def test_user_history(tenant_user):
    # Меняем имя и проверяем, что запись в history создаётся
    tenant_user.first_name = 'Updated'
    tenant_user.save()
    assert tenant_user.history.count() == 2  # Создание + обновление
    assert tenant_user.history.latest().first_name == 'Updated'


@pytest.mark.django_db
def test_verification_token_expiry():
    user = User.objects.create(
        email='test@example.com',
        first_name='T',
        last_name='U',
        role='TENANT'
    )
    token = VerificationToken.objects.create(user=user, token='abc123')
    assert token.expires_at.date() == (timezone.now() + timedelta(hours=24)).date()
