# core/views.py

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.http import HttpResponse
from django.utils.timezone import now

from bookings.models import Booking
from listings.models import Listing
from reviews.models import Review

User = get_user_model()


def status_page_view(request):
    # Проверка соединения с БД
    try:
        connection.ensure_connection()
        db_status = "🟢 Online"
    except Exception:
        db_status = "🔴 Offline"

    # Статистика
    user_count = User.objects.count()
    landlord_count = User.objects.filter(role="landlord").count()
    tenant_count = User.objects.filter(role="tenant").count()
    admin_count = User.objects.filter(is_superuser=True).count()

    listing_count = Listing.objects.count()
    booking_count = Booking.objects.count()
    review_count = Review.objects.count()

    current_time = now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <html>
    <head>
        <title>MietSystem — System Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 2rem;
                background-color: #f9f9f9;
                color: #333;
            }}
            h1 {{
                color: #222;
            }}
            .section {{
                margin-bottom: 2rem;
            }}
            ul {{
                list-style: none;
                padding-left: 0;
            }}
            li {{
                padding: 0.3rem 0;
            }}
            .code {{
                font-family: monospace;
                background: #eee;
                padding: 2px 5px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <h1>MietSystem — Статус системы</h1>
        <div class="section">
            <strong>🕓 Текущее серверное время:</strong> {current_time}
        </div>
        <div class="section">
            <strong>🟢 Статус базы данных:</strong> {db_status}
        </div>
        <div class="section">
            <strong>👤 Пользователи:</strong>
            <ul>
                <li>Всего: {user_count}</li>
                <li>👑 Админы: {admin_count}</li>
                <li>🧑‍💼 Арендодатели: {landlord_count}</li>
                <li>🧑‍💻 Арендаторы: {tenant_count}</li>
            </ul>
        </div>
        <div class="section">
            <strong>📊 Объекты:</strong>
            <ul>
                <li>📢 Объявлений: {listing_count}</li>
                <li>📅 Бронирований: {booking_count}</li>
                <li>⭐ Отзывов: {review_count}</li>
            </ul>
        </div>
        <div class="section">
            <strong>🔗 Быстрые ссылки:</strong>
            <ul>
                <li><a href="/admin/">Админка</a></li>
                <li><a href="/api/swagger/">Swagger</a></li>
                <li><a href="/api/redoc/">Redoc</a></li>
                <li><a href="/api/users/token/">JWT Login</a></li>
                <li><a href="/api/users/me/">Профиль пользователя</a></li>
                <li><a href="/api/listings/">Объявления</a></li>
                <li><a href="/api/bookings/">Бронирования</a></li>
                <li><a href="/api/reviews/">Отзывы</a></li>
            </ul>
        </div>
        <div class="section">
            <strong>🌍 Поддержка языков:</strong>
            <ul>
                <li>🇺🇸 Английский</li>
                <li>🇩🇪 Немецкий</li>
                <li>🇷🇺 Русский</li>
            </ul>
        </div>
        {"<div class='section'><strong>🧪 Тестовые логины (DEBUG):</strong><ul><li>tenant1 / pass123</li><li>landlord1 / pass456</li><li>admin / adminpass</li></ul></div>" if settings.DEBUG else ""}
    </body>
    </html>
    """
    return HttpResponse(html)


# from django.http import HttpResponse
# from users.models import User
# from listings.models import Listing
# from bookings.models import Booking
# from reviews.models import Review
# from django.db import connection
#
#
# def healthcheck_view(request):
#     try:
#         connection.ensure_connection()
#         db_status = "🟢 OK"
#         users = User.objects.count()
#         listings = Listing.objects.count()
#         bookings = Booking.objects.count()
#         reviews = Review.objects.count()
#     except Exception as e:
#         return HttpResponse(
#             f"<h1>❌ Ошибка подключения к Базе Данных</h1><pre>{str(e)}</pre>",
#             status=500,
#         )
#
#     html = f"""
#     <html>
#     <head>
#         <title>MietSystem Status</title>
#     </head>
#     <body style="font-family:sans-serif; padding:2rem;">
#         <h1>🏠 MietSystem — Backend Сводка</h1>
#         <p><b>📦 Статус базы данных:</b> {db_status}</p>
#         <ul>
#             <li>👤 Пользователей: <b>{users}</b></li>
#             <li>📢 Объявлений: <b>{listings}</b></li>
#             <li>📅 Бронирований: <b>{bookings}</b></li>
#             <li>⭐ Отзывов: <b>{reviews}</b></li>
#         </ul>
#         <hr />
#         <h3>🔗 Быстрые ссылки</h3>
#         <ul>
#             <li><a href="/admin/">Админка</a></li>
#             <li><a href="/api/swagger/">Swagger UI</a></li>
#             <li><a href="/api/redoc/">ReDoc</a></li>
#         </ul>
#     </body>
#     </html>
#     """
#     return HttpResponse(html)
