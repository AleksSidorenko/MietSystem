# bookings/tests/test_serializers.py

from datetime import date, timedelta

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from bookings.models import Booking
from bookings.serializers import BookingSerializer
from users.models import User  # Убедитесь, что это правильный путь к вашей модели User


class TestBookingSerializer:

    def test_valid_booking_data(self, listing, regular_user):
        """
        Тест на успешную валидацию с корректными данными.
        """
        listing.is_active = True
        listing.price_per_night = 100.00  # Установим цену для расчета
        listing.availability = {
            (date.today() + timedelta(days=1)).isoformat(): True,
            (date.today() + timedelta(days=2)).isoformat(): True,
            (date.today() + timedelta(days=3)).isoformat(): True,
        }
        listing.save()

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data)
        # serializer = BookingSerializer(data=payload, context={'request': request})

        assert serializer.is_valid(raise_exception=True)
        # Ожидаем, что total_price будет вычислен сериализатором
        assert (
            serializer.validated_data["total_price"] == 2 * listing.price_per_night
        )  # 2 ночи

    def test_cannot_book_inactive_listing(self, listing, regular_user):
        """
        Тест на ошибку при бронировании неактивного объявления.
        """
        listing.is_active = False
        listing.save()

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=2)).isoformat(),
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert (
            "listing is not active" in str(excinfo.value).lower()
        )  # Проверяем сообщение об ошибке

    def test_end_date_before_start_date(self, listing, regular_user):
        """
        Тест на ошибку, если дата выезда раньше или равна дате заезда.
        """
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=5)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        # Обновленное ожидаемое сообщение
        assert "end date must be after start date" in str(excinfo.value).lower()

    def test_booking_duration_too_short(self, listing, regular_user):
        """
        Тест на ошибку, если продолжительность бронирования меньше 1 дня.
        """
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (
                date.today() + timedelta(days=1)
            ).isoformat(),  # То же самое, что и start_date
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(
            ValidationError
        ) as excinfo:  # Добавлено raise_exception=True
            serializer.is_valid(raise_exception=True)
        # Ожидаем, что ошибка будет о том, что конечная дата должна быть после начальной
        assert "end date must be after start date" in str(excinfo.value).lower()

        # assert 'end date must be after start date' in str(serializer.errors)

    def test_booking_duration_too_long(self, listing, regular_user):
        """
        Тест на ошибку, если продолжительность бронирования больше 30 дней.
        """
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=32)).isoformat(),  # 31 день
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        # Обновленное ожидаемое сообщение
        assert "booking duration cannot exceed 30 days" in str(excinfo.value).lower()

    def test_dates_overlap_with_existing_booking(self, listing, regular_user):
        """
        Тест на ошибку, если даты пересекаются с существующим подтвержденным бронированием.
        """
        # Создаем существующее бронирование
        Booking.objects.create(
            listing=listing,
            user=regular_user,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            status="CONFIRMED",
            total_price=5
            * listing.price_per_night,  # Убедимся, что total_price установлен
        )

        data = {
            "listing": listing.id,
            "start_date": (
                date.today() + timedelta(days=7)
            ).isoformat(),  # Пересекается
            "end_date": (date.today() + timedelta(days=12)).isoformat(),
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(
            ValidationError
        ) as excinfo:  # Добавлено raise_exception=True
            serializer.is_valid(raise_exception=True)
        assert "dates overlap with an existing booking" in str(excinfo.value).lower()

    def test_dates_overlap_with_pending_booking(self, listing, regular_user):
        """
        Тест на ошибку, если даты пересекаются с существующим ожидающим бронированием.
        """
        # Создаем существующее бронирование
        Booking.objects.create(
            listing=listing,
            user=regular_user,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            status="PENDING",
            total_price=5
            * listing.price_per_night,  # Убедимся, что total_price установлен
        )

        data = {
            "listing": listing.id,
            "start_date": (
                date.today() + timedelta(days=7)
            ).isoformat(),  # Пересекается
            "end_date": (date.today() + timedelta(days=12)).isoformat(),
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(
            ValidationError
        ) as excinfo:  # Добавлено raise_exception=True
            serializer.is_valid(raise_exception=True)
        assert "dates overlap with an existing booking" in str(excinfo.value).lower()

    def test_selected_dates_not_available(self, listing, regular_user):
        """
        Тест на ошибку, если выбранные даты недоступны.
        """
        listing.is_active = True
        listing.availability = {
            (date.today() + timedelta(days=1)).isoformat(): True,
            (date.today() + timedelta(days=2)).isoformat(): False,  # День недоступен
            (date.today() + timedelta(days=3)).isoformat(): True,
        }
        listing.save()

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (
                date.today() + timedelta(days=3)
            ).isoformat(),  # Включает недоступный день
        }
        serializer = BookingSerializer(data=data)
        with pytest.raises(
            ValidationError
        ) as excinfo:  # Добавлено raise_exception=True
            serializer.is_valid(raise_exception=True)
        assert "is not available for booking" in str(excinfo.value).lower()

    def test_total_price_calculation(self, listing, regular_user):
        """
        Тест на корректный расчет общей стоимости.
        """
        listing.is_active = True
        listing.price_per_night = 75.00
        listing.availability = {
            (date.today() + timedelta(days=1)).isoformat(): True,
            (date.today() + timedelta(days=2)).isoformat(): True,
            (date.today() + timedelta(days=3)).isoformat(): True,
            (date.today() + timedelta(days=4)).isoformat(): True,
        }
        listing.save()

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=4)).isoformat(),  # 3 ночи
        }
        serializer = BookingSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        expected_total_price = 3 * 75.00
        assert serializer.validated_data["total_price"] == expected_total_price

    from rest_framework.test import APIRequestFactory

    def test_create_method_total_price_set(self, listing, regular_user):
        """
        Тест, что total_price устанавливается при создании.
        """
        listing.is_active = True
        listing.price_per_night = 100.00
        listing.availability = {
            (date.today() + timedelta(days=1)).isoformat(): True,
            (date.today() + timedelta(days=2)).isoformat(): True,
            (date.today() + timedelta(days=3)).isoformat(): True,
        }
        listing.save()

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),  # 2 ночи
        }

        # ✅ создаём мок-запрос с пользователем
        factory = APIRequestFactory()
        request = factory.post("/fake-url/")
        request.user = regular_user

        # ✅ передаём request через context
        serializer = BookingSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

        booking_instance = (
            serializer.save()
        )  # теперь `user` будет установлен автоматически в create()
        assert booking_instance.total_price == 2 * listing.price_per_night
        assert booking_instance.status == "PENDING"


