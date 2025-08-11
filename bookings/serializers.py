# bookings/serializers.py
from datetime import date, timedelta, datetime
from django.db.models import Q
from rest_framework import serializers
from django.contrib.auth.models import AnonymousUser  # <-- Добавлено
from bookings.models import Booking
from listings.models import AvailabilitySlot

from users.models import User  # или кастомная модель
from listings.models import Listing


class BookingSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='booking-detail')
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Booking
        fields = ['url', 'id', 'start_date', 'end_date', 'total_price', 'status', 'created_at', 'user', 'listing']
        read_only_fields = ['id', 'status', 'created_at', 'total_price']  # <-- total_price теперь read_only

    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        if not request or not request.user or isinstance(request.user, AnonymousUser):
            raise serializers.ValidationError("Authentication is required to create a booking.")

        is_create = request and request.method == "POST"

        listing = data.get("listing") or getattr(self.instance, "listing", None)
        start_date = data.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = data.get("end_date") or getattr(self.instance, "end_date", None)

        if not listing or not start_date or not end_date:
            raise serializers.ValidationError("Missing required fields for validation.")

        if not listing.is_active:
            raise serializers.ValidationError({"listing": ["Cannot book an inactive listing."]})

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date >= end_date:
            raise serializers.ValidationError(
                {"non_field_errors": ["End date must be after start date."]}
            )
        current_date = start_date
        while current_date < end_date:
            print(f"Checking availability for date: {current_date}")
            slot = AvailabilitySlot.objects.filter(
                listing=listing,
                date=current_date,
                is_available=True
            ).first()
            if not slot:
                print(f"Date {current_date} is not available!")
                raise serializers.ValidationError(
                    {"non_field_errors": [f"Selected date {current_date} is not available."]}
                )
            current_date += timedelta(days=1)

        # def validate(self, data):
    #     request = self.context.get("request")
    #     # Проверка на AnonymousUser для безопасности
    #     if not request or not request.user or isinstance(request.user, AnonymousUser):
    #         raise serializers.ValidationError("Authentication is required to create a booking.")
    #
    #     is_create = request and request.method == "POST"
    #
    #     # Получаем поля из запроса или из текущего объекта
    #     listing = data.get("listing") or getattr(self.instance, "listing", None)
    #     start_date = data.get("start_date") or getattr(self.instance, "start_date", None)
    #     end_date = data.get("end_date") or getattr(self.instance, "end_date", None)
    #
    #     if not listing or not start_date or not end_date:
    #         raise serializers.ValidationError("Missing required fields for validation.")
    #
    #     # Преобразование в даты, если нужно
    #     if isinstance(start_date, str):
    #         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    #     if isinstance(end_date, str):
    #         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    #
    #     if start_date >= end_date:
    #         raise serializers.ValidationError(
    #             {"non_field_errors": ["End date must be after start date."]}
    #         )
    #
    #     # Проверка доступности дат
    #     current_date = start_date
    #     while current_date < end_date:
    #         slot = AvailabilitySlot.objects.filter(
    #             listing=listing,
    #             date=current_date,
    #             is_available=True
    #         ).first()
    #         if not slot:
    #             raise serializers.ValidationError(
    #                 {"non_field_errors": [f"Selected date {current_date} is not available."]}
    #             )
    #         current_date += timedelta(days=1)

        # Проверка пересечений
        instance = self.instance
        if instance:
            overlapping_bookings = (
                Booking.objects.filter(
                    listing=listing,
                    start_date__lt=end_date,
                    end_date__gt=start_date
                )
                .exclude(pk=instance.pk)
                .filter(Q(status="CONFIRMED") | Q(status="PENDING"))
            )
        else:
            overlapping_bookings = Booking.objects.filter(
                listing=listing,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).filter(Q(status="CONFIRMED") | Q(status="PENDING"))

        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["Selected dates overlap with an existing booking."]}
            )

        # Пересчёт total_price только при создании
        # Теперь это делает модель в методе save(), но можно и здесь для двойной проверки
        # duration = (end_date - start_date).days
        # data["total_price"] = duration * listing.price_per_night

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        # Проверка на AnonymousUser уже сделана в validate, но повторим для безопасности
        if not request or not request.user or isinstance(request.user, AnonymousUser):
            raise serializers.ValidationError("Authentication is required to create a booking.")

        # Логика для администратора
        if request.user.is_staff and "user" in validated_data:
            pass  # не перезаписываем — админ указал вручную
        else:
            validated_data["user"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Пример для update: убедитесь, что total_price тоже пересчитывается
        # Валидация уже сделала это, так что просто обновляем поля
        # Если start_date или end_date изменяются, модель Booking сама пересчитает total_price в save()
        instance.listing = validated_data.get("listing", instance.listing)
        instance.start_date = validated_data.get("start_date", instance.start_date)
        instance.end_date = validated_data.get("end_date", instance.end_date)
        instance.status = validated_data.get("status", instance.status)
        # instance.total_price = validated_data.get("total_price", instance.total_price) # Убираем, модель сама рассчитает
        instance.save()  # save() вызовет перерасчет total_price
        return instance

# # bookings/serializers.py
# from datetime import date, timedelta, datetime
# from django.db.models import Q
# from rest_framework import serializers
# from bookings.models import Booking
# from listings.models import AvailabilitySlot
#
# from users.models import User  # или кастомная модель
# from listings.models import Listing
#
# class BookingSerializer(serializers.ModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name='booking-detail')  # <-- НОВОЕ ПОЛЕ
#     user = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(),
#         required=False
#     )
#
#     class Meta:
#         model = Booking
#         fields = ['url','id', 'start_date', 'end_date', 'total_price', 'status', 'created_at', 'user', 'listing']
#         read_only_fields = ['id', 'status', 'created_at']
#
#     def validate_start_date(self, value):
#         if value < date.today():
#             raise serializers.ValidationError("Start date cannot be in the past.")
#         return value
#
#     def validate(self, data):
#         request = self.context.get("request")
#         is_create = request and request.method == "POST"
#
#         # Получаем поля из запроса или из текущего объекта
#         listing = data.get("listing") or getattr(self.instance, "listing", None)
#         start_date = data.get("start_date") or getattr(self.instance, "start_date", None)
#         end_date = data.get("end_date") or getattr(self.instance, "end_date", None)
#
#         if not listing or not start_date or not end_date:
#             raise serializers.ValidationError("Missing required fields for validation.")
#
#         # Преобразование в даты, если нужно
#         if isinstance(start_date, str):
#             start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#         if isinstance(end_date, str):
#             end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#
#         if start_date >= end_date:
#             raise serializers.ValidationError(
#                 {"non_field_errors": ["End date must be after start date."]}
#             )
#
#         # Проверка доступности дат
#         current_date = start_date
#         while current_date < end_date:
#             slot = AvailabilitySlot.objects.filter(
#                 listing=listing,
#                 date=current_date,
#                 is_available=True
#             ).first()
#             if not slot:
#                 raise serializers.ValidationError(
#                     {"non_field_errors": [f"Selected date {current_date} is not available."]}
#                 )
#             current_date += timedelta(days=1)
#
#         # Проверка пересечений
#         instance = self.instance
#         if instance:
#             overlapping_bookings = (
#                 Booking.objects.filter(
#                     listing=listing,
#                     start_date__lt=end_date,
#                     end_date__gt=start_date
#                 )
#                 .exclude(pk=instance.pk)
#                 .filter(Q(status="CONFIRMED") | Q(status="PENDING"))
#             )
#         else:
#             overlapping_bookings = Booking.objects.filter(
#                 listing=listing,
#                 start_date__lt=end_date,
#                 end_date__gt=start_date
#             ).filter(Q(status="CONFIRMED") | Q(status="PENDING"))
#
#         if overlapping_bookings.exists():
#             raise serializers.ValidationError(
#                 "Selected dates overlap with an existing booking."
#             )
#
#         # Пересчёт total_price только при создании
#         if is_create:
#             duration = (end_date - start_date).days
#             data["total_price"] = duration * listing.price_per_night
#
#         return data
#
#     def create(self, validated_data):
#         request = self.context.get("request")
#         if request.user.is_staff and "user" in validated_data:
#             pass  # не перезаписываем — админ указал вручную
#         else:
#             validated_data["user"] = request.user
#         return super().create(validated_data)
#
#     def update(self, instance, validated_data):
#         # Пример для update: убедитесь, что total_price тоже пересчитывается
#         # Если start_date или end_date изменяются, total_price должен обновиться
#         # Валидация уже сделала это, так что просто обновляем поля
#         instance.listing = validated_data.get("listing", instance.listing)
#         instance.start_date = validated_data.get("start_date", instance.start_date)
#         instance.end_date = validated_data.get("end_date", instance.end_date)
#         instance.status = validated_data.get("status", instance.status)
#         instance.total_price = validated_data.get(
#             "total_price", instance.total_price
#         )  # total_price будет в validated_data
#         instance.save()
#         return instance
