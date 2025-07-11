### `bookings/admin.py`
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import Booking
#
# @admin.register(Booking)
# class BookingAdmin(BaseHistoryAdmin):
#     list_display = ('listing', 'user', 'start_date', 'end_date', 'status', 'total_price', 'created_at')
#     list_filter = ('status', 'start_date', 'end_date')
#     search_fields = ('listing__title', 'user__email')
#     readonly_fields = ('created_at',)
#     history_list_display = ['status', 'start_date', 'end_date', 'total_price']
#     actions = ['confirm_booking']
#
#     def confirm_booking(self, request, queryset):
#         queryset.update(status='CONFIRMED')
#     confirm_booking.short_description = "Confirm selected bookings"
#
#     def has_view_permission(self, request, obj=None):
#         if request.user.is_superuser or request.user.role == 'ADMIN':
#             return True
#         if obj is not None:
#             return obj.user == request.user or obj.listing.user == request.user
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return request.user.is_superuser or request.user.role == 'ADMIN'


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import Booking
#
# @admin.register(Booking)
# class BookingAdmin(SimpleHistoryAdmin):
#     list_display = ('listing', 'user', 'start_date', 'end_date', 'status')
#     list_filter = ('status', 'start_date')
#     search_fields = ('listing__title', 'user__email')
#     actions = ['confirm_booking']
#
#     def confirm_booking(self, request, queryset):
#         queryset.update(status='CONFIRMED')
#     confirm_booking.short_description = "Confirm selected bookings"
