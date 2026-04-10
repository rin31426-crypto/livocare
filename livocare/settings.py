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
    'livocare-fronend.onrender.com',
]

# ==============================================================================
# 🔔 خدمات خارجية مستقلة - الإشعارات
# ==============================================================================

# خدمة الإشعارات (Push Notifications)
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'https://notification-service-2xej.onrender.com')

# خدمة البريد الإلكتروني
EMAIL_SERVICE_URL = os.environ.get('EMAIL_SERVICE_URL', 'https://email-service-zc0r.onrender.com')

# ✅ إعدادات الإشعارات الداخلية
NOTIFICATION_SETTINGS = {
    'ENABLED': True,
    'CHECK_INTERVAL_MINUTES': 30,  # التحقق كل 30 دقيقة
    'MAX_NOTIFICATIONS_PER_USER': 50,  # الحد الأقصى للإشعارات لكل مستخدم
    'KEEP_DAYS': 30,  # الاحتفاظ بالإشعارات لمدة 30 يوم
    'PUSH_ENABLED': True,  # تفعيل Push Notifications
    'EMAIL_ENABLED': True,  # تفعيل الإيميلات
    'DAILY_TIP_ENABLED': True,  # تفعيل النصائح اليومية
    'ACHIEVEMENT_ENABLED': True,  # تفعيل إشعارات الإنجازات
}

# ==============================================================================
# 📦 التطبيقات المثبتة
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
]

# ==============================================================================
# 🛡️ Middleware
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
# 🚀 REST Framework و JWT (تعديل قسم التحديد)
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # ✅ إضافة تحديد معدل الطلبات لمنع الـ 429
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '2000/day',      # زيادة للزوار غير المسجلين
        'user': '5000/day',      # زيادة للمستخدمين المسجلين
        'notifications': '1000/hour',  # زيادة للإشعارات
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ==============================================================================
# 🔗 CORS - إضافة خدمات جديدة (تعديل)
# ==============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.8.187:8000",
    "https://livocare-fronend.onrender.com",
    "https://camera-service-fag3.onrender.com",
    "https://google-auth.onrender.com",
    "https://notification-service-2xej.onrender.com",
    "https://email-service-zc0r.onrender.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.onrender\.com$",
    r"^https://.*\.railway\.app$",
]

CORS_ALLOW_CREDENTIALS = True
# ⚠️ في الإنتاج، يفضل تعيين هذا إلى False واستخدام CORS_ALLOWED_ORIGINS فقط
CORS_ALLOW_ALL_ORIGINS = True  # مؤقتاً للتجربة

CSRF_TRUSTED_ORIGINS = [
    "https://livocare-fronend.onrender.com",
    "https://camera-service-fag3.onrender.com",
    "https://google-auth.onrender.com",
    "https://notification-service-2xej.onrender.com",
    "https://email-service-zc0r.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.8.187:8000",
    "https://*.onrender.com",
    "https://*.railway.app",
]

# ✅ إضافات CORS للطلبات المتكررة
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ==============================================================================
# 🔔 إعدادات الإشعارات الإضافية (إضافة)
# ==============================================================================

# VAPID keys لـ Web Push (للإشعارات الفورية)
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_ADMIN_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'admin@livocare.com')

# ✅ إعدادات التنبيهات الصحية
HEALTH_ALERTS = {
    'weight': {
        'min': 50,
        'max': 100,
        'urgent_min': 40,
        'urgent_max': 120,
    },
    'systolic': {
        'min': 90,
        'max': 140,
        'urgent_min': 80,
        'urgent_max': 160,
    },
    'diastolic': {
        'min': 60,
        'max': 90,
        'urgent_min': 50,
        'urgent_max': 100,
    },
    'glucose': {
        'min': 70,
        'max': 140,
        'urgent_min': 60,
        'urgent_max': 180,
    },
}

# ✅ إعدادات توقيت الإشعارات
NOTIFICATION_TIMING = {
    'breakfast': {'hour': 8, 'minute': 0},
    'lunch': {'hour': 13, 'minute': 0},
    'dinner': {'hour': 19, 'minute': 0},
    'sleep_reminder': {'hour': 21, 'minute': 0},
    'activity_reminder': {'hour': 17, 'minute': 0},
    'daily_tip': {'hour': 10, 'minute': 0},
}

# ✅ إعدادات إضافية للإشعارات
NOTIFICATION_BATCH_SIZE = 50  # عدد الإشعارات المرسلة في الدفعة الواحدة
NOTIFICATION_RETRY_ATTEMPTS = 3  # عدد محاولات إعادة إرسال الإشعار الفاشل
NOTIFICATION_RETRY_DELAY = 60  # ثواني بين محاولات إعادة الإرسال
# ✅ إعدادات التنبيهات الصحية
HEALTH_ALERTS = {
    'weight': {
        'min': 50,
        'max': 100,
        'urgent_min': 40,
        'urgent_max': 120,
    },
    'systolic': {
        'min': 90,
        'max': 140,
        'urgent_min': 80,
        'urgent_max': 160,
    },
    'diastolic': {
        'min': 60,
        'max': 90,
        'urgent_min': 50,
        'urgent_max': 100,
    },
    'glucose': {
        'min': 70,
        'max': 140,
        'urgent_min': 60,
        'urgent_max': 180,
    },
}

# ✅ إعدادات توقيت الإشعارات
NOTIFICATION_TIMING = {
    'breakfast': {'hour': 8, 'minute': 0},
    'lunch': {'hour': 13, 'minute': 0},
    'dinner': {'hour': 19, 'minute': 0},
    'sleep_reminder': {'hour': 21, 'minute': 0},
    'activity_reminder': {'hour': 17, 'minute': 0},
    'daily_tip': {'hour': 10, 'minute': 0},
}