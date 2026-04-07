"""
Django settings for livocare project.
"""

from pathlib import Path
from datetime import timedelta
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 🔐 الإعدادات الأساسية
# ==============================================================================

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-...')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.8.187',
    '.onrender.com',
    '.railway.app',
    'livocare.onrender.com',
]

# ==============================================================================
# 📦 التطبيقات المثبتة (مبسطة)
# ==============================================================================

INSTALLED_APPS = [
    'django_extensions',
    'sslserver',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'analytics',
    'whitenoise.runserver_nostatic',
    'webpush',
]
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "BHlznz8R_5JWZ7C-JtA-kV60tNuqOU4vdW55C9p8iIhU6hJIHiJSH3SpkvYT_0HB81yj_P2Wv0IT5mG_YNmjf4E",
    "VAPID_PRIVATE_KEY": "_QIay_MCjUoCV8S_WPD6uSUuB9F-AMLpkNc445jDTxA",
    "VAPID_ADMIN_EMAIL": "rin31426@gmail.com"
}
# ==============================================================================
# 🛡️ Middleware (مبسطة)
# ==============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'livocare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'livocare.wsgi.application'

# ==============================================================================
# 🗄️ قاعدة البيانات
# ==============================================================================

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================================================================
# 🔐 المصادقة
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 🌐 اللغة والوقت
# ==============================================================================

LANGUAGE_CODE = 'ar-eg'
TIME_ZONE = 'Asia/Aden'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 📁 الملفات الثابتة والإعلامية
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# 🔑 الإعدادات الأساسية
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'main.CustomUser'

# ==============================================================================
# 🚀 REST Framework و JWT
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "ALGORITHM": "HS256",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ==============================================================================
# 🔗 CORS
# ==============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.8.187:8000",
    "https://livocare-fronend.onrender.com",
    "https://camera-service-fag3.onrender.com",
    "https://google-auth.onrender.com",  # ✅ أضف خدمة Google Auth
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.onrender\.com$",
    r"^https://.*\.railway\.app$",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG

CSRF_TRUSTED_ORIGINS = [
    "https://livocare-fronend.onrender.com",
    "https://camera-service-fag3.onrender.com",
    "https://google-auth.onrender.com",  # ✅ أضف خدمة Google Auth
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.8.187:8000",
    "https://*.onrender.com",
    "https://*.railway.app",
]

# ==============================================================================
# 🔒 إعدادات الأمان للإنتاج
# ==============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# 🆕 APIs الخارجية
# ==============================================================================

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')
OPENFOODFACTS_ENABLED = True
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')