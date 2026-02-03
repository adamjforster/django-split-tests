# Django settings file used to run tests and make migrations.


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
    "django.contrib.sites",
    "split_tests",
]
SITE_ID = 1
SECRET_KEY = "fake-key"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
