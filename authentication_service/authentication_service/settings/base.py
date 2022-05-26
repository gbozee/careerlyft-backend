"""
Django settings for authentication_service project.

Generated by 'django-admin startproject' using Django 2.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
from typing import List, Set, Dict, Tuple, Optional, Union
import os
import raven
import environ
import datetime

root = environ.Path(__file__) - 3  # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False))  # set default values and casting
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "rol&5bcu%vdqn(^q9np!t$ykto_qib8aan775im+%ko^%nczne"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: List[str] = []

# Application definition

INSTALLED_APPS: List[str] = [
    # 'django.contrib.admin',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "raven.contrib.django.raven_compat",
    #     'django.contrib.messages',
    #     'django.contrib.staticfiles',
    "authentication_service",
]

MIDDLEWARE = [
    # "corsheaders.middleware.CorsMiddleware",
    # 'django.middleware.security.SecurityMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # "authenticaton_service.middleware.SetLastVisitMiddleware"
]

ROOT_URLCONF = "authentication_service.urls"

TEMPLATES: List[Dict[str, Union[str, List[str], bool]]] = [
    # {
    #     'BACKEND': 'django.template.backends.django.DjangoTemplates',
    #     'DIRS': [],
    #     'APP_DIRS': True,
    #     'OPTIONS': {
    #         'context_processors': [
    #             'django.template.context_processors.debug',
    #             'django.template.context_processors.request',
    #             'django.contrib.auth.context_processors.auth',
    #             'django.contrib.messages.context_processors.messages',
    #         ],
    #     },
    # },
]

WSGI_APPLICATION = "authentication_service.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    "default":
    env.db(
        "DATABASE_URL",
        default="postgres://tuteria:punnisher@127.0.0.1:5435/careerlyft")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

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

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES":
    ("rest_framework.permissions.IsAuthenticated", ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
}
JWT_ALLOW_REFRESH = True
LAST_ACTIVITY_INTERVAL_SECS = 3600
AUTH_USER_MODEL = "authentication_service.User"

JWT_AUTH = {
    "JWT_RESPONSE_PAYLOAD_HANDLER":
    "authentication_service.utils.jwt_response_payload_handler",
    "JWT_AUTH_HEADER_PREFIX":
    "Token",
    "JWT_EXPIRATION_DELTA":
    datetime.timedelta(days=2),
    "JWT_GET_USER_SECRET_KEY":
    lambda user: user.password_hash + SECRET_KEY,
}
CLIENT_URL = os.getenv("CLIENT_URL", "https://app.careerlyft.com")
AGENT_URL = os.getenv('AGENT_URL', 'https://agent.careerlyft.com')
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "demo_key")
CLIENT_PASSWORD_URL = os.getenv("CLIENT_PASSWORD_URL", "/reset-password")
CLIENT_WELCOME_PATH = os.getenv("CLIENT_WELCOME_PATH", "/account-dashboard")
CORS_ORIGIN_ALLOW_ALL = True
CV_SERVICE_URL = os.getenv("CV_SERVICE_URL", "http://localhost:8000")
CV_SERVICE_DELETE_URL = f"{CV_SERVICE_URL}/v2/get-profile"
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8007")
PAYMENT_SERVICE_FREE_TEMPLATE_URL = f"{PAYMENT_SERVICE_URL}/create-free-template"

RAVEN_CONFIG = {
    "dsn":
    "https://ce321241fdd046f6970bc717ac212f83:9ab35cb4fe7e44a58fc88c7cd81fb8df@sentry.io/1255796",
    #  If  you  are  using  git,  you  can  also  automatically  configure  the
    #  release  based  on  the  git  info.
    # "release": raven.fetch_git_sha(os.path.abspath(os.pardir)),
}
BASE_URL = os.getenv("BASE_URL", "https://authentication.careerlyft.com")