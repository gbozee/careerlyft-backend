"""
Django settings for django_app project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import environ
import raven

env = environ.Env(DEBUG=(bool, False))  # set default values and casting
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "a8m7&irp9qcdn=8-_*ag)qu@+k8o!_)dn90esu(4e%jp-bz!*s"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    "django.contrib.sessions",
    "raven.contrib.django.raven_compat",
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    "payment_service",
    "paystack",
    "quickbooks",
    "ravepay",
    # 'channels',
]

MIDDLEWARE = [
    # "corsheaders.middleware.CorsMiddleware",
    # 'django.middleware.security.SecurityMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "payment_service.urls"
CORS_ORIGIN_ALLOW_ALL = True


WSGI_APPLICATION = "payment_service.wsgi.application"
ASGI_APPLICATION = "payment_service.routing.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(os.getenv("REDIS_HOST", "localhost"), 6379)]},
    }
}

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    "default": env.db("DATABASE_URL", default=""),
    # 'replica': env.db('REPLICA_DATABASE_URL', default='postgres://tuteria:punnisher@127.0.0.1:5435/tuteria')
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
AUTHENTICATION_SERVICE = os.getenv(
    "AUTHENTICATION_SERVICE", "http://localhost:8001/api-token-verify"
)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SUCCESS_URL = "redirect_func"
SUCCESS_URL = os.getenv("PAYSTACK_SUCCESS_URL", "http://www.google.com")
PAYSTACK_FAILED_URL = os.getenv("PAYSTACK_FAILED_URL", "http://www.facebook.com")
RAVEPAY_PUBLIC_KEY = os.getenv("RAVEPAY_PUBLIC_KEY", "")
RAVEPAY_SECRET_KEY = os.getenv("RAVEPAY_SECRET_KEY", "")

AUTH_ENDPOINT = os.getenv("AUTH_ENDPOINT", "http://localhost:8001")
QUICKBOOKS_REDIRECT_URL = os.getenv(
    "QUICKBOOKS_REDIRECT_URL", "http://localhost:8000/quickbooks/auth-response"
)

RAVEN_CONFIG = {
    "dsn": "https://d1e6ab4dff934882a398235e5dab42f8:394f5e453a2c47fb87d1a52d7c4a0f46@sentry.io/1255805"
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "WARNING", "handlers": ["sentry"]},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "sentry": {
            "level": "ERROR",  # To capture more than ERROR, change to WARNING, INFO, etc.
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
            "tags": {"custom-tag": "x"},
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "raven": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
        "sentry.errors": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

CURRENT_DOMAIN = os.getenv("CURRENT_DOMAIN", "https://payment.careerlyft.com")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "demo_key")

