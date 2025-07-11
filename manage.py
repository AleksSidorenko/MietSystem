### `manage.py`
# <xaiArtifact artifact_id="db1908fb-35f6-423d-b221-5cfe7c9e1c83" artifact_version_id="e035dea7-5179-4148-9d8c-e83fc262ed91" title="manage.py" contentType="text/python">
#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
# </xaiArtifact>

# **Пояснение**: Ядро включает настройки
# (с `django-simple-history`, Celery Beat, middleware), маршруты, исключения, WSGI, админку с 2FA и точку входа.


#!/usr/bin/env python
# """Django's command-line utility for administrative tasks."""
# import os
# import sys
#
#
# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project_MietSystem.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)
#
#
# if __name__ == '__main__':
#     main()
