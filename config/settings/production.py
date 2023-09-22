from .base import *  # noqa
from .base import env

# import sentry_sdk
# from sentry_sdk.integrations.celery import CeleryIntegration
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.logging import LoggingIntegration

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*.hey-match.com"])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"] = env.db("DATABASE_URL")  # noqa F405
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"  # noqa F405
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += [  # noqa F405
    "django_extensions",
    "drf_yasg",
]

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "heymatch.shared.renderers.ErrorHandlerMiddleware",
    "drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware",
]

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
# DEFAULT_FROM_EMAIL = env(
#     "DJANGO_DEFAULT_FROM_EMAIL",
#     default="Hey There <noreply@188corporation.com>",
# )
# # https://docs.djangoproject.com/en/dev/ref/settings/#server-email
# SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# # https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
# EMAIL_SUBJECT_PREFIX = env(
#     "DJANGO_EMAIL_SUBJECT_PREFIX",
#     default="[Hey There]",
# )

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Anymail
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
# INSTALLED_APPS += ["anymail"]  # noqa F405
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
# https://anymail.readthedocs.io/en/stable/esps/amazon_ses/
# EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"
# ANYMAIL = {}

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s (%(levelname)s) %(filename)s|%(funcName)s|%(process)d|%(thread)d] "
            "Message: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "to_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "/tmp/log/heymatch/django.log",
            "interval": 1,
            "when": "midnight",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["to_file"]},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["to_file"],
            "propagate": False,
        },
        # Errors logged by the SDK itself
        "sentry_sdk": {"level": "ERROR", "handlers": ["to_file"], "propagate": False},
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["to_file"],
            "propagate": False,
        },
    },
}

# Sentry
# ------------------------------------------------------------------------------
# SENTRY_DSN = env("SENTRY_DSN")
# SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)
#
# sentry_logging = LoggingIntegration(
#     level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
#     event_level=logging.ERROR,  # Send errors as events
# )
# integrations = [
#     sentry_logging,
#     DjangoIntegration(),
#     CeleryIntegration(),
#     # RedisIntegration(),
# ]
# sentry_sdk.init(
#     dsn=SENTRY_DSN,
#     integrations=integrations,
#     environment=env("SENTRY_ENVIRONMENT", default="production"),
#     traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=1.0),
#     # If you wish to associate users to errors (assuming you are using
#     # django.contrib.auth) you may enable sending PII data.
#     send_default_pii=True,
# )

# Celery
# ------------------------------------------------------------------------------
CELERY_BEAT_SCHEDULE["aggregate-business-report"] = {  # noqa F405
    "task": "heymatch.apps.celery.tasks.aggregate_business_report",
    "schedule": crontab(minute=0, hour=7),  # noqa F405
    "args": (),
}

# Your stuff...
# ------------------------------------------------------------------------------

# DRF-API-Logger
# ------------------------------------------------------------------------------
DRF_API_LOGGER_DATABASE = True  # Default to False
DRF_LOGGER_QUEUE_MAX_SIZE = 50  # Default to 50 if not specified.
DRF_LOGGER_INTERVAL = 10  # In Seconds, Default to 10 seconds if not specified.
