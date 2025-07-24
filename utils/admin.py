# Project_MietSystem/utils/admin.py
# Централизованная админка

import csv

from allauth.account.models import EmailAddress
from axes.models import AccessAttempt, AccessFailureLog, AccessLog
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)
from django_otp.plugins.otp_totp.models import TOTPDevice
from leaflet.admin import LeafletGeoAdmin
from leaflet.forms.widgets import LeafletWidget
from modeltranslation.admin import TranslationAdmin
from simple_history.admin import SimpleHistoryAdmin

from analytics.models import SearchHistory, ViewHistory
from bookings.models import Booking
from listings.forms import ListingForm
from listings.models import Amenity, AvailabilitySlot, Listing
from locations.models import Location
from reviews.models import Review
from users.models import User
from utils.role_utils import user_has_role


class DefaultLocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = "__all__"
        widgets = {
            "coordinates": LeafletWidget(),
        }


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    pass


class AvailabilitySlotInline(admin.TabularInline):
    model = AvailabilitySlot
    extra = 3
    min_num = 0
    verbose_name = "Availability Slot"
    verbose_name_plural = "Availability Slots"
    classes = ["collapse"]

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or user_has_role(request.user, ["ADMIN"]):
            return True
        if (
            user_has_role(request.user, ["LANDLORD"])
            and obj
            and obj.user == request.user
        ):
            return True
        return False

    def has_add_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ["listing", "date", "is_available"]
    list_filter = ["is_available", "date"]
    search_fields = ["listing__title"]
    date_hierarchy = "date"
    allowed_roles = ["ADMIN", "LANDLORD"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_has_role(request.user, ["ADMIN"]):
            return qs
        if user_has_role(request.user, ["LANDLORD"]):
            return qs.filter(listing__user=request.user)
        return qs.none()

    def has_module_permission(self, request):
        return user_has_role(request.user, self.allowed_roles)

    def has_change_permission(self, request, obj=None):
        if user_has_role(request.user, ["ADMIN"]):
            return True
        if (
            user_has_role(request.user, ["LANDLORD"])
            and obj
            and obj.listing.user == request.user
        ):
            return True
        return False

    def has_add_permission(self, request):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


class LocationInline(admin.StackedInline):
    model = Location
    extra = 1
    readonly_fields = ("get_latitude", "get_longitude")

    def get_latitude(self, obj):
        # Получаем широту из поля coordinates
        if obj.coordinates:
            return obj.coordinates.y
        return None

    def get_longitude(self, obj):
        # Получаем долготу из поля coordinates
        if obj.coordinates:
            return obj.coordinates.x
        return None

    get_latitude.short_description = "Latitude"
    get_longitude.short_description = "Longitude"


def user_has_role(user, roles):
    """
    Проверяет, имеет ли пользователь одну из указанных ролей.
    Суперпользователь считается ADMIN.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True  # суперпользователь = ADMIN
    return getattr(user, "role", None) in roles


class RoleAccessMixin:
    """
    Универсальный миксин для управления правами доступа в админке на основе ролей.
    По умолчанию доступ разрешён суперпользователям и ролям из `allowed_roles`.
    """

    def get_allowed_roles(self):
        return getattr(self, "allowed_roles", ["ADMIN"])

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_add_permission(self, request):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return user_has_role(request.user, self.get_allowed_roles())
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.is_superuser

    def has_module_permission(self, request):
        return self.has_view_permission(request)


class ExportCsvMixin:
    export_fields = []

    # (1) Опционально скрываем action 'export_to_csv' для TENANT
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not user_has_role(request.user, ["ADMIN", "LANDLORD"]):
            if "export_to_csv" in actions:
                del actions[
                    "export_to_csv"
                ]  ##️ Удаляем export, если роль — не ADMIN и не LANDLORD
        return actions

    # (2) Проверка разрешённых ролей внутри самого действия
    def export_to_csv(self, request, queryset):
        if not user_has_role(request.user, ["ADMIN", "LANDLORD"]):
            self.message_user(
                request,
                "You do not have permission to export data.",
                level=messages.ERROR,
            )
            return None  # Не даём экспортировать

        if not self.export_fields:
            self.message_user(
                request, "Export fields not defined", level=messages.ERROR
            )
            return HttpResponse(status=400)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=export.csv"

        writer = csv.writer(response)
        writer.writerow(self.export_fields)

        for obj in queryset:
            row = []
            for field in self.export_fields:
                # Поддержка полей с '__' (related fields)
                try:
                    value = self._get_nested_attr(obj, field)
                except AttributeError:
                    value = ""
                row.append(str(value))
            writer.writerow(row)

        return response

    export_to_csv.short_description = "Export selected to CSV"

    # (3) Вспомогательная функция для __ цепочек, если ещё не была реализована
    def _get_nested_attr(self, obj, attr):
        """Поддержка доступа к вложенным аттрибутам через '__'"""
        for part in attr.split("__"):
            obj = getattr(obj, part, "")
            if obj is None:
                return ""
        return obj


class BaseTranslatableAdmin(
    TranslationAdmin, ExportCsvMixin, RoleAccessMixin, admin.ModelAdmin
):
    allowed_roles = ["ADMIN"]
    actions = ["export_to_csv"]


class BaseAdmin(RoleAccessMixin, admin.ModelAdmin):
    allowed_roles = ["ADMIN"]


class BaseHistoryAdmin(RoleAccessMixin, SimpleHistoryAdmin):
    allowed_roles = ["ADMIN"]

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class AdminDisplayModeMixin:
    """
    Миксин для переключения между детализированным и простым режимом отображения
    list_display, list_filter, search_fields в админке.
    """

    def _get_admin_attr(self, attr_name):
        detailed = getattr(self, f"detailed_{attr_name}", None)
        simple = getattr(self, f"simple_{attr_name}", None)
        if getattr(settings, "ADMIN_DETAILED_MODE", False) and detailed is not None:
            return detailed
        if simple is not None:
            return simple
        return detailed or []

    @property
    def list_display(self):
        return self._get_admin_attr("list_display")

    @property
    def list_filter(self):
        return self._get_admin_attr("list_filter")

    @property
    def search_fields(self):
        return self._get_admin_attr("search_fields")


# Отмена регистрации ненужных моделей
admin.site.unregister(AccessLog)
admin.site.unregister(AccessFailureLog)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(TOTPDevice)
admin.site.unregister(EmailAddress)
admin.site.unregister(AccessAttempt)
admin.site.unregister(PeriodicTask)


@admin.register(TOTPDevice)
class TOTPDeviceAdmin(BaseAdmin):
    list_display = ("user", "name", "confirmed")
    list_filter = ("confirmed",)
    search_fields = ("user__email", "name")


@admin.register(EmailAddress)
class EmailAddressAdmin(BaseAdmin):
    list_display = ("user", "email", "verified", "primary")
    list_filter = ("verified", "primary")
    search_fields = ("email", "user__email")


@admin.register(AccessAttempt)
class AccessAttemptAdmin(BaseAdmin, ExportCsvMixin):
    list_display = ["ip_address", "username", "attempt_time", "failures_since_start"]
    list_filter = ["attempt_time"]
    search_fields = ("username", "ip_address")
    readonly_fields = ["attempt_time"]
    export_fields = ["ip_address", "username", "attempt_time", "failures_since_start"]
    actions = ["export_to_csv", "reset_attempts"]

    def reset_attempts(self, request, queryset):
        queryset.delete()
        self.message_user(request, "Selected access attempts have been reset.")

    reset_attempts.short_description = "Reset selected access attempts"

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, ["ADMIN"])

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(BaseAdmin):
    list_display = ("name", "task", "enabled", "last_run_at")
    list_filter = ("enabled",)
    search_fields = ("name", "task")
    readonly_fields = ("last_run_at",)


@admin.register(User)
class UserAdmin(AdminDisplayModeMixin, BaseHistoryAdmin):
    allowed_roles = ["ADMIN", "TENANT", "LANDLORD"]
    actions = ["make_verified"]

    detailed_list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_verified",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    simple_list_display = ("email", "first_name", "last_name", "role")
    history_list_display = ["email", "role", "is_active", "is_verified"]
    detailed_list_filter = ("role", "is_active", "is_verified", "is_staff")
    simple_list_filter = ("role",)
    detailed_search_fields = ("email", "first_name", "last_name")
    simple_search_fields = ("email",)
    readonly_fields = ("date_joined", "last_login")

    # Изменение 2: Права редактирования Tenant и Landlord — разрешаем менять только имя,
    # фамилию, email, телефон (если есть)
    def get_readonly_fields(self, request, obj=None):
        user = request.user

        if obj and (user_has_role(user, ["TENANT", "LANDLORD"])) and obj.pk == user.pk:
            allowed = [
                "first_name",
                "last_name",
                "email",
                "phone",
            ]  # <- добавь phone, если есть
            readonly = [
                f.name for f in self.model._meta.fields if f.name not in allowed
            ]
            return readonly

        return super().get_readonly_fields(request, obj)

    # Изменение 1: get_queryset — Tenant и Landlord видят себя и других, связанных бронированиями
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return qs

        if user_has_role(user, ["LANDLORD"]):
            # Landlord видит себя и Tenant, у которых есть брони его объявлений
            tenant_ids = (
                Booking.objects.filter(listing__user=user)
                .values_list("user_id", flat=True)
                .distinct()
            )
            return qs.filter(Q(pk=user.pk) | Q(pk__in=tenant_ids))

        if user_has_role(user, ["TENANT"]):
            # Tenant видит себя и Landlord, у которых у него брони
            landlord_ids = (
                Booking.objects.filter(user=user)
                .values_list("listing__user_id", flat=True)
                .distinct()
            )
            return qs.filter(Q(pk=user.pk) | Q(pk__in=landlord_ids))

        return qs.none()

    # --------------------------

    def has_delete_permission(self, request, obj=None):
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return True
        if obj and user_has_role(user, ["LANDLORD"]):
            return False
        if obj and user_has_role(user, ["TENANT"]):
            return obj.pk == user.pk  # Только сам себя
        return False

    @admin.action(description="Mark selected users as verified")
    def make_verified(self, request, queryset):
        queryset.update(is_verified=True)

    make_verified.short_description = "Mark selected users as verified"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            if user_has_role(request.user, ["ADMIN"]):
                kwargs["queryset"] = Group.objects.all()
                if not request.user.groups.filter(name="Admin").exists():
                    admin_group = Group.objects.filter(name="Admin").first()
                    if admin_group:
                        request.user.groups.add(admin_group)
            elif user_has_role(request.user, ["TENANT"]):
                kwargs["queryset"] = Group.objects.filter(name="Tenant")
            elif user_has_role(request.user, ["LANDLORD"]):
                kwargs["queryset"] = Group.objects.filter(name="Landlord")
            else:
                kwargs["queryset"] = Group.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_change_permission(self, request, obj=None):
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return True
        if obj and user_has_role(user, ["TENANT", "LANDLORD"]):
            return obj.pk == user.pk
        if obj is None:
            return user_has_role(request.user, self.get_allowed_roles())
        return False

    def has_module_permission(self, request):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_add_permission(self, request):
        # Добавлять пользователей может только Admin
        return user_has_role(request.user, ["ADMIN"])


@admin.register(Listing)
class ListingAdmin(AdminDisplayModeMixin, BaseTranslatableAdmin):
    allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
    form = ListingForm
    filter_horizontal = ("amenities",)  # Использует виджет FilteredSelectMultiple

    inlines = [AvailabilitySlotInline]  # , LocationInline]
    export_fields = [
        "title_en",
        "title_de",
        "title_ru",
        "user__email",
        "price_per_night",
        "city",
        "popularity",
    ]
    actions = ["export_to_csv", "toggle_active", "export_top_listings"]

    class AmenityFilter(SimpleListFilter):
        title = "Amenities (Удобства)"
        parameter_name = "amenity"

        def lookups(self, request, model_admin):
            return [(a.id, a.name) for a in Amenity.objects.all()]

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(amenities__id=self.value())
            return queryset

    detailed_list_display = (
        "title_en",
        "user",
        "city",
        "country",
        "price_per_night",
        "availability_range",
        "amenities_list",  # ← добавили
        "is_active",
        "popularity",
        "created_at",
    )
    simple_list_display = ("title_en", "user", "price_per_night", "photo_preview")
    readonly_fields = ("photo_preview",)

    history_list_display = [
        "title_en",
        "title_de",
        "title_ru",
        "price_per_night",
        "is_active",
        "popularity",
        "amenities",
    ]
    detailed_list_filter = (
        "is_active",
        "property_type",
        "city",
        "country",
        "created_at",
        AmenityFilter,
    )
    simple_list_filter = ("is_active",)
    detailed_search_fields = (
        "title_en",
        "description_en",
        "user__email",
        "city",
        "country",
        "address",
    )
    simple_search_fields = ("title_en", "user__email")

    def availability_range(self, obj):
        slots = obj.availability_slots.filter(is_available=True).order_by("date")
        if not slots.exists():
            return "Нет доступных дат"

        first = date_format(slots.first().date, "DATE_FORMAT")
        last = date_format(slots.last().date, "DATE_FORMAT")
        return f"{first} — {last}"

    availability_range.short_description = "Availability Slots"

    def amenities_list(self, obj):
        return ", ".join([a.name for a in obj.amenities.all()])

    amenities_list.short_description = "Amenities"

    def photo_preview(self, obj):
        if not obj.photos:
            return "-"
        tags = []
        for url in obj.photos:
            tags.append(f'<img src="/{url}" style="max-height:80px; margin:2px;" />')
        return mark_safe("".join(tags))

    photo_preview.short_description = "Photos"

    def toggle_active(self, request, queryset):
        updated_count = 0
        for obj in queryset:
            if self.has_change_permission(request, obj):  # 👈 проверка прав
                obj.is_active = not obj.is_active
                obj.save()
                updated_count += 1
        if updated_count > 0:
            self.message_user(
                request,
                f"Toggled active status for {updated_count} listings.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No listings were updated. You may not have permission.",
                level=messages.WARNING,
            )

    toggle_active.short_description = "Toggle active status for selected listings"

    def export_top_listings(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="top_listings.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Title (EN)",
                "Title (DE)",
                "Title (RU)",
                "User Email",
                "Price Per Night",
                "City",
                "Popularity",
            ]
        )
        for obj in queryset.order_by("-popularity")[:5]:
            writer.writerow(
                [
                    obj.title_en,
                    obj.title_de,
                    obj.title_ru,
                    obj.user.email,
                    obj.price_per_night,
                    obj.address,
                    obj.popularity,
                ]
            )
        return response

    export_top_listings.short_description = "Export top 5 listings to CSV"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return qs

        if user_has_role(user, ["LANDLORD"]):
            return qs.filter(user=user)  # ✅ Только свои объявления

        if user_has_role(user, ["TENANT"]):
            return qs.filter(is_active=True)  # ✅ Только активные

        return qs.none()

    def has_add_permission(self, request):
        return user_has_role(request.user, ["LANDLORD", "ADMIN"])

    def has_view_permission(self, request, obj=None):
        # Все роли могут просматривать
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return True

        if user_has_role(user, ["LANDLORD"]):
            return obj is None or (obj and obj.user == user)

        # Tenant может только просматривать
        return False

    def has_module_permission(self, request):
        return user_has_role(request.user, self.get_allowed_roles())


@admin.register(Booking)
class BookingAdmin(
    AdminDisplayModeMixin,
    ExportCsvMixin,  # ✅ отдельно
    BaseAdmin,  # ✅ включает RoleAccessMixin
):
    allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
    export_fields = [
        "listing__title_en",
        "user__email",
        "status",
        "start_date",
        "end_date",
        "total_price",
    ]
    actions = ["confirm_booking", "export_to_csv"]

    detailed_list_display = (
        "listing",
        "user",
        "start_date",
        "end_date",
        "status",
        "total_price",
        "created_at",
    )
    simple_list_display = ("listing", "user", "status", "start_date", "end_date")

    detailed_list_filter = ("status", "start_date", "end_date")
    simple_list_filter = ("status", "start_date")

    detailed_search_fields = (
        "listing__title_en",
        "listing__title_de",
        "listing__title_ru",
        "user__email",
    )
    simple_search_fields = ("listing__title_en", "user__email")

    def confirm_booking(self, request, queryset):
        queryset.update(status="CONFIRMED")

    confirm_booking.short_description = "Confirm selected bookings"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return qs

        if user_has_role(user, ["LANDLORD"]):
            return qs.filter(listing__user=user)

        if user_has_role(user, ["TENANT"]):
            return qs.filter(user=user)

        return qs.none()

    def has_delete_permission(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return True

        if obj and user_has_role(user, ["TENANT"]):
            return obj.user == user  # Только своё

        if obj and user_has_role(user, ["LANDLORD"]):
            return obj.listing.user == user  # Только по своим объявлениям

        return False

    def has_add_permission(self, request):
        return user_has_role(request.user, ["TENANT", "ADMIN"])

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_change_permission(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return True

        if obj and user_has_role(user, ["LANDLORD"]):
            return obj.listing.user == user

        if obj and user_has_role(user, ["TENANT"]):
            return obj.user == user

        # Разрешаем доступ к changelist для всех ролей
        if obj is None:
            return user_has_role(request.user, self.get_allowed_roles())

        return False

    def has_module_permission(self, request):
        return user_has_role(request.user, self.get_allowed_roles())


@admin.register(Review)
class ReviewAdmin(AdminDisplayModeMixin, ExportCsvMixin, BaseAdmin):
    allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
    export_fields = [
        "user__email",
        "booking__listing__title_en",
        "rating",
        "comment",
        "is_approved",
    ]
    actions = ["approve_review", "export_to_csv", "respond_to_reviews"]

    detailed_list_display = (
        "action_links",
        "booking",
        "user",
        "user_email",
        "rating",
        "is_approved",
        "created_at",
    )
    simple_list_display = ("action_links", "booking", "user_email", "rating", "comment")

    detailed_list_filter = ("is_approved", "rating", "created_at")
    simple_list_filter = ("is_approved",)

    detailed_search_fields = (
        "comment",
        "user__email",
        "booking__listing__title_en",
        "booking__listing__title_de",
        "booking__listing__title_ru",
    )
    simple_search_fields = ("user__email",)

    fieldsets = (
        (None, {"fields": ("booking", "user", "rating", "comment")}),
        (
            "Ответ арендодателя",
            {
                "fields": ("landlord_response",),
                "description": "Здесь вы можете ответить на отзыв арендатора.",
            },
        ),
    )

    def action_links(self, obj):
        user = getattr(self, "request_user", None)
        if not user:
            return ""
        url = reverse("admin:reviews_review_change", args=[obj.pk])
        if user_has_role(user, ["LANDLORD"]):
            return format_html(
                '<a class="button" href="{}">Ответить на отзыв</a> &nbsp; '
                '<a class="button" href="{}">Просмотр</a>',
                url,
                url,
            )
        return format_html('<a class="button" href="{}">Изменить</a>', url)

    action_links.short_description = "Действия"

    class HasLandlordResponseFilter(SimpleListFilter):
        title = "Наличие ответа арендодателя"
        parameter_name = "has_landlord_response"

        def lookups(self, request, model_admin):
            return (
                ("yes", "Есть ответ"),
                ("no", "Нет ответа"),
            )

        def queryset(self, request, queryset):

            if self.value() == "yes":
                return queryset.exclude(landlord_response__exact="").exclude(
                    landlord_response__isnull=True
                )
            if self.value() == "no":
                return queryset.filter(landlord_response__exact="") | queryset.filter(
                    landlord_response__isnull=True
                )
            return queryset

    list_filter = ("is_approved", "rating", "created_at", HasLandlordResponseFilter)

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"

    def approve_review(self, request, queryset):
        queryset.update(is_approved=True)

    approve_review.short_description = "Approve selected reviews"

    def get_queryset(self, request):
        self.request_user = request.user  # используется в action_links

        qs = super().get_queryset(request)
        user = request.user
        print(f"[ReviewAdmin] get_queryset for {user.email} ({user.role})")

        if user_has_role(user, ["ADMIN"]):
            print("[ReviewAdmin] ADMIN: return all")
            return qs
        if user_has_role(user, ["LANDLORD"]):
            filtered_qs = qs.filter(booking__listing__user=user)
            print(f"[ReviewAdmin] LANDLORD: filtered_qs.count = {filtered_qs.count()}")
            return filtered_qs
        if user_has_role(user, ["TENANT"]):
            filtered_qs = qs.filter(user=user)
            print(f"[ReviewAdmin] TENANT: filtered_qs.count = {filtered_qs.count()}")
            return filtered_qs

        print("[ReviewAdmin] No access - returning empty queryset")
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["LANDLORD"]) and obj:
            # Только разрешить редактировать landlord_response
            return [
                f.name for f in self.model._meta.fields if f.name != "landlord_response"
            ]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request):
        return user_has_role(request.user, ["TENANT", "ADMIN"])

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_change_permission(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return True
        if obj and user_has_role(user, ["LANDLORD"]):
            return obj.booking.listing.user == user
        if obj and user_has_role(user, ["TENANT"]):
            return obj.user == user
        if obj is None:
            return True
        return False

    def has_module_permission(self, request):
        return user_has_role(request.user, self.get_allowed_roles())

    def has_delete_permission(self, request, obj=None):
        user = request.user

        if user_has_role(user, ["ADMIN"]):
            return True

        if obj and user_has_role(user, ["TENANT"]):
            return obj.user == user  # Только свои отзывы

        return False  # Landlord не может удалять

    @admin.action(description="Ответить на отзыв")
    def respond_to_reviews(self, request, queryset):
        user = request.user

        if not user_has_role(user, ["LANDLORD"]):
            self.message_user(
                request,
                "Только Landlord может отвечать на отзывы.",
                level=messages.ERROR,
            )
            return

        if queryset.count() != 1:
            self.message_user(
                request, "Выберите ровно один отзыв для ответа.", level=messages.WARNING
            )
            return

        obj = queryset.first()

        # Проверка: Landlord может ответить только на отзывы к своим объявлениям
        if obj.booking.listing.user != user:
            self.message_user(
                request,
                "Вы можете отвечать только на отзывы по своим объявлениям.",
                level=messages.ERROR,
            )
            return

        # Перенаправляем на стандартную admin change form
        url = reverse("admin:reviews_review_change", args=[obj.pk])
        return redirect(url)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if user_has_role(request.user, ["LANDLORD"]):
            extra_context["title"] = "Ответить на отзыв"
        return super().changeform_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        if not qs.exists() and user_has_role(request.user, ["LANDLORD"]):
            messages.info(request, "У вас пока нет отзывов.")
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(SearchHistory)
class SearchHistoryAdmin(ExportCsvMixin, BaseAdmin):
    allowed_roles = ["ADMIN", "LANDLORD"]
    export_fields = ["user__email", "query", "timestamp"]
    actions = ["export_to_csv"]

    list_display = ("user", "query", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("query", "user__email")
    readonly_fields = ("timestamp",)
    history_list_display = ["query", "timestamp"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return qs
        if user_has_role(user, ["LANDLORD"]):
            return qs.filter(user=user)
        return qs.none()

    def has_module_permission(self, request):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_change_permission(self, request, obj=None):
        # По умолчанию запрещаем редактирование для лендлорда
        return user_has_role(request.user, ["ADMIN"])

    def has_add_permission(self, request):
        return user_has_role(request.user, ["ADMIN"])


@admin.register(ViewHistory)
class ViewHistoryAdmin(ExportCsvMixin, BaseAdmin):
    allowed_roles = ["ADMIN", "LANDLORD"]
    export_fields = ["user__email", "listing__title_en", "timestamp"]
    actions = ["export_to_csv"]

    list_display = ("user", "listing", "timestamp")
    list_filter = ("timestamp",)
    search_fields = (
        "user__email",
        "listing__title_en",
        "listing__title_de",
        "listing__title_ru",
    )
    readonly_fields = ("timestamp",)
    history_list_display = ["listing", "timestamp"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return qs
        if user_has_role(user, ["LANDLORD"]):
            return qs.filter(listing__user=user)
        return qs.none()

    def has_module_permission(self, request):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_change_permission(self, request, obj=None):
        # По умолчанию запрещаем редактирование для лендлорда
        return user_has_role(request.user, ["ADMIN"])

    def has_add_permission(self, request):
        return user_has_role(request.user, ["ADMIN"])


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = "__all__"


@admin.register(Location)
class LocationAdmin(AdminDisplayModeMixin, LeafletGeoAdmin, BaseHistoryAdmin):

    allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
    form = LocationForm

    list_display = (
        "listing",
        "street",
        "city",
        "federal_state",
        "country_display",
        "get_latitude",
        "get_longitude",
        "photo_preview",
    )
    list_filter = ("city", "federal_state")
    search_fields = ("street", "city", "federal_state", "listing__country__iexact")

    def get_readonly_fields(self, request, obj=None):
        base = ["photo_preview", "country_display"]
        if getattr(request.user, "role", None) == "TENANT":
            base.append("readonly_coordinates_map")
        return base

    def get_fieldsets(self, request, obj=None):
        if getattr(request.user, "role", None) == "TENANT":
            return (
                (
                    None,
                    {
                        "fields": (
                            "listing",
                            "street",
                            "postal_code",
                            "city",
                            "federal_state",
                            "country_display",
                            "readonly_coordinates_map",
                        )
                    },
                ),
                (
                    "Дополнительно",
                    {"fields": ("photo_preview",), "classes": ("collapse",)},
                ),
            )
        return (
            (
                None,
                {
                    "fields": (
                        "listing",
                        "street",
                        "postal_code",
                        "city",
                        "federal_state",
                        "country_display",
                        "coordinates",
                    )
                },
            ),
            ("Дополнительно", {"fields": ("photo_preview",), "classes": ("collapse",)}),
        )

    # ==== HELPERS ====
    def get_latitude(self, obj):
        return obj.coordinates.y if obj.coordinates else None

    get_latitude.short_description = "Latitude"

    def get_longitude(self, obj):
        return obj.coordinates.x if obj.coordinates else None

    get_longitude.short_description = "Longitude"

    def readonly_coordinates_map(self, obj):
        if not obj or not obj.coordinates:
            return "-"
        lat, lon = obj.coordinates.y, obj.coordinates.x
        return mark_safe(
            f"""
            <iframe width="100%" height="250" style="border:1px solid #ccc"
                    src="https://www.openstreetmap.org/export/embed.html?bbox=  {lon-0.01}%2C{lat-0.01}%2C{lon+0.01}%2C{lat+0.01}&layer=mapnik&marker={lat}%2C{lon}">
            </iframe>
            <br><a href="https://www.openstreetmap.org/?mlat=  {lat}&mlon={lon}#map=15/{lat}/{lon}" target="_blank">View on OpenStreetMap</a>
        """
        )

    readonly_coordinates_map.short_description = "Карта (только просмотр)"

    def photo_preview(self, obj):
        if obj.listing and obj.listing.photos:
            tags = []
            for url in (
                obj.listing.photos
                if isinstance(obj.listing.photos, (list, tuple))
                else [obj.listing.photos]
            ):
                if url:
                    tags.append(
                        f'<img src="/{url}" style="max-height:100px; max-width:100px; object-fit:contain; margin:2px;" />'
                    )
            return mark_safe("".join(tags))
        return "-"

    photo_preview.short_description = "Photos"

    def country_display(self, obj):
        return obj.listing.country if obj.listing else "-"

    country_display.short_description = "Country"

    # ==== PERMISSIONS ====
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return qs
        if user_has_role(user, ["LANDLORD"]):
            return qs.filter(listing__user=user).distinct()
        if user_has_role(user, ["TENANT"]):
            return qs.filter(listing__is_active=True)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        return user_has_role(request.user, ["ADMIN", "LANDLORD", "TENANT"])

    def has_module_permission(self, request):
        return user_has_role(request.user, ["ADMIN", "LANDLORD", "TENANT"])

    def has_add_permission(self, request):
        return user_has_role(request.user, ["ADMIN", "LANDLORD"])

    def has_change_permission(self, request, obj=None):
        user = request.user
        return user_has_role(user, ["ADMIN", "LANDLORD"])

    def has_delete_permission(self, request, obj=None):
        user = request.user
        if user_has_role(user, ["ADMIN"]):
            return True
        return obj and user_has_role(user, ["LANDLORD"]) and obj.listing.user == user



# # Project_MietSystem/utils/admin.py
# # Централизованная админка
#
# import csv
#
# from allauth.account.models import EmailAddress
# from axes.models import AccessAttempt, AccessFailureLog, AccessLog
# from django import forms
# from django.conf import settings
# from django.contrib import admin, messages
# from django.contrib.admin import SimpleListFilter
# from django.contrib.auth.models import Group
# from django.db.models import Q
# from django.http import HttpResponse
# from django.shortcuts import redirect
# from django.urls import reverse
# from django.utils.formats import date_format
# from django.utils.html import format_html
# from django.utils.safestring import mark_safe
# from django_celery_beat.models import (
#     ClockedSchedule,
#     CrontabSchedule,
#     IntervalSchedule,
#     PeriodicTask,
#     SolarSchedule,
# )
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from leaflet.admin import LeafletGeoAdmin
# from leaflet.forms.widgets import LeafletWidget
# from modeltranslation.admin import TranslationAdmin
# from simple_history.admin import SimpleHistoryAdmin
#
# from analytics.models import SearchHistory, ViewHistory
# from bookings.models import Booking
# from listings.forms import ListingForm
# from listings.models import Amenity, AvailabilitySlot, Listing
# from locations.models import Location
# from reviews.models import Review
# from users.models import User
# from utils.role_utils import user_has_role
#
#
# class DefaultLocationForm(forms.ModelForm):
#     class Meta:
#         model = Location
#         fields = "__all__"
#         widgets = {
#             "coordinates": LeafletWidget(),
#         }
#
#
# @admin.register(Amenity)
# class AmenityAdmin(admin.ModelAdmin):
#     pass
#
#
# class AvailabilitySlotInline(admin.TabularInline):
#     model = AvailabilitySlot
#     extra = 3
#     min_num = 0
#     verbose_name = "Availability Slot"
#     verbose_name_plural = "Availability Slots"
#     classes = ["collapse"]
#
#     def has_change_permission(self, request, obj=None):
#         if request.user.is_superuser or user_has_role(request.user, ["ADMIN"]):
#             return True
#         if (
#             user_has_role(request.user, ["LANDLORD"])
#             and obj
#             and obj.user == request.user
#         ):
#             return True
#         return False
#
#     def has_add_permission(self, request, obj=None):
#         return self.has_change_permission(request, obj)
#
#     def has_delete_permission(self, request, obj=None):
#         return self.has_change_permission(request, obj)
#
#
# @admin.register(AvailabilitySlot)
# class AvailabilitySlotAdmin(admin.ModelAdmin):
#     list_display = ["listing", "date", "is_available"]
#     list_filter = ["is_available", "date"]
#     search_fields = ["listing__title"]
#     date_hierarchy = "date"
#     allowed_roles = ["ADMIN", "LANDLORD"]
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if user_has_role(request.user, ["ADMIN"]):
#             return qs
#         if user_has_role(request.user, ["LANDLORD"]):
#             return qs.filter(listing__user=request.user)
#         return qs.none()
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, self.allowed_roles)
#
#     def has_change_permission(self, request, obj=None):
#         if user_has_role(request.user, ["ADMIN"]):
#             return True
#         if (
#             user_has_role(request.user, ["LANDLORD"])
#             and obj
#             and obj.listing.user == request.user
#         ):
#             return True
#         return False
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_delete_permission(self, request, obj=None):
#         return self.has_change_permission(request, obj)
#
#
# class LocationInline(admin.StackedInline):
#     model = Location
#     extra = 1
#     readonly_fields = ("get_latitude", "get_longitude")
#
#     def get_latitude(self, obj):
#         # Получаем широту из поля coordinates
#         if obj.coordinates:
#             return obj.coordinates.y
#         return None
#
#     def get_longitude(self, obj):
#         # Получаем долготу из поля coordinates
#         if obj.coordinates:
#             return obj.coordinates.x
#         return None
#
#     get_latitude.short_description = "Latitude"
#     get_longitude.short_description = "Longitude"
#
#
# def user_has_role(user, roles):
#     """
#     Проверяет, имеет ли пользователь одну из указанных ролей.
#     Суперпользователь считается ADMIN.
#     """
#     if not user.is_authenticated:
#         return False
#     if user.is_superuser:
#         return True  # суперпользователь = ADMIN
#     return getattr(user, "role", None) in roles
#
#
# class RoleAccessMixin:
#     """
#     Универсальный миксин для управления правами доступа в админке на основе ролей.
#     По умолчанию доступ разрешён суперпользователям и ролям из `allowed_roles`.
#     """
#
#     def get_allowed_roles(self):
#         return getattr(self, "allowed_roles", ["ADMIN"])
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_change_permission(self, request, obj=None):
#         if obj is None:
#             return user_has_role(request.user, self.get_allowed_roles())
#         return self.has_view_permission(request, obj)
#
#     def has_delete_permission(self, request, obj=None):
#         return request.user.is_authenticated and request.user.is_superuser
#
#     def has_module_permission(self, request):
#         return self.has_view_permission(request)
#
#
# class ExportCsvMixin:
#     export_fields = []
#
#     # (1) Опционально скрываем action 'export_to_csv' для TENANT
#     def get_actions(self, request):
#         actions = super().get_actions(request)
#         if not user_has_role(request.user, ["ADMIN", "LANDLORD"]):
#             if "export_to_csv" in actions:
#                 del actions[
#                     "export_to_csv"
#                 ]  ##️ Удаляем export, если роль — не ADMIN и не LANDLORD
#         return actions
#
#     # (2) Проверка разрешённых ролей внутри самого действия
#     def export_to_csv(self, request, queryset):
#         if not user_has_role(request.user, ["ADMIN", "LANDLORD"]):
#             self.message_user(
#                 request,
#                 "You do not have permission to export data.",
#                 level=messages.ERROR,
#             )
#             return None  # Не даём экспортировать
#
#         if not self.export_fields:
#             self.message_user(
#                 request, "Export fields not defined", level=messages.ERROR
#             )
#             return HttpResponse(status=400)
#
#         response = HttpResponse(content_type="text/csv")
#         response["Content-Disposition"] = "attachment; filename=export.csv"
#
#         writer = csv.writer(response)
#         writer.writerow(self.export_fields)
#
#         for obj in queryset:
#             row = []
#             for field in self.export_fields:
#                 # Поддержка полей с '__' (related fields)
#                 try:
#                     value = self._get_nested_attr(obj, field)
#                 except AttributeError:
#                     value = ""
#                 row.append(str(value))
#             writer.writerow(row)
#
#         return response
#
#     export_to_csv.short_description = "Export selected to CSV"
#
#     # (3) Вспомогательная функция для __ цепочек, если ещё не была реализована
#     def _get_nested_attr(self, obj, attr):
#         """Поддержка доступа к вложенным аттрибутам через '__'"""
#         for part in attr.split("__"):
#             obj = getattr(obj, part, "")
#             if obj is None:
#                 return ""
#         return obj
#
#
# class BaseTranslatableAdmin(
#     TranslationAdmin, ExportCsvMixin, RoleAccessMixin, admin.ModelAdmin
# ):
#     allowed_roles = ["ADMIN"]
#     actions = ["export_to_csv"]
#
#
# class BaseAdmin(RoleAccessMixin, admin.ModelAdmin):
#     allowed_roles = ["ADMIN"]
#
#
# class BaseHistoryAdmin(RoleAccessMixin, SimpleHistoryAdmin):
#     allowed_roles = ["ADMIN"]
#
#     def has_delete_permission(self, request, obj=None):
#         return request.user.is_superuser
#
#
# class AdminDisplayModeMixin:
#     """
#     Миксин для переключения между детализированным и простым режимом отображения
#     list_display, list_filter, search_fields в админке.
#     """
#
#     def _get_admin_attr(self, attr_name):
#         detailed = getattr(self, f"detailed_{attr_name}", None)
#         simple = getattr(self, f"simple_{attr_name}", None)
#         if getattr(settings, "ADMIN_DETAILED_MODE", False) and detailed is not None:
#             return detailed
#         if simple is not None:
#             return simple
#         return detailed or []
#
#     @property
#     def list_display(self):
#         return self._get_admin_attr("list_display")
#
#     @property
#     def list_filter(self):
#         return self._get_admin_attr("list_filter")
#
#     @property
#     def search_fields(self):
#         return self._get_admin_attr("search_fields")
#
#
# # Отмена регистрации ненужных моделей
# admin.site.unregister(AccessLog)
# admin.site.unregister(AccessFailureLog)
# admin.site.unregister(ClockedSchedule)
# admin.site.unregister(CrontabSchedule)
# admin.site.unregister(SolarSchedule)
# admin.site.unregister(IntervalSchedule)
# admin.site.unregister(TOTPDevice)
# admin.site.unregister(EmailAddress)
# admin.site.unregister(AccessAttempt)
# admin.site.unregister(PeriodicTask)
#
#
# @admin.register(TOTPDevice)
# class TOTPDeviceAdmin(BaseAdmin):
#     list_display = ("user", "name", "confirmed")
#     list_filter = ("confirmed",)
#     search_fields = ("user__email", "name")
#
#
# @admin.register(EmailAddress)
# class EmailAddressAdmin(BaseAdmin):
#     list_display = ("user", "email", "verified", "primary")
#     list_filter = ("verified", "primary")
#     search_fields = ("email", "user__email")
#
#
# @admin.register(AccessAttempt)
# class AccessAttemptAdmin(BaseAdmin, ExportCsvMixin):
#     list_display = ["ip_address", "username", "attempt_time", "failures_since_start"]
#     list_filter = ["attempt_time"]
#     search_fields = ("username", "ip_address")
#     readonly_fields = ["attempt_time"]
#     export_fields = ["ip_address", "username", "attempt_time", "failures_since_start"]
#     actions = ["export_to_csv", "reset_attempts"]
#
#     def reset_attempts(self, request, queryset):
#         queryset.delete()
#         self.message_user(request, "Selected access attempts have been reset.")
#
#     reset_attempts.short_description = "Reset selected access attempts"
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, ["ADMIN"])
#
#     def has_change_permission(self, request, obj=None):
#         return False
#
#
# @admin.register(PeriodicTask)
# class PeriodicTaskAdmin(BaseAdmin):
#     list_display = ("name", "task", "enabled", "last_run_at")
#     list_filter = ("enabled",)
#     search_fields = ("name", "task")
#     readonly_fields = ("last_run_at",)
#
#
# @admin.register(User)
# class UserAdmin(AdminDisplayModeMixin, BaseHistoryAdmin):
#     allowed_roles = ["ADMIN", "TENANT", "LANDLORD"]
#     actions = ["make_verified"]
#
#     detailed_list_display = (
#         "email",
#         "first_name",
#         "last_name",
#         "role",
#         "is_active",
#         "is_verified",
#         "is_staff",
#         "is_superuser",
#         "date_joined",
#     )
#     simple_list_display = ("email", "first_name", "last_name", "role")
#     history_list_display = ["email", "role", "is_active", "is_verified"]
#     detailed_list_filter = ("role", "is_active", "is_verified", "is_staff")
#     simple_list_filter = ("role",)
#     detailed_search_fields = ("email", "first_name", "last_name")
#     simple_search_fields = ("email",)
#     readonly_fields = ("date_joined", "last_login")
#
#     # Изменение 2: Права редактирования Tenant и Landlord — разрешаем менять только имя,
#     # фамилию, email, телефон (если есть)
#     def get_readonly_fields(self, request, obj=None):
#         user = request.user
#
#         if obj and (user_has_role(user, ["TENANT", "LANDLORD"])) and obj.pk == user.pk:
#             allowed = [
#                 "first_name",
#                 "last_name",
#                 "email",
#                 "phone",
#             ]  # <- добавь phone, если есть
#             readonly = [
#                 f.name for f in self.model._meta.fields if f.name not in allowed
#             ]
#             return readonly
#
#         return super().get_readonly_fields(request, obj)
#
#     # Изменение 1: get_queryset — Tenant и Landlord видят себя и других, связанных бронированиями
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#
#         if user_has_role(user, ["LANDLORD"]):
#             # Landlord видит себя и Tenant, у которых есть брони его объявлений
#             tenant_ids = (
#                 Booking.objects.filter(listing__user=user)
#                 .values_list("user_id", flat=True)
#                 .distinct()
#             )
#             return qs.filter(Q(pk=user.pk) | Q(pk__in=tenant_ids))
#
#         if user_has_role(user, ["TENANT"]):
#             # Tenant видит себя и Landlord, у которых у него брони
#             landlord_ids = (
#                 Booking.objects.filter(user=user)
#                 .values_list("listing__user_id", flat=True)
#                 .distinct()
#             )
#             return qs.filter(Q(pk=user.pk) | Q(pk__in=landlord_ids))
#
#         return qs.none()
#
#     # --------------------------
#
#     def has_delete_permission(self, request, obj=None):
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return True
#         if obj and user_has_role(user, ["LANDLORD"]):
#             return False
#         if obj and user_has_role(user, ["TENANT"]):
#             return obj.pk == user.pk  # Только сам себя
#         return False
#
#     @admin.action(description="Mark selected users as verified")
#     def make_verified(self, request, queryset):
#         queryset.update(is_verified=True)
#
#     make_verified.short_description = "Mark selected users as verified"
#
#     def formfield_for_manytomany(self, db_field, request, **kwargs):
#         if db_field.name == "groups":
#             if user_has_role(request.user, ["ADMIN"]):
#                 kwargs["queryset"] = Group.objects.all()
#                 if not request.user.groups.filter(name="Admin").exists():
#                     admin_group = Group.objects.filter(name="Admin").first()
#                     if admin_group:
#                         request.user.groups.add(admin_group)
#             elif user_has_role(request.user, ["TENANT"]):
#                 kwargs["queryset"] = Group.objects.filter(name="Tenant")
#             elif user_has_role(request.user, ["LANDLORD"]):
#                 kwargs["queryset"] = Group.objects.filter(name="Landlord")
#             else:
#                 kwargs["queryset"] = Group.objects.none()
#         return super().formfield_for_manytomany(db_field, request, **kwargs)
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_change_permission(self, request, obj=None):
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return True
#         if obj and user_has_role(user, ["TENANT", "LANDLORD"]):
#             return obj.pk == user.pk
#         if obj is None:
#             return user_has_role(request.user, self.get_allowed_roles())
#         return False
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_add_permission(self, request):
#         # Добавлять пользователей может только Admin
#         return user_has_role(request.user, ["ADMIN"])
#
#
# @admin.register(Listing)
# class ListingAdmin(AdminDisplayModeMixin, BaseTranslatableAdmin):
#     allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
#     form = ListingForm
#     filter_horizontal = ("amenities",)  # Использует виджет FilteredSelectMultiple
#
#     inlines = [AvailabilitySlotInline]  # , LocationInline]
#     export_fields = [
#         "title_en",
#         "title_de",
#         "title_ru",
#         "user__email",
#         "price_per_night",
#         "city",
#         "popularity",
#     ]
#     actions = ["export_to_csv", "toggle_active", "export_top_listings"]
#
#     class AmenityFilter(SimpleListFilter):
#         title = "Amenities (Удобства)"
#         parameter_name = "amenity"
#
#         def lookups(self, request, model_admin):
#             return [(a.id, a.name) for a in Amenity.objects.all()]
#
#         def queryset(self, request, queryset):
#             if self.value():
#                 return queryset.filter(amenities__id=self.value())
#             return queryset
#
#     detailed_list_display = (
#         "title_en",
#         "user",
#         "city",
#         "country",
#         "price_per_night",
#         "availability_range",
#         "amenities_list",  # ← добавили
#         "is_active",
#         "popularity",
#         "created_at",
#     )
#     simple_list_display = ("title_en", "user", "price_per_night", "photo_preview")
#     readonly_fields = ("photo_preview",)
#
#     history_list_display = [
#         "title_en",
#         "title_de",
#         "title_ru",
#         "price_per_night",
#         "is_active",
#         "popularity",
#         "amenities",
#     ]
#     detailed_list_filter = (
#         "is_active",
#         "property_type",
#         "city",
#         "country",
#         "created_at",
#         AmenityFilter,
#     )
#     simple_list_filter = ("is_active",)
#     detailed_search_fields = (
#         "title_en",
#         "description_en",
#         "user__email",
#         "city",
#         "country",
#         "address",
#     )
#     simple_search_fields = ("title_en", "user__email")
#
#     def availability_range(self, obj):
#         slots = obj.availability_slots.filter(is_available=True).order_by("date")
#         if not slots.exists():
#             return "Нет доступных дат"
#
#         first = date_format(slots.first().date, "DATE_FORMAT")
#         last = date_format(slots.last().date, "DATE_FORMAT")
#         return f"{first} — {last}"
#
#     availability_range.short_description = "Availability Slots"
#
#     def amenities_list(self, obj):
#         return ", ".join([a.name for a in obj.amenities.all()])
#
#     amenities_list.short_description = "Amenities"
#
#     def photo_preview(self, obj):
#         if not obj.photos:
#             return "-"
#         tags = []
#         for url in obj.photos:
#             tags.append(f'<img src="/{url}" style="max-height:80px; margin:2px;" />')
#         return mark_safe("".join(tags))
#
#     photo_preview.short_description = "Photos"
#
#     def toggle_active(self, request, queryset):
#         updated_count = 0
#         for obj in queryset:
#             if self.has_change_permission(request, obj):  # 👈 проверка прав
#                 obj.is_active = not obj.is_active
#                 obj.save()
#                 updated_count += 1
#         if updated_count > 0:
#             self.message_user(
#                 request,
#                 f"Toggled active status for {updated_count} listings.",
#                 level=messages.SUCCESS,
#             )
#         else:
#             self.message_user(
#                 request,
#                 "No listings were updated. You may not have permission.",
#                 level=messages.WARNING,
#             )
#
#     toggle_active.short_description = "Toggle active status for selected listings"
#
#     def export_top_listings(self, request, queryset):
#         response = HttpResponse(content_type="text/csv")
#         response["Content-Disposition"] = 'attachment; filename="top_listings.csv"'
#         writer = csv.writer(response)
#         writer.writerow(
#             [
#                 "Title (EN)",
#                 "Title (DE)",
#                 "Title (RU)",
#                 "User Email",
#                 "Price Per Night",
#                 "City",
#                 "Popularity",
#             ]
#         )
#         for obj in queryset.order_by("-popularity")[:5]:
#             writer.writerow(
#                 [
#                     obj.title_en,
#                     obj.title_de,
#                     obj.title_ru,
#                     obj.user.email,
#                     obj.price_per_night,
#                     obj.address,
#                     obj.popularity,
#                 ]
#             )
#         return response
#
#     export_top_listings.short_description = "Export top 5 listings to CSV"
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#
#         if user_has_role(user, ["LANDLORD"]):
#             return qs.filter(user=user)  # ✅ Только свои объявления
#
#         if user_has_role(user, ["TENANT"]):
#             return qs.filter(is_active=True)  # ✅ Только активные
#
#         return qs.none()
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["LANDLORD", "ADMIN"])
#
#     def has_view_permission(self, request, obj=None):
#         # Все роли могут просматривать
#         return self.has_module_permission(request)
#
#     def has_change_permission(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return True
#
#         if user_has_role(user, ["LANDLORD"]):
#             return obj is None or (obj and obj.user == user)
#
#         # Tenant может только просматривать
#         return False
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#
# @admin.register(Booking)
# class BookingAdmin(
#     AdminDisplayModeMixin,
#     ExportCsvMixin,  # ✅ отдельно
#     BaseAdmin,  # ✅ включает RoleAccessMixin
# ):
#     allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
#     export_fields = [
#         "listing__title_en",
#         "user__email",
#         "status",
#         "start_date",
#         "end_date",
#         "total_price",
#     ]
#     actions = ["confirm_booking", "export_to_csv"]
#
#     detailed_list_display = (
#         "listing",
#         "user",
#         "start_date",
#         "end_date",
#         "status",
#         "total_price",
#         "created_at",
#     )
#     simple_list_display = ("listing", "user", "status", "start_date", "end_date")
#
#     detailed_list_filter = ("status", "start_date", "end_date")
#     simple_list_filter = ("status", "start_date")
#
#     detailed_search_fields = (
#         "listing__title_en",
#         "listing__title_de",
#         "listing__title_ru",
#         "user__email",
#     )
#     simple_search_fields = ("listing__title_en", "user__email")
#
#     def confirm_booking(self, request, queryset):
#         queryset.update(status="CONFIRMED")
#
#     confirm_booking.short_description = "Confirm selected bookings"
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#
#         if user_has_role(user, ["LANDLORD"]):
#             return qs.filter(listing__user=user)
#
#         if user_has_role(user, ["TENANT"]):
#             return qs.filter(user=user)
#
#         return qs.none()
#
#     def has_delete_permission(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return True
#
#         if obj and user_has_role(user, ["TENANT"]):
#             return obj.user == user  # Только своё
#
#         if obj and user_has_role(user, ["LANDLORD"]):
#             return obj.listing.user == user  # Только по своим объявлениям
#
#         return False
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["TENANT", "ADMIN"])
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_change_permission(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return True
#
#         if obj and user_has_role(user, ["LANDLORD"]):
#             return obj.listing.user == user
#
#         if obj and user_has_role(user, ["TENANT"]):
#             return obj.user == user
#
#         # Разрешаем доступ к changelist для всех ролей
#         if obj is None:
#             return user_has_role(request.user, self.get_allowed_roles())
#
#         return False
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#
# @admin.register(Review)
# class ReviewAdmin(AdminDisplayModeMixin, ExportCsvMixin, BaseAdmin):
#     allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
#     export_fields = [
#         "user__email",
#         "booking__listing__title_en",
#         "rating",
#         "comment",
#         "is_approved",
#     ]
#     actions = ["approve_review", "export_to_csv", "respond_to_reviews"]
#
#     detailed_list_display = (
#         "action_links",
#         "booking",
#         "user",
#         "user_email",
#         "rating",
#         "is_approved",
#         "created_at",
#     )
#     simple_list_display = ("action_links", "booking", "user_email", "rating", "comment")
#
#     detailed_list_filter = ("is_approved", "rating", "created_at")
#     simple_list_filter = ("is_approved",)
#
#     detailed_search_fields = (
#         "comment",
#         "user__email",
#         "booking__listing__title_en",
#         "booking__listing__title_de",
#         "booking__listing__title_ru",
#     )
#     simple_search_fields = ("user__email",)
#
#     fieldsets = (
#         (None, {"fields": ("booking", "user", "rating", "comment")}),
#         (
#             "Ответ арендодателя",
#             {
#                 "fields": ("landlord_response",),
#                 "description": "Здесь вы можете ответить на отзыв арендатора.",
#             },
#         ),
#     )
#
#     def action_links(self, obj):
#         user = getattr(self, "request_user", None)
#         if not user:
#             return ""
#         url = reverse("admin:reviews_review_change", args=[obj.pk])
#         if user_has_role(user, ["LANDLORD"]):
#             return format_html(
#                 '<a class="button" href="{}">Ответить на отзыв</a> &nbsp; '
#                 '<a class="button" href="{}">Просмотр</a>',
#                 url,
#                 url,
#             )
#         return format_html('<a class="button" href="{}">Изменить</a>', url)
#
#     action_links.short_description = "Действия"
#
#     class HasLandlordResponseFilter(SimpleListFilter):
#         title = "Наличие ответа арендодателя"
#         parameter_name = "has_landlord_response"
#
#         def lookups(self, request, model_admin):
#             return (
#                 ("yes", "Есть ответ"),
#                 ("no", "Нет ответа"),
#             )
#
#         def queryset(self, request, queryset):
#
#             if self.value() == "yes":
#                 return queryset.exclude(landlord_response__exact="").exclude(
#                     landlord_response__isnull=True
#                 )
#             if self.value() == "no":
#                 return queryset.filter(landlord_response__exact="") | queryset.filter(
#                     landlord_response__isnull=True
#                 )
#             return queryset
#
#     list_filter = ("is_approved", "rating", "created_at", HasLandlordResponseFilter)
#
#     def user_email(self, obj):
#         return obj.user.email
#
#     user_email.short_description = "User Email"
#
#     def approve_review(self, request, queryset):
#         queryset.update(is_approved=True)
#
#     approve_review.short_description = "Approve selected reviews"
#
#     def get_queryset(self, request):
#         self.request_user = request.user  # используется в action_links
#
#         qs = super().get_queryset(request)
#         user = request.user
#         print(f"[ReviewAdmin] get_queryset for {user.email} ({user.role})")
#
#         if user_has_role(user, ["ADMIN"]):
#             print("[ReviewAdmin] ADMIN: return all")
#             return qs
#         if user_has_role(user, ["LANDLORD"]):
#             filtered_qs = qs.filter(booking__listing__user=user)
#             print(f"[ReviewAdmin] LANDLORD: filtered_qs.count = {filtered_qs.count()}")
#             return filtered_qs
#         if user_has_role(user, ["TENANT"]):
#             filtered_qs = qs.filter(user=user)
#             print(f"[ReviewAdmin] TENANT: filtered_qs.count = {filtered_qs.count()}")
#             return filtered_qs
#
#         print("[ReviewAdmin] No access - returning empty queryset")
#         return qs.none()
#
#     def get_readonly_fields(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["LANDLORD"]) and obj:
#             # Только разрешить редактировать landlord_response
#             return [
#                 f.name for f in self.model._meta.fields if f.name != "landlord_response"
#             ]
#         return super().get_readonly_fields(request, obj)
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["TENANT", "ADMIN"])
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_change_permission(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return True
#         if obj and user_has_role(user, ["LANDLORD"]):
#             return obj.booking.listing.user == user
#         if obj and user_has_role(user, ["TENANT"]):
#             return obj.user == user
#         if obj is None:
#             return True
#         return False
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, self.get_allowed_roles())
#
#     def has_delete_permission(self, request, obj=None):
#         user = request.user
#
#         if user_has_role(user, ["ADMIN"]):
#             return True
#
#         if obj and user_has_role(user, ["TENANT"]):
#             return obj.user == user  # Только свои отзывы
#
#         return False  # Landlord не может удалять
#
#     @admin.action(description="Ответить на отзыв")
#     def respond_to_reviews(self, request, queryset):
#         user = request.user
#
#         if not user_has_role(user, ["LANDLORD"]):
#             self.message_user(
#                 request,
#                 "Только Landlord может отвечать на отзывы.",
#                 level=messages.ERROR,
#             )
#             return
#
#         if queryset.count() != 1:
#             self.message_user(
#                 request, "Выберите ровно один отзыв для ответа.", level=messages.WARNING
#             )
#             return
#
#         obj = queryset.first()
#
#         # Проверка: Landlord может ответить только на отзывы к своим объявлениям
#         if obj.booking.listing.user != user:
#             self.message_user(
#                 request,
#                 "Вы можете отвечать только на отзывы по своим объявлениям.",
#                 level=messages.ERROR,
#             )
#             return
#
#         # Перенаправляем на стандартную admin change form
#         url = reverse("admin:reviews_review_change", args=[obj.pk])
#         return redirect(url)
#
#     def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
#         extra_context = extra_context or {}
#         if user_has_role(request.user, ["LANDLORD"]):
#             extra_context["title"] = "Ответить на отзыв"
#         return super().changeform_view(request, object_id, form_url, extra_context)
#
#     def changelist_view(self, request, extra_context=None):
#         qs = self.get_queryset(request)
#         if not qs.exists() and user_has_role(request.user, ["LANDLORD"]):
#             messages.info(request, "У вас пока нет отзывов.")
#         return super().changelist_view(request, extra_context=extra_context)
#
#
# @admin.register(SearchHistory)
# class SearchHistoryAdmin(ExportCsvMixin, BaseAdmin):
#     allowed_roles = ["ADMIN", "LANDLORD"]
#     export_fields = ["user__email", "query", "timestamp"]
#     actions = ["export_to_csv"]
#
#     list_display = ("user", "query", "timestamp")
#     list_filter = ("timestamp",)
#     search_fields = ("query", "user__email")
#     readonly_fields = ("timestamp",)
#     history_list_display = ["query", "timestamp"]
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#         if user_has_role(user, ["LANDLORD"]):
#             return qs.filter(user=user)
#         return qs.none()
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_change_permission(self, request, obj=None):
#         # По умолчанию запрещаем редактирование для лендлорда
#         return user_has_role(request.user, ["ADMIN"])
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["ADMIN"])
#
#
# @admin.register(ViewHistory)
# class ViewHistoryAdmin(ExportCsvMixin, BaseAdmin):
#     allowed_roles = ["ADMIN", "LANDLORD"]
#     export_fields = ["user__email", "listing__title_en", "timestamp"]
#     actions = ["export_to_csv"]
#
#     list_display = ("user", "listing", "timestamp")
#     list_filter = ("timestamp",)
#     search_fields = (
#         "user__email",
#         "listing__title_en",
#         "listing__title_de",
#         "listing__title_ru",
#     )
#     readonly_fields = ("timestamp",)
#     history_list_display = ["listing", "timestamp"]
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#         if user_has_role(user, ["LANDLORD"]):
#             return qs.filter(listing__user=user)
#         return qs.none()
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_change_permission(self, request, obj=None):
#         # По умолчанию запрещаем редактирование для лендлорда
#         return user_has_role(request.user, ["ADMIN"])
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["ADMIN"])
#
#
# class LocationForm(forms.ModelForm):
#     class Meta:
#         model = Location
#         fields = "__all__"
#
#
# @admin.register(Location)
# class LocationAdmin(AdminDisplayModeMixin, LeafletGeoAdmin, BaseHistoryAdmin):
#
#     allowed_roles = ["ADMIN", "LANDLORD", "TENANT"]
#     form = LocationForm
#
#     list_display = (
#         "listing",
#         "street",
#         "city",
#         "federal_state",
#         "country_display",
#         "get_latitude",
#         "get_longitude",
#         "photo_preview",
#     )
#     list_filter = ("city", "federal_state")
#     search_fields = ("street", "city", "federal_state", "listing__country__iexact")
#
#     def get_readonly_fields(self, request, obj=None):
#         base = ["photo_preview", "country_display"]
#         if getattr(request.user, "role", None) == "TENANT":
#             base.append("readonly_coordinates_map")
#         return base
#
#     def get_fieldsets(self, request, obj=None):
#         if getattr(request.user, "role", None) == "TENANT":
#             return (
#                 (
#                     None,
#                     {
#                         "fields": (
#                             "listing",
#                             "street",
#                             "postal_code",
#                             "city",
#                             "federal_state",
#                             "country_display",
#                             "readonly_coordinates_map",
#                         )
#                     },
#                 ),
#                 (
#                     "Дополнительно",
#                     {"fields": ("photo_preview",), "classes": ("collapse",)},
#                 ),
#             )
#         return (
#             (
#                 None,
#                 {
#                     "fields": (
#                         "listing",
#                         "street",
#                         "postal_code",
#                         "city",
#                         "federal_state",
#                         "country_display",
#                         "coordinates",
#                     )
#                 },
#             ),
#             ("Дополнительно", {"fields": ("photo_preview",), "classes": ("collapse",)}),
#         )
#
#     # ==== HELPERS ====
#     def get_latitude(self, obj):
#         return obj.coordinates.y if obj.coordinates else None
#
#     get_latitude.short_description = "Latitude"
#
#     def get_longitude(self, obj):
#         return obj.coordinates.x if obj.coordinates else None
#
#     get_longitude.short_description = "Longitude"
#
#     def readonly_coordinates_map(self, obj):
#         if not obj or not obj.coordinates:
#             return "-"
#         lat, lon = obj.coordinates.y, obj.coordinates.x
#         return mark_safe(
#             f"""
#             <iframe width="100%" height="250" style="border:1px solid #ccc"
#                     src="https://www.openstreetmap.org/export/embed.html?bbox={lon-0.01}%2C{lat-0.01}%2C{lon+0.01}%2C{lat+0.01}&layer=mapnik&marker={lat}%2C{lon}">
#             </iframe>
#             <br><a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}" target="_blank">View on OpenStreetMap</a>
#         """
#         )
#
#     readonly_coordinates_map.short_description = "Карта (только просмотр)"
#
#     def photo_preview(self, obj):
#         if obj.listing and obj.listing.photos:
#             tags = []
#             for url in (
#                 obj.listing.photos
#                 if isinstance(obj.listing.photos, (list, tuple))
#                 else [obj.listing.photos]
#             ):
#                 if url:
#                     tags.append(
#                         f'<img src="/{url}" style="max-height:100px; max-width:100px; object-fit:contain; margin:2px;" />'
#                     )
#             return mark_safe("".join(tags))
#         return "-"
#
#     photo_preview.short_description = "Photos"
#
#     def country_display(self, obj):
#         return obj.listing.country if obj.listing else "-"
#
#     country_display.short_description = "Country"
#
#     # ==== PERMISSIONS ====
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return qs
#         if user_has_role(user, ["LANDLORD"]):
#             return qs.filter(listing__user=user).distinct()
#         if user_has_role(user, ["TENANT"]):
#             return qs.filter(listing__is_active=True)
#         return qs.none()
#
#     def has_view_permission(self, request, obj=None):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD", "TENANT"])
#
#     def has_module_permission(self, request):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD", "TENANT"])
#
#     def has_add_permission(self, request):
#         return user_has_role(request.user, ["ADMIN", "LANDLORD"])
#
#     def has_change_permission(self, request, obj=None):
#         user = request.user
#         return user_has_role(user, ["ADMIN", "LANDLORD"])
#
#     def has_delete_permission(self, request, obj=None):
#         user = request.user
#         if user_has_role(user, ["ADMIN"]):
#             return True
#         return obj and user_has_role(user, ["LANDLORD"]) and obj.listing.user == user
