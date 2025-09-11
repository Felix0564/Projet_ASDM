

from pathlib import Path
import os
import environ
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2v72_5dar8)sitov3q0yee4pf195xihvf!r26$8f&6$(ah=h&!"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = ["projet-asdm.onrender.com", ".onrender.com", "localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = ["https://projet-asdm.onrender.com", "https://*.onrender.com"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "app_principale",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    #"whitenoise.middleware.WhiteNoiseMiddleware",  # Ajoutez cette ligne
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "asdmbackend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "asdmbackend.wsgi.application"

# Database
DATABASES = {
    'default': dj_database_url.parse(env('DATABASE_URL')) 
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media (upload)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'app_principale.CustomUser'

# REST Framework configuration (si vous l'utilisez)
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}
# from pathlib import Path
# import os
# import environ
# import dj_database_url


# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
# env=environ.Env()
# environ.Env.read_env()
 
# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-2v72_5dar8)sitov3q0yee4pf195xihvf!r26$8f&6$(ah=h&!"

# # SECURITY WARNING: don't run with debug turned on in production!
# #DEBUG = True
# DEBUG = environ.Env.bool(env, "DEBUG", default=False)

# #ALLOWED_HOSTS = []

# ALLOWED_HOSTS = ["projet-asdm.onrender.com", ".onrender.com", "localhost", "127.0.0.1"]

# CSRF_TRUSTED_ORIGINS = ["https://projet-asdm.onrender.com", "https://*.onrender.com"]

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# # Application definition

# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "rest_framework",
#     "app_principale",
#     "django_filters",
    
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "asdmbackend.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
    
# ]

# WSGI_APPLICATION = "asdmbackend.wsgi.application"


# # Database
# # https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# # DATABASES = {
# #     "default": {
# #         "ENGINE": 'django.db.backends.postgresql',   #"django.db.backends.sqlite3",
# #         "NAME": 'asdm_db',#BASE_DIR / "db.sqlite3",
# #         "USER": 'asdm_db_user',
# #         "PASSWORD":'4y78hTHR8m2qtjenyYf6im4mbF8sdEqp',
# #         "HOST":'dpg-d30qu9l6ubrc73fbetug-a',
# #         "PORT":'5432',
# #     }
# # }
# DATABASES= {
#     'default': dj_database_url.parse(env('DATABASE_URL')) 
# }


# # Password validation
# # https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/5.2/topics/i18n/

# LANGUAGE_CODE = "en-us"

# TIME_ZONE = "UTC"

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/5.2/howto/static-files/

# STATIC_URL = "static/"
# # Media (upload)
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

# # Default primary key field type
# # https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# AUTH_USER_MODEL = 'app_principale.CustomUser'