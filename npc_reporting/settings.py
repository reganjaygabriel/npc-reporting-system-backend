import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.getenv('RENDER_EXTERNAL_HOSTNAME'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    # 'rest_framework_simplejwt',  # Temporarily disabled due to pkg_resources issue
    'corsheaders',
    'django_celery_beat',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',  # Add at top for caching
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # DISABLED FOR DEVELOPMENT
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reports.middleware.AuditLoggingMiddleware',
    'reports.middleware.SecurityAuditMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Add at bottom for caching
]

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'npc'

ROOT_URLCONF = 'npc_reporting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'npc_reporting.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'NPC_REPORTING_SYSTEM'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '2002'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
    }
}

# Uncomment below for SQLite testing
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Performance Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'npc-reporting-cache',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
    'api_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'npc-api-cache',
        'TIMEOUT': 600,  # 10 minutes for API responses
        'OPTIONS': {
            'MAX_ENTRIES': 500,
        }
    }
}

# Cache sessions for better performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File Upload Settings
# Maximum size for file uploads (25MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25MB in bytes

# For larger files, consider increasing these limits
# 50MB: 52428800
# 100MB: 104857600
# Note: Larger files will consume more memory and processing time

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,  # Reduced for better performance
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',  # Temporarily disabled due to import error
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour',  # Increased from 100 to 10000
        'user': '100000/hour'  # Increased from 1000 to 100000 for unlimited target changes
    }
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# AGGRESSIVE CORS SETTINGS - ALLOW EVERYTHING FOR DEVELOPMENT
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_PREFLIGHT_MAX_AGE = 86400
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
    'cache-control',
    'pragma',
    'expires',
    'x-requested-at',
    'access-control-allow-origin',
    'access-control-allow-credentials',
    'access-control-allow-headers',
    'access-control-allow-methods',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Additional CORS settings
CORS_URLS_REGEX = r'^/api/.*$'

# Frontend URL for email links
SITE_URL = "http://localhost:3000"

# Session Cookie Settings for Cross-Origin Requests
SESSION_COOKIE_SAMESITE = None  # Allow cross-origin cookies
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_AGE = 86400  # 24 hours
CSRF_COOKIE_SAMESITE = None
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

# Allow cache-busting headers
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
    'cache-control',
    'pragma',
    'expires',
]

MAX_UPLOAD_SIZE = 10485760  # 10MB

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@npc-reporting.com')

# Custom Exception Handler
REST_FRAMEWORK['EXCEPTION_HANDLER'] = 'reports.error_handlers.custom_exception_handler'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'reports': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ============================================================================
# SIGNATURE SECURITY SETTINGS
# ============================================================================

# Cryptographic Keys for Signature Security
# IMPORTANT: Change these in production and keep them secret!
SIGNATURE_SECRET_KEY = os.getenv('SIGNATURE_SECRET_KEY', SECRET_KEY)

# Generate encryption key: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
SIGNATURE_ENCRYPTION_KEY = os.getenv(
    'SIGNATURE_ENCRYPTION_KEY',
    'gAAAAABl_default_key_change_in_production_12345678901234567890='
)

# 2FA Settings
SIGNATURE_2FA_ENABLED = os.getenv('SIGNATURE_2FA_ENABLED', 'True') == 'True'
SIGNATURE_OTP_VALIDITY_MINUTES = int(os.getenv('SIGNATURE_OTP_VALIDITY_MINUTES', '5'))
SIGNATURE_MAX_OTP_ATTEMPTS = int(os.getenv('SIGNATURE_MAX_OTP_ATTEMPTS', '3'))

# Rate Limiting
SIGNATURE_RATE_LIMIT_HOUR = int(os.getenv('SIGNATURE_RATE_LIMIT_HOUR', '10'))
SIGNATURE_RATE_LIMIT_DAY = int(os.getenv('SIGNATURE_RATE_LIMIT_DAY', '50'))

# Audit Settings
SIGNATURE_AUDIT_RETENTION_DAYS = int(os.getenv('SIGNATURE_AUDIT_RETENTION_DAYS', '2555'))  # 7 years
SIGNATURE_LOG_GEOLOCATION = os.getenv('SIGNATURE_LOG_GEOLOCATION', 'False') == 'True'

# Security Features
SIGNATURE_ENABLE_ENCRYPTION = os.getenv('SIGNATURE_ENABLE_ENCRYPTION', 'True') == 'True'
SIGNATURE_ENABLE_VERIFICATION_HASH = os.getenv('SIGNATURE_ENABLE_VERIFICATION_HASH', 'True') == 'True'
SIGNATURE_REQUIRE_DEVICE_FINGERPRINT = os.getenv('SIGNATURE_REQUIRE_DEVICE_FINGERPRINT', 'True') == 'True'

# Notification Settings
SIGNATURE_NOTIFY_ON_SIGNATURE = os.getenv('SIGNATURE_NOTIFY_ON_SIGNATURE', 'True') == 'True'
SIGNATURE_NOTIFY_ON_SUSPICIOUS = os.getenv('SIGNATURE_NOTIFY_ON_SUSPICIOUS', 'True') == 'True'

# Add signature audit logger
LOGGING['loggers']['signature_audit'] = {
    'handlers': ['file'],
    'level': 'INFO',
    'propagate': False,
}
