### analytics/admin.py
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import SearchHistory, ViewHistory
# from django.http import HttpResponse
# import csv
#
# @admin.register(SearchHistory)
# class SearchHistoryAdmin(BaseHistoryAdmin):
#     list_display = ('user', 'query', 'timestamp')
#     list_filter = ('timestamp',)
#     search_fields = ('user__email', 'query')
#     readonly_fields = ('timestamp',)
#     history_list_display = ['query', 'timestamp']
#     actions = ['export_to_csv']
#
#     def export_to_csv(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="search_history.csv"'
#         writer = csv.writer(response)
#         writer.writerow(['User Email', 'Query', 'Timestamp'])
#         for obj in queryset:
#             writer.writerow([obj.user.email, obj.query, obj.timestamp])
#         return response
#     export_to_csv.short_description = "Export selected search history to CSV"
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return False
#
# @admin.register(ViewHistory)
# class ViewHistoryAdmin(BaseHistoryAdmin):
#     list_display = ('user', 'listing', 'timestamp')
#     list_filter = ('timestamp',)
#     search_fields = ('user__email', 'listing__title')
#     readonly_fields = ('timestamp',)
#     history_list_display = ['listing', 'timestamp']
#     actions = ['export_to_csv']
#
#     def export_to_csv(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="view_history.csv"'
#         writer = csv.writer(response)
#         writer.writerow(['User Email', 'Listing Title', 'Timestamp'])
#         for obj in queryset:
#             writer.writerow([obj.user.email, obj.listing.title, obj.timestamp])
#         return response
#     export_to_csv.short_description = "Export selected view history to CSV"
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return False


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import SearchHistory, ViewHistory
#
#
# @admin.register(SearchHistory)
# class SearchHistoryAdmin(SimpleHistoryAdmin):
#     list_display = ('user', 'query', 'timestamp')
#     list_filter = ('timestamp',)
#     search_fields = ('user__email', 'query')
#     readonly_fields = ('timestamp',)
#
#     def has_add_permission(self, request):
#         # Запрещаем добавление записей вручную
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         # Только просмотр, изменения невозможны
#         return False
#
#
# @admin.register(ViewHistory)
# class ViewHistoryAdmin(SimpleHistoryAdmin):
#     list_display = ('user', 'listing', 'timestamp')
#     list_filter = ('timestamp',)
#     search_fields = ('user__email', 'listing__title')
#     readonly_fields = ('timestamp',)
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return False
