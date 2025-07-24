# core/settings.py
import os
from datetime import timedelta
from pathlib import Path

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

ADMIN_DEBUG_MODE = True
ADMIN_DETAILED_MODE = True

# Безопасность для production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (51.1657, 10.4515),
    "DEFAULT_ZOOM": 6,
    "MIN_ZOOM": 3,
    "MAX_ZOOM": 18,
    "SCALE": "both",
    "RESET_VIEW": True,
}

INSTALLED_APPS = [
    "modeltranslation",  # Для перевода моделей
    "django.contrib.gis",
    "leaflet",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "django_extensions",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "axes",
    "allauth",
    "allauth.account",
    "django_celery_beat",
    "django_ratelimit",
    "storages",
    "simple_history",
    "utils",
    "users",
    "listings.apps.ListingsConfig",
    "bookings",
    "reviews",
    "analytics",
    "locations",
    'rangefilter',
    'rest_framework.authtoken',
    'drf_yasg',
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Для мультиязычности
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "axes.middleware.AxesMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
    "core.middleware.MetaResponseMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",  # Изменено на DEBUG для отладки мультиязычности
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/debug.log",
        },
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.SentryHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "sentry"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.template": {  # Логирование шаблонов
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

ROOT_URLCONF = "core.urls"
AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "en"  # Язык по умолчанию
LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
    ("de", "Deutsch"),
]
LOCALE_PATHS = [
    BASE_DIR / "locale",
]
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Modeltranslation settings
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ["en", "de", "ru"]
MODELTRANSLATION_AUTO_POPULATE = "all"

DATE_FORMAT = "d.m.Y"

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.CookieJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "utils.renderers.CustomRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/minute",
        "user": "100/minute",
    },
}
SPECTACULAR_SETTINGS = {
    "TITLE": "MietSystem API",
    "DESCRIPTION": "Документация API для MietSystem",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # "SCHEMA_PATH_PREFIX_TRIM": True,
    "SECURITY": [{"cookieJWT": []}],
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_REFRESH": "refresh_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_SAMESITE": "Strict",
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
FRONTEND_URL = config("FRONTEND_URL")

CELERY_BROKER_URL = config("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = config("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "update-popularity-every-hour": {
        "task": "utils.tasks.update_popularity",
        "schedule": 3600.0,
    },
    "cleanup-expired-tokens-every-day": {
        "task": "users.tasks.cleanup_expired_tokens",
        "schedule": 86400.0,
    },
    "cleanup-old-bookings-every-day": {
        "task": "bookings.tasks.cleanup_old_bookings",
        "schedule": 86400.0,
    },
    "cleanup-old-views-every-day": {
        "task": "analytics.tasks.cleanup_old_views",
        "schedule": 86400.0,
    },
}

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = "eu-central-1"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

SLACK_TOKEN = config("SLACK_TOKEN", default="")

AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCK_OUT_AT_FAILURE = True
AXES_LOCKOUT_TEMPLATE = "core/lockout.html"

RATELIMIT_ENABLE = True
RATELIMIT_RATE = "100/m"
RATELIMIT_BLOCK = True

SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

LOGIN_REDIRECT_URL = '/'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_COOKIE_SECURE = False  # Для локального тестирования
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Сессия завершается при закрытии браузера

# SESSION_COOKIE_NAME = "miet_sessionid"
# CSRF_COOKIE_NAME = "miet_csrftoken"
# # SESSION_COOKIE_AGE = 1209600  # 2 недели
# # SESSION_COOKIE_SECURE = False  # Для разработки, установите True для HTTPS в продакшене
# SESSION_COOKIE_SECURE = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ADMIN_SITE_HEADER = "MietSystem Admin"
ADMIN_SITE_TITLE = "MietSystem"
ADMIN_INDEX_TITLE = "Добро пожаловать в админ-панель MietSystem"

SILENCED_SYSTEM_CHECKS = ["models.W036"]

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)


LOGIN_URL = '/admin/login/'