# import pytest
# from datetime import date, timedelta
# from rest_framework.exceptions import ValidationError
# from bookings.serializers import BookingSerializer
# from listings.models import Listing
# from bookings.models import Booking
# from users.models import User
#
#
# class TestBookingSerializer:
#
#     def test_valid_booking_data(self, listing, regular_user):
#         """
#         Тест на успешную валидацию с корректными данными.
#         """
#         # Убедимся, что объявление активно и даты доступны
#         listing.is_active = True
#         listing.availability = {
#             (date.today() + timedelta(days=1)).isoformat(): True,
#             (date.today() + timedelta(days=2)).isoformat(): True,
#             (date.today() + timedelta(days=3)).isoformat(): True,
#         }
#         listing.save()
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=3),
#         }
#         serializer = BookingSerializer(data=data)
#         assert serializer.is_valid(raise_exception=True)
#         assert serializer.validated_data['total_price'] == 2 * listing.price_per_night # 2 дня
#         assert serializer.validated_data['listing'] == listing
#
#     def test_cannot_book_inactive_listing(self, listing, regular_user):
#         """
#         Тест на ошибку при бронировании неактивного объявления.
#         """
#         listing.is_active = False
#         listing.save()
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=2),
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'Cannot book an inactive listing' in str(excinfo.value)
#
#     def test_end_date_before_start_date(self, listing, regular_user):
#         """
#         Тест на ошибку, если дата выезда раньше или равна дате заезда.
#         """
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=5),
#             'end_date': date.today() + timedelta(days=3),
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'End date must be after start date' in str(excinfo.value)
#
#     def test_start_date_in_past(self, listing, regular_user):
#         """
#         Тест на ошибку, если дата заезда в прошлом.
#         """
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() - timedelta(days=1),
#             'end_date': date.today() + timedelta(days=1),
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'Start date cannot be in the past' in str(excinfo.value)
#
#     def test_booking_duration_too_short(self, listing, regular_user):
#         """
#         Тест на ошибку, если продолжительность бронирования меньше 1 дня.
#         (Хотя 'start_date >= end_date' уже покроет 0 дней)
#         """
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=1), # То же самое, что и start_date
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'End date must be after start date' in str(excinfo.value) # Это срабатывает первым
#
#     def test_booking_duration_too_long(self, listing, regular_user):
#         """
#         Тест на ошибку, если продолжительность бронирования больше 30 дней.
#         """
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=32), # 31 день
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'Booking duration must be between 1 and 30 days' in str(excinfo.value)
#
#     def test_dates_overlap_with_existing_booking(self, listing, regular_user):
#         """
#         Тест на ошибку, если даты пересекаются с существующим подтвержденным бронированием.
#         """
#         # Создаем существующее бронирование
#         Booking.objects.create(
#             listing=listing,
#             user=regular_user, # Используем 'user' вместо 'guest'
#             start_date=date.today() + timedelta(days=5),
#             end_date=date.today() + timedelta(days=10),
#             status='CONFIRMED',
#             total_price=500
#         )
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=7), # Пересекается
#             'end_date': date.today() + timedelta(days=12),
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'Dates overlap with existing booking' in str(excinfo.value)
#
#     def test_dates_overlap_with_pending_booking(self, listing, regular_user):
#         """
#         Тест на ошибку, если даты пересекаются с существующим ожидающим бронированием.
#         """
#         # Создаем существующее бронирование
#         Booking.objects.create(
#             listing=listing,
#             user=regular_user,
#             start_date=date.today() + timedelta(days=5),
#             end_date=date.today() + timedelta(days=10),
#             status='PENDING',
#             total_price=500
#         )
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=7), # Пересекается
#             'end_date': date.today() + timedelta(days=12),
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         assert 'Dates overlap with existing booking' in str(excinfo.value)
#
#     def test_selected_dates_not_available(self, listing, regular_user):
#         """
#         Тест на ошибку, если выбранные даты недоступны.
#         """
#         listing.is_active = True
#         listing.availability = {
#             (date.today() + timedelta(days=1)).isoformat(): True,
#             (date.today() + timedelta(days=2)).isoformat(): False,  # День недоступен
#             (date.today() + timedelta(days=3)).isoformat(): True,
#         }
#         listing.save()
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=3),  # Включает недоступный день
#         }
#         serializer = BookingSerializer(data=data)
#         with pytest.raises(ValidationError) as excinfo:
#             serializer.is_valid(raise_exception=True)
#         # ИЗМЕНЕНИЕ ЗДЕСЬ: Проверяем часть сообщения, которое содержит дату
#         assert f"Date {(date.today() + timedelta(days=2)).isoformat()} is not available for booking." in str(
#             excinfo.value)
#
#     def test_total_price_calculation(self, listing, regular_user):
#         """
#         Тест на корректный расчет общей стоимости.
#         """
#         listing.is_active = True
#         listing.price_per_night = 75.00
#         listing.availability = {
#             (date.today() + timedelta(days=1)).isoformat(): True,
#             (date.today() + timedelta(days=2)).isoformat(): True,
#             (date.today() + timedelta(days=3)).isoformat(): True,
#             (date.today() + timedelta(days=4)).isoformat(): True,
#         }
#         listing.save()
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=4), # 3 ночи
#         }
#         serializer = BookingSerializer(data=data)
#         assert serializer.is_valid(raise_exception=True)
#         expected_total_price = 3 * 75.00
#         assert serializer.validated_data['total_price'] == expected_total_price
#
#     def test_create_method_total_price_set(self, listing, regular_user):
#         """
#         Тест, что total_price устанавливается при создании.
#         """
#         listing.is_active = True
#         listing.price_per_night = 100.00
#         listing.availability = {
#             (date.today() + timedelta(days=1)).isoformat(): True,
#             (date.today() + timedelta(days=2)).isoformat(): True,
#             (date.today() + timedelta(days=3)).isoformat(): True,
#         }
#         listing.save()
#
#         data = {
#             'listing': listing.id,
#             'start_date': date.today() + timedelta(days=1),
#             'end_date': date.today() + timedelta(days=3), # 2 ночи
#         }
#         serializer = BookingSerializer(data=data)
#         assert serializer.is_valid(raise_exception=True)
#         # Для метода create нам нужен 'user' в validated_data
#         validated_data = serializer.validated_data
#         validated_data['user'] = regular_user # Устанавливаем пользователя, так как он read_only
#         booking_instance = serializer.create(validated_data)
#
#         assert booking_instance.total_price == 2 * listing.price_per_night
#         assert booking_instance.user == regular_user
#         assert booking_instance.listing == listing
#         assert booking_instance.start_date == data['start_date']
#         assert booking_instance.end_date == data['end_date']
