### `listings/admin.py`
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import Listing
# from django.http import HttpResponse
# import csv
#
# @admin.register(Listing)
# class ListingAdmin(BaseHistoryAdmin):
#     list_display = ('title', 'user', 'price_per_night', 'city', 'is_active', 'popularity', 'created_at')
#     list_filter = ('is_active', 'property_type', 'city', 'federal_state', 'created_at')
#     search_fields = ('title', 'description', 'address', 'user__email')
#     readonly_fields = ('created_at',)
#     history_list_display = ['title', 'price_per_night', 'is_active', 'popularity']
#     actions = ['export_top_listings']
#
#     def export_top_listings(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="top_listings.csv"'
#         writer = csv.writer(response)
#         writer.writerow(['Title', 'User Email', 'Price Per Night', 'City', 'Popularity'])
#         for obj in queryset.order_by('-popularity')[:5]:
#             writer.writerow([obj.title, obj.user.email, obj.price_per_night, obj.city, obj.popularity])
#         return response
#     export_top_listings.short_description = "Export top 5 listings to CSV"
#
#     def has_view_permission(self, request, obj=None):
#         if request.user.is_superuser or request.user.role == 'ADMIN':
#             return True
#         if request.user.role == 'LANDLORD' and obj is not None:
#             return obj.user == request.user
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         if request.user.is_superuser or request.user.role == 'ADMIN':
#             return True
#         if request.user.role == 'LANDLORD' and obj is not None:
#             return obj.user == request.user
#         return False


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import Listing
#
# @admin.register(Listing)
# class ListingAdmin(SimpleHistoryAdmin):
#     list_display = ('title', 'user', 'price_per_night', 'city', 'is_active')
#     list_filter = ('is_active', 'property_type', 'city', 'federal_state')
#     search_fields = ('title', 'description', 'address')
