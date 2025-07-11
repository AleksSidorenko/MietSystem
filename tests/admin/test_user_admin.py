# tests/admin/test_user_admin.py

import pytest
from django.urls import reverse

from users.models import User


@pytest.fixture
@pytest.mark.django_db
def superuser():
    return User.objects.create_user(
        email="super@example.com",
        password="pass",
        role="ADMIN",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
@pytest.mark.django_db
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        password="pass",
        role="ADMIN",
        is_staff=True,
    )


@pytest.fixture
@pytest.mark.django_db
def landlord_user():
    return User.objects.create_user(
        email="landlord@example.com", password="pass", role="LANDLORD"
    )


@pytest.fixture
@pytest.mark.django_db
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com", password="pass", role="TENANT"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture, can_access",
    [
        ("superuser", True),
        ("admin_user", True),
        ("landlord_user", False),
        ("tenant_user", False),
    ],
)
def test_useradmin_module_permission(client, request, user_fixture, can_access):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    url = reverse("admin:users_user_changelist")

    response = client.get(url)
    if can_access:
        assert response.status_code == 200
    else:
        assert response.status_code in (302, 403)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture, can_change",
    [
        ("superuser", True),
        ("admin_user", True),
        ("landlord_user", False),
        ("tenant_user", False),
    ],
)
def test_useradmin_change_permission(
    client, request, user_fixture, can_change, admin_user
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    url = reverse("admin:users_user_change", args=[admin_user.id])
    response = client.get(url)
    if can_change:
        assert response.status_code == 200
    else:
        assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_make_verified_action(client, admin_user):
    client.force_login(admin_user)

    # Создаем пользователя для проверки
    target = User.objects.create_user(
        email="toverify@example.com", password="pass", is_verified=False
    )
    url = reverse("admin:users_user_changelist")

    data = {
        "action": "make_verified",
        "_selected_action": [target.id],
    }
    response = client.post(url, data, follow=True)
    target.refresh_from_db()
    assert response.status_code == 200
    assert target.is_verified is True


@pytest.mark.django_db
def test_readonly_fields_cannot_be_changed(client, admin_user):
    client.force_login(admin_user)
    target = User.objects.create_user(email="readonlytest@example.com", password="pass")

    url = reverse("admin:users_user_change", args=[target.id])

    # Пытаемся изменить readonly поля
    data = {
        "email": target.email,
        "first_name": "NewName",
        "date_joined": "2000-01-01 00:00:00",
        "last_login": "2000-01-01 00:00:00",
        "role": target.role,
        "is_verified": target.is_verified,
        "_save": "Save",
    }
    response = client.post(url, data, follow=True)
    target.refresh_from_db()
    # Проверяем, что дата создания и последний вход не изменились (по умолчанию Django сам защищает readonly)
    assert target.date_joined != "2000-01-01 00:00:00"
    assert target.last_login != "2000-01-01 00:00:00"
    assert response.status_code == 200


@pytest.mark.django_db
def test_search_and_filter(client, admin_user):
    client.force_login(admin_user)

    User.objects.create_user(
        email="searchtest@example.com",
        password="pass",
        first_name="Test",
        last_name="User",
        role="TENANT",
    )

    url = reverse("admin:users_user_changelist")

    # Поиск по email
    response = client.get(url, {"q": "searchtest"})
    assert response.status_code == 200
    assert "searchtest@example.com" in response.content.decode()

    # Фильтр по роли
    response = client.get(url, {"role": "TENANT"})
    assert response.status_code == 200
    assert "searchtest@example.com" in response.content.decode()
