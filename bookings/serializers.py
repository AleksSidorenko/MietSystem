# bookings/serializers.py
from datetime import date, timedelta
from django.db.models import Q
from rest_framework import serializers
from bookings.models import Booking
# from listings.models import Listing
# from listings.serializers import ListingShortSerializer
# from users.serializers import UserShortSerializer


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['tenant', 'status']

# class BookingSerializer(serializers.ModelSerializer):
#     # listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
#
#     listing = serializers.PrimaryKeyRelatedField(
#         queryset=Listing.objects.all(), write_only=True
#     )
#     listing_data = ListingShortSerializer(source="listing", read_only=True)
#     user = UserShortSerializer(read_only=True)
#
#     class Meta:
#         model = Booking
#         fields = [
#             "id",
#             "listing",  # write_only
#             "listing_data",  # read_only
#             "user",
#             "start_date",
#             "end_date",
#             "status",
#             "total_price",
#         ]
#         read_only_fields = ["id", "user", "status", "total_price"]

    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate(self, data):
        """
        Общая валидация для бронирования.
        """
        listing = data.get("listing")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not all([listing, start_date, end_date]):
            raise serializers.ValidationError(
                "Listing, start date, and end date are required."
            )

        # Проверка активности объявления
        if not listing.is_active:
            raise serializers.ValidationError(
                "This listing is not active and cannot be booked."
            )

        # Проверка дат: дата выезда должна быть после даты заезда
        if start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date.")

        # Проверка дат: дата начала бронирования не должна быть в прошлом
        if start_date < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")

        # Проверка продолжительности бронирования
        duration = (end_date - start_date).days
        if duration < 1:  # Это уже покрывается start_date >= end_date, но можно явно
            raise serializers.ValidationError(
                "Booking duration must be at least 1 day."
            )
        if duration > 30:
            raise serializers.ValidationError("Booking duration cannot exceed 30 days.")

        # Проверка доступности дат в объявлении
        # Предполагаем, что availability - это словарь {дата: True/False}
        current_date = start_date
        while current_date < end_date:
            date_str = current_date.isoformat()
            if not listing.availability.get(
                date_str, False
            ):  # False по умолчанию, если даты нет
                raise serializers.ValidationError(
                    f"Selected date {date_str} is not available for booking."
                )
            current_date += timedelta(days=1)

        # Проверка пересечения дат с существующими бронированиями
        # Исключаем текущий инстанс при обновлении
        instance = self.instance
        if instance:
            # Для обновления, исключаем текущее бронирование из проверок на пересечение
            overlapping_bookings = (
                Booking.objects.filter(
                    listing=listing, start_date__lt=end_date, end_date__gt=start_date
                )
                .exclude(pk=instance.pk)
                .filter(Q(status="CONFIRMED") | Q(status="PENDING"))
            )
        else:
            overlapping_bookings = Booking.objects.filter(
                listing=listing, start_date__lt=end_date, end_date__gt=start_date
            ).filter(Q(status="CONFIRMED") | Q(status="PENDING"))

        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                "Selected dates overlap with an existing booking."
            )

        # Расчет total_price
        data["total_price"] = duration * listing.price_per_night

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["tenant"] = request.user
        # validated_data["user"] = request.user
        return super().create(
            validated_data
        )  # или Booking.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Пример для update: убедитесь, что total_price тоже пересчитывается
        # Если start_date или end_date изменяются, total_price должен обновиться
        # Валидация уже сделала это, так что просто обновляем поля
        instance.listing = validated_data.get("listing", instance.listing)
        instance.start_date = validated_data.get("start_date", instance.start_date)
        instance.end_date = validated_data.get("end_date", instance.end_date)
        instance.status = validated_data.get("status", instance.status)
        instance.total_price = validated_data.get(
            "total_price", instance.total_price
        )  # total_price будет в validated_data
        instance.save()
        return instance
