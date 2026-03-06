"""
OpportuCI - Test Settings
==========================
Utilise SQLite pour les tests sans PostgreSQL
"""
from .base import *

# Database - SQLite pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Accélérer les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactiver le cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Désactiver le debug
DEBUG = False

# Désactiver les logs excessifs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}
