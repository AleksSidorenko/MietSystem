### `reviews/admin.py`
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import Review
#
# @admin.register(Review)
# class ReviewAdmin(BaseHistoryAdmin):
#     list_display = ('booking', 'user', 'rating', 'is_approved', 'created_at')
#     list_filter = ('is_approved', 'rating', 'created_at')
#     search_fields = ('comment', 'user__email', 'booking__listing__title')
#     readonly_fields = ('created_at',)
#     history_list_display = ['rating', 'comment', 'is_approved']
#     actions = ['approve_review']
#
#     def approve_review(self, request, queryset):
#         queryset.update(is_approved=True)
#     approve_review.short_description = "Approve selected reviews"
#
#     def has_view_permission(self, request, obj=None):
#         if request.user.is_superuser or request.user.role == 'ADMIN':
#             return True
#         if obj is not None:
#             return obj.user == request.user
#         return False


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import Review
#
# @admin.register(Review)
# class ReviewAdmin(SimpleHistoryAdmin):
#     list_display = ('booking', 'user', 'rating', 'is_approved')
#     list_filter = ('is_approved', 'rating')
#     search_fields = ('comment', 'user__email')
#     actions = ['approve_review']
#
#     def approve_review(self, request, queryset):
#         queryset.update(is_approved=True)
#     approve_review.short_description = "Approve selected reviews"
