# Django settings file used to run tests and make migrations.


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "split_tests",
]
SECRET_KEY = "fake-key"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SITE_ID = 1
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
