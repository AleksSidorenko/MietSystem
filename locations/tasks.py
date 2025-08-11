# locations/tasks.py
import geocoder
from celery import shared_task
from sentry_sdk import capture_exception

from .models import Location


@shared_task(bind=True, max_retries=3)
def geocode_address(self, location_id):
    try:
        location = Location.objects.get(id=location_id)
        address = (
            f"{location.street}, {location.city}, {location.federal_state}, Germany"
        )
        g = geocoder.osm(address)
        if g.ok:
            location.latitude = g.lat
            location.longitude = g.lng
            location.save()
        else:
            raise Exception("Geocoding failed")
    except Location.DoesNotExist:
        capture_exception()
        raise self.retry(countdown=60)
    except Exception as e:
        capture_exception(e)
        raise self.retry(countdown=60)