# import os
# from datetime import timedelta
# from pathlib import Path
#
# import sentry_sdk
# from decouple import config
# from sentry_sdk.integrations.celery import CeleryIntegration
# from sentry_sdk.integrations.django import DjangoIntegration
#
# BASE_DIR = Path(__file__).resolve().parent.parent
#
# SECRET_KEY = config("SECRET_KEY")
# DEBUG = config("DEBUG", default=False, cast=bool)
# ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
#
# ADMIN_DEBUG_MODE = True  # True — подробный режим, False — компактный
# ADMIN_DETAILED_MODE = True
#
# # Безопасность для production
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = 'DENY'
#
# LEAFLET_CONFIG = {
#     "DEFAULT_CENTER": (51.1657, 10.4515),  # Центр Германии
#     "DEFAULT_ZOOM": 6,
#     "MIN_ZOOM": 3,
#     "MAX_ZOOM": 18,
#     "SCALE": "both",
#     "RESET_VIEW": True,
# }
#
# INSTALLED_APPS = [
#     "modeltranslation",
#     "django.contrib.gis",
#     "leaflet",
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "rest_framework",
#     "rest_framework_simplejwt",
#     "django_filters",
#     "drf_spectacular",
#     "django_extensions",
#     "django_otp",
#     "django_otp.plugins.otp_totp",
#     "axes",
#     "allauth",
#     "allauth.account",
#     "django_celery_beat",
#     "django_ratelimit",
#     "storages",
#     "simple_history",
#     "utils",
#     "users",
#     "listings.apps.ListingsConfig",
#     "bookings",
#     "reviews",
#     "analytics",
#     "locations",
# ]
#
# AUTHENTICATION_BACKENDS = [
#     "axes.backends.AxesStandaloneBackend",
#     "django.contrib.auth.backends.ModelBackend",
# ]
#
# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.locale.LocaleMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     'django.middleware.csrf.CsrfViewMiddleware',
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
#     "allauth.account.middleware.AccountMiddleware",
#     "axes.middleware.AxesMiddleware",
#     "django_ratelimit.middleware.RatelimitMiddleware",
#     "core.middleware.MetaResponseMiddleware",
#     # 'sentry_sdk.integrations.django.middleware.DjangoMiddleware',
# ]
#
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "file": {
#             "level": "ERROR",
#             "class": "logging.FileHandler",
#             "filename": BASE_DIR / "logs/error.log",
#         },
#         "sentry": {
#             "level": "ERROR",
#             "class": "sentry_sdk.integrations.logging.SentryHandler",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["file", "sentry"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#     },
# }
#
# ROOT_URLCONF = "core.urls"
# AUTH_USER_MODEL = "users.User"
#
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],  # Убедитесь, что templates в корне проекта
#         'APP_DIRS': True,  # Автоматический поиск шаблонов в папках приложений (core/templates/)
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 'django.template.context_processors.i18n',  # Для мультиязычности
#             ],
#         },
#     },
# ]
#
# WSGI_APPLICATION = "core.wsgi.application"
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.contrib.gis.db.backends.mysql",
#         "NAME": config("DB_NAME"),
#         "USER": config("DB_USER"),
#         "PASSWORD": config("DB_PASSWORD"),
#         "HOST": config("DB_HOST"),
#         "PORT": config("DB_PORT"),
#         "OPTIONS": {
#             "charset": "utf8mb4",
#             "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }
#
# # Настройки кэширования
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": config("REDIS_URL"),
#         "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
#     }
# }
#
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
#     },
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]
#
# PASSWORD_HASHERS = [
#     "django.contrib.auth.hashers.Argon2PasswordHasher",
#     "django.contrib.auth.hashers.PBKDF2PasswordHasher",
# ]
#
# LANGUAGE_CODE = "en-us"
# LANGUAGES = [("en", "English"), ("de", "Deutsch"), ("ru", "Русский")]
#
# MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
# MODELTRANSLATION_LANGUAGES = ["en", "de", "ru"]
# MODELTRANSLATION_AUTO_POPULATE = "all"
#
# LOCALE_PATHS = [BASE_DIR / "locale"]
# TIME_ZONE = "Europe/Berlin"
# USE_I18N = True
# USE_L10N = True
# USE_TZ = True
#
# DATE_FORMAT = "j F Y"  # для формата "10 July 2025"
# # или
# # DATE_FORMAT = 'd.m.Y'  # для формата "10.07.2025"
#
# STATIC_URL = "/static/"
# STATICFILES_DIRS = [
#     BASE_DIR / "static",
# ]
# STATIC_ROOT = BASE_DIR / "staticfiles"
#
#
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"
# # MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
#
# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         "rest_framework_simplejwt.authentication.JWTAuthentication",
#     ],
#     "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
#     "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
#     "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
#     "PAGE_SIZE": 10,
#     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
#     "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
#     "DEFAULT_THROTTLE_CLASSES": [
#         "rest_framework.throttling.AnonRateThrottle",
#         "rest_framework.throttling.UserRateThrottle",
#     ],
#     "DEFAULT_RENDERER_CLASSES": [
#         "utils.renderers.CustomRenderer",
#         "rest_framework.renderers.BrowsableAPIRenderer",  # Можно удалить в проде
#     ],
#     "DEFAULT_THROTTLE_RATES": {
#         "anon": "100/minute",
#         "user": "100/minute",
#     },
# }
#
# SPECTACULAR_SETTINGS = {
#     "TITLE": "MietSystem API",
#     "DESCRIPTION": "API for MietSystem rental platform",
#     "VERSION": "1.0.0",
#     "SERVE_INCLUDE_SCHEMA": True,
#     "SERVE_PUBLIC": True,  # Убедись, что схема публичная
# }
#
# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
#     "AUTH_HEADER_TYPES": ("Bearer",),
#     "AUTH_COOKIE": "access_token",
#     "AUTH_COOKIE_REFRESH": "refresh_token",
#     "AUTH_COOKIE_HTTP_ONLY": True,
#     "AUTH_COOKIE_SECURE": True,
#     "AUTH_COOKIE_SAMESITE": "Strict",
# }
#
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# EMAIL_HOST = config("EMAIL_HOST")
# EMAIL_PORT = config("EMAIL_PORT", cast=int)
# EMAIL_HOST_USER = config("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
#
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# ACCOUNT_EMAIL_REQUIRED = True
# FRONTEND_URL = config("FRONTEND_URL")
#
# CELERY_BROKER_URL = config("CELERY_BROKER_URL")
# CELERY_RESULT_BACKEND = config("REDIS_URL")
# CELERY_ACCEPT_CONTENT = ["json"]
# CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_SERIALIZER = "json"
# CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
#
# CELERY_BEAT_SCHEDULE = {
#     "update-popularity-every-hour": {
#         "task": "utils.tasks.update_popularity",
#         "schedule": 3600.0,
#     },
#     "cleanup-expired-tokens-every-day": {
#         "task": "users.tasks.cleanup_expired_tokens",
#         "schedule": 86400.0,  # 24 hours
#     },
#     "cleanup-old-bookings-every-day": {
#         "task": "bookings.tasks.cleanup_old_bookings",
#         "schedule": 86400.0,  # 24 hours
#     },
#     "cleanup-old-views-every-day": {
#         "task": "analytics.tasks.cleanup_old_views",
#         "schedule": 86400.0,
#     },
# }
#
# AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
# AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
# AWS_S3_REGION_NAME = "eu-central-1"
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
#
# SLACK_TOKEN = config('SLACK_TOKEN', default='')
#
# # Настройки django-axes для защиты от брутфорса
# AXES_ENABLED = True
# AXES_FAILURE_LIMIT = 5
# AXES_COOLOFF_TIME = timedelta(minutes=30)
# AXES_LOCK_OUT_AT_FAILURE = True
# AXES_LOCKOUT_TEMPLATE = 'core/lockout.html'  # Шаблон для страницы блокировки
#
# # Настройки django-ratelimit
# RATELIMIT_ENABLE = True
# RATELIMIT_RATE = '100/m'  # 100 запросов в минуту
# RATELIMIT_BLOCK = True
#
# SENTRY_DSN = config("SENTRY_DSN", default="")
# if SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration(), CeleryIntegration()],
#         traces_sample_rate=1.0,
#         send_default_pii=True,
#     )
#
# SESSION_COOKIE_NAME = "miet_sessionid"
# CSRF_COOKIE_NAME = "miet_csrftoken"
#
# # Гарантирует, что браузер не запомнит логин
# SESSION_COOKIE_SECURE = True  # Для HTTPS
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Сессия заканчивается при закрытии браузера
#
#
# ADMIN_SITE_HEADER = "MietSystem Admin"
# ADMIN_SITE_TITLE = "MietSystem"
# ADMIN_INDEX_TITLE = "Добро пожаловать в админ-панель MietSystem"
#
# SILENCED_SYSTEM_CHECKS = ["models.W036"]
#
# SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
#
# LOGIN_URL = "/admin/login/"
