"""
Base settings to build other settings files upon.
"""
import datetime
from pathlib import Path

import environ
import stream_chat
from celery.schedules import crontab
from inapppy import AppStoreValidator, GooglePlayVerifier

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# heymatch/
APPS_DIR = ROOT_DIR / "heymatch"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Asia/Seoul"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(ROOT_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_celery_beat",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "phonenumber_field",
    "phone_verify",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "colorfield",
    "fcm_django",
    "ordered_model",
    "django_admin_logs",
    "simple_history",
]

LOCAL_APPS = [
    # Your stuff: custom apps go here
    "heymatch.infra",
    "heymatch.apps.authen.apps.AuthAppConfig",
    "heymatch.apps.user.apps.UserAppConfig",
    "heymatch.apps.hotplace.apps.HotplaceAppConfig",
    "heymatch.apps.group.apps.GroupAppConfig",
    "heymatch.apps.match.apps.MatchAppConfig",
    "heymatch.apps.payment.apps.PaymentAppConfig",
    "heymatch.apps.celery.apps.CeleryAppConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "heymatch.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "user.User"
# # https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
# LOGIN_REDIRECT_URL = "users:redirect"
# # https://docs.djangoproject.com/en/dev/ref/settings/#login-url
# LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/staticfiles/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
# STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": [str(APPS_DIR / "templates")],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""Jin J""", "jin@hey-match.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

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
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "requestlogs_to_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "/tmp/requestlogs.log",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "requestlogs": {
            "level": "DEBUG",
            "handlers": [
                "console"
            ],  # if you want log into file, use "requestlogs_to_file"
            "propagate": False,
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    },
}

# Celery
# ------------------------------------------------------------------------------
if USE_TZ:
    # https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ["json"]
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = "json"
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = "json"
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERY_TASK_TIME_LIMIT = 5 * 60
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-soft-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERY_TASK_SOFT_TIME_LIMIT = 60
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#beat-scheduler
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    # Disable groups, matches, chat at the end of the day
    "end-of-the-day": {
        "task": "heymatch.apps.celery.tasks.end_of_the_day_task",
        "schedule": crontab(minute=0, hour=5),  # execute daily at 5 a.m
        "args": (),
    },
    # Process DeleteScheduledUsers
    "delete-scheduled-users": {
        "task": "heymatch.apps.celery.tasks.delete_scheduled_users",
        "schedule": crontab(minute=0, hour="*/1"),  # execute every hour
        "args": (),
    },
}

# django-allauth
# ------------------------------------------------------------------------------
# ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# # https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_AUTHENTICATION_METHOD = "username"
# # https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_EMAIL_REQUIRED = True
# # https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# # https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_ADAPTER = "heymatch.users.adapters.AccountAdapter"
# # https://django-allauth.readthedocs.io/en/latest/forms.html
# ACCOUNT_FORMS = {"signup": "heymatch.users.forms.UserSignupForm"}
# # https://django-allauth.readthedocs.io/en/latest/configuration.html
# SOCIALACCOUNT_ADAPTER = "heymatch.users.adapters.SocialAccountAdapter"
# # https://django-allauth.readthedocs.io/en/latest/forms.html
# SOCIALACCOUNT_FORMS = {"signup": "heymatch.users.forms.UserSocialSignupForm"}

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "dj_rest_auth.jwt_auth.JWTAuthentication",
        # REST API for mobile app does not need session
        # https://security.stackexchange.com/questions/231710/is-csrf-prevention-logic-required-for-api-that-is-consumed-only-by-mobile-app/231713#231713
        # "rest_framework.authentication.SessionAuthentication",
        # "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("heymatch.shared.renderers.JSONResponseRenderer",),
    "EXCEPTION_HANDLER": "heymatch.shared.renderers.custom_exception_handler",
    # "EXCEPTION_HANDLER": "requestlogs.views.exception_handler",
}

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/api/.*$"

# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Hey There API",
    "DESCRIPTION": "Documentation of API endpoints of Hey There",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SERVERS": [
        {"url": "http://127.0.0.1:8000", "description": "Local Development server"},
        {
            "url": "https://heymatch.188corporation.com",
            "description": "Production server",
        },
    ],
}
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
}
# Your stuff...
# ------------------------------------------------------------------------------

# django-phone-verify
# ------------------------------------------------------------------------------
PHONE_VERIFICATION = {
    "BACKEND": "phone_verify.backends.twilio.TwilioBackend",
    "OPTIONS": {
        "SID": env("TWILIO_SID"),
        "SECRET": env("TWILIO_SECRET"),
        "FROM": env("TWILIO_PHONE_NUMBER"),
        "SANDBOX_TOKEN": "123456",
    },
    "TOKEN_LENGTH": 6,
    "MESSAGE": "{app} 인증번호 [{security_code}]를 입력해주세요.",
    "APP_NAME": "HeyMatch",
    "SECURITY_CODE_EXPIRATION_TIME": 300,  # In seconds only
    "VERIFY_SECURITY_CODE_ONLY_ONCE": True,
    # If False, then a security code can be used multiple times for verification
}
PHONE_VERIFICATION_DEFAULT_PASSWORD = "heymatch@!188corp"

# dj-rest-auth
# ------------------------------------------------------------------------------
REST_USE_JWT = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGOUT_ON_GET = True
REST_AUTH_SERIALIZERS = {
    "LOGIN_SERIALIZER": "heymatch.apps.authen.api.serializers.UserLoginByPhoneNumberSerializer",
    "USER_DETAILS_SERIALIZER": "heymatch.apps.authen.api.serializers.UserDetailByPhoneNumberSerializer",
}
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "heymatch.apps.authen.api.serializers.UserRegisterByPhoneNumberSerializer",
}

# djangorestframework-simplejwt
# ------------------------------------------------------------------------------
# https://jpadilla.github.io/django-rest-framework-jwt/?#security
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(days=30 * 6),  # 6 months
}

# swagger and debug toolbar
# ------------------------------------------------------------------------------
ENABLE_DOCS = env.bool("ENABLE_DOCS", default=False)
ENABLE_DEBUG_TOOLBAR = env.bool("ENABLE_DEBUG_TOOLBAR", default=False)

# phonenumber
PHONENUMBER_DEFAULT_REGION = "KR"

# django-storages
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = "ap-northeast-2"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_GROUP_PHOTO_FOLDER = "group_photos"

# stream-django
STREAM_API_KEY = env("STREAM_API_KEY")
STREAM_API_SECRET = env("STREAM_API_SECRET")
STREAM_CHAT_CHANNEL_TYPE = env("STREAM_CHAT_CHANNEL_TYPE")
STREAM_CLIENT = stream_chat.StreamChat(
    api_key=STREAM_API_KEY, api_secret=STREAM_API_SECRET
)

# Firebase Cloud Messaging
# FIREBASE_APP = initialize_app()
# FCM_DJANGO_SETTINGS = {
#     "ONE_DEVICE_PER_USER": True,
#     "DELETE_INACTIVE_DEVICES": False,
#     "UPDATE_ON_DUPLICATE_REG_ID": True,
# }

# Inappy Validators
IS_INAPP_TESTING = env("IS_INAPP_TESTING")
GOOGLE_PLAY_VALIDATOR = GooglePlayVerifier(
    bundle_id=env("GOOGLE_PLAY_BUNDLE_ID"),
    play_console_credentials=env("GOOGLE_PLAY_CONSOLE_SA_PATH"),
)
APP_STORE_VALIDATOR = AppStoreValidator(
    bundle_id=env("APP_STORE_BUNDLE_ID"),
    sandbox=env("IS_INAPP_TESTING"),
    auto_retry_wrong_env_request=False,
)

# Simple History
SIMPLE_HISTORY_REVERT_DISABLED = True
