# core/test_settings.py

from .settings import *  # Импортируем все из основных настроек

# Отключаем CSRF в тестах
# Это очень частая практика для DRF тестов, чтобы избежать проблем с CSRF
# при использовании APIClient, который по умолчанию не отправляет CSRF-токены.
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.TokenAuthentication",
    "rest_framework.authentication.SessionAuthentication",  # Оставьте это, если используете SessionAuthentication
)

# Отключить Django CSRF middleware для тестов
# Это предотвратит вызов _get_secret, который ищет request.COOKIES
MIDDLEWARE = [mw for mw in MIDDLEWARE if "CsrfViewMiddleware" not in mw]
