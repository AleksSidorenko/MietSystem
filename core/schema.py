# core/schema.py

from drf_spectacular.utils import extend_schema
from core.views import HealthCheckAPIView

@extend_schema(
    responses={
        200: {
            'type': 'object',
            'properties': {
                'time': {'type': 'string', 'format': 'date-time'},
                'database': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['online', 'offline']},
                        'error': {'type': 'string', 'nullable': True},
                    },
                },
                'redis': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['online', 'offline']},
                        'error': {'type': 'string', 'nullable': True},
                    },
                },
                'celery': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['online', 'offline']},
                        'error': {'type': 'string', 'nullable': True},
                    },
                },
                's3': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['online', 'offline']},
                        'error': {'type': 'string', 'nullable': True},
                    },
                },
                'localization': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['online', 'offline']},
                        'languages': {'type': 'array', 'items': {'type': 'string'}},
                        'error': {'type': 'string', 'nullable': True},
                    },
                },
                'users': {
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'admins': {'type': 'integer'},
                        'landlords': {'type': 'integer'},
                        'tenants': {'type': 'integer'},
                    },
                },
                'stats': {
                    'type': 'object',
                    'properties': {
                        'listings': {'type': 'integer'},
                        'bookings': {'type': 'integer'},
                        'reviews': {'type': 'integer'},
                        'locations': {'type': 'integer'},
                    },
                },
                'system_metrics': {
                    'type': 'object',
                    'properties': {
                        'cpu_percent': {'type': 'number'},
                        'memory_percent': {'type': 'number'},
                        'disk_free_gb': {'type': 'number'},
                        'celery_tasks': {'type': 'integer'},
                    },
                },
            },
        },
    },
    description="Health check endpoint for monitoring system services.",
)
class HealthCheckAPIView(HealthCheckAPIView):
    pass
