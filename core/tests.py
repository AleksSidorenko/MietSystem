# core/tests.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            email="testuser@example.com",  # Обязательное поле, USERNAME_FIELD
            password="testpass",
            first_name="Test",  # Обязательное поле
            last_name="User",  # Обязательное поле
            role="ADMIN",  # Обязательное поле
            phone_number="1234567890",  # Необязательное поле, но добавим для полноты
            language="en",  # Необязательное поле, но добавим для теста
            is_active=True,
            is_verified=True,
            is_staff=True,  # Для доступа к админке
            is_superuser=True,  # Для доступа к админке
        )
        self.client.login(email="testuser@example.com", password="testpass")

    def test_health_check_api(self):
        response = self.api_client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

    def test_status_page_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access Denied")

    def test_status_page_authenticated(self):
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Information")

    def test_status_page_localization(self):
        response = self.client.get(reverse("status"))
        self.assertContains(response, "System Information")
        self.assertEqual(translation.get_language(), "en")

    def test_language_switch(self):
        # Тест для английского
        response = self.client.get(reverse("status"))
        self.assertContains(response, "System Information")
        self.assertEqual(translation.get_language(), "en")

        # Переключение на русский
        response = self.client.post(
            "/i18n/set_language/", {"language": "ru", "next": reverse("status")}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, "Системная информация")
        self.assertEqual(translation.get_language(), "ru")

        # Переключение на немецкий
        response = self.client.post(
            "/i18n/set_language/", {"language": "de", "next": reverse("status")}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, "Systeminformation")
        self.assertEqual(translation.get_language(), "de")

        # Обратное переключение на английский
        response = self.client.post(
            "/i18n/set_language/", {"language": "en", "next": reverse("status")}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, "System Information")
        self.assertEqual(translation.get_language(), "en")

    def test_status_page_data(self):
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["data"]["users"]["total"], 100)
        self.assertEqual(response.context["data"]["system_metrics"]["cpu_percent"], 25)

    def test_debug_block(self):
        response = self.client.get(reverse("status"))
        self.assertContains(response, "Debug Information")
        self.assertContains(response, "admin / adminpass")

    def test_system_metrics(self):
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["data"]["system_metrics"]["disk_free_gb"], 100
        )
        self.assertEqual(response.context["data"]["system_metrics"]["celery_tasks"], 10)

    def test_localization_status(self):
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["data"]["localization"]["status"])
        self.assertEqual(
            response.context["data"]["localization"]["languages"], ["en", "ru", "de"]
        )

    def test_stats_data(self):
        response = self.client.get(reverse("status"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["data"]["stats"]["listings"], 50)
        self.assertEqual(response.context["data"]["stats"]["bookings"], 30)
