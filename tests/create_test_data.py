# create_test_data.py

from django.contrib.auth import get_user_model

from listings.models import Listing

User = get_user_model()

user, _ = User.objects.get_or_create(
    email="admin@example.com",
    defaults={
        "password": "adminpass",
        "first_name": "Админ",
        "last_name": "Пользователь",
        "role": "ADMIN",
    },
)

listing, _ = Listing.objects.get_or_create(
    user=user,
    address="ул. Примерная, 124",
    defaults={
        "title_en": "Test Listing",
        "title_de": "Testanzeige",
        "title_ru": "Тестовое объявление",
        "description_en": "This is a test listing.",
        "description_de": "Dies ist eine Testanzeige.",
        "description_ru": "Это тестовое объявление.",
        "city": "Берлин",
        "federal_state": "Берлин",
        "price_per_night": 100.00,
        "rooms": 2.5,
        "property_type": "Квартира",
    },
)

print(f"🌍 {listing.title_en} {listing.title_de} {listing.title_ru}")
