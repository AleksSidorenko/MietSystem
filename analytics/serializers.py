# analytics/serializers.py

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import SearchHistory, ViewHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "user", "query", "timestamp"]
        read_only_fields = ["id", "user", "timestamp"]
        swagger_schema_fields = {"description": "Serializer for search history"}

    def validate_query(self, value):
        if len(value) < 1 or len(value) > 255:
            raise serializers.ValidationError(
                _("Query must be between 1 and 255 characters")
            )
        return value


class ViewHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewHistory
        fields = ["id", "user", "listing", "timestamp"]
        read_only_fields = ["id", "user", "timestamp"]
        swagger_schema_fields = {"description": "Serializer for view history"}
