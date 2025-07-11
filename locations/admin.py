#### `locations/admin.py`
### Вариант: Гибридный подход с базовым классом

# from django.contrib import admin
# from utils.admin import BaseHistoryAdmin
# from .models import Location
#
# @admin.register(Location)
# class LocationAdmin(BaseHistoryAdmin):
#     list_display = ('listing', 'city', 'federal_state', 'postal_code', 'street', 'latitude', 'longitude')
#     list_filter = ('city', 'federal_state')
#     search_fields = ('listing__title', 'city', 'street', 'postal_code')
#     history_list_display = ['city', 'federal_state', 'postal_code']


# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
# from .models import Location
#
# @admin.register(Location)
# class LocationAdmin(SimpleHistoryAdmin):
#     list_display = ('listing', 'city', 'federal_state', 'latitude', 'longitude')
#     list_filter = ('city', 'federal_state')
#     search_fields = ('listing__title', 'city')
