### users/admin.py
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import User
#
# @admin.register(User)
# class UserAdmin(BaseHistoryAdmin):
#     list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
#     list_filter = ('role', 'is_active', 'is_verified', 'is_staff')
#     search_fields = ('email', 'first_name', 'last_name')
#     readonly_fields = ('date_joined',)
#     history_list_display = ['email', 'role', 'is_active', 'is_verified']
#     actions = ['make_verified']
#
#     def make_verified(self, request, queryset):
#         queryset.update(is_verified=True)
#     make_verified.short_description = "Mark selected users as verified"


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import User
#
# @admin.register(User)
# class UserAdmin(SimpleHistoryAdmin):
#     list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified')
#     list_filter = ('role', 'is_active', 'is_verified')
#     search_fields = ('email', 'first_name', 'last_name')
#     actions = ['make_verified']
#
#     def make_verified(self, request, queryset):
#         queryset.update(is_verified=True)
#     make_verified.short_description = "Mark selected users as verified"
