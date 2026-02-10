from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


SETTINGS_NAME = "DJANGO_SPLIT_TESTS"


DEFAULTS = {
    "COOKIE_DOMAIN": None,
    "COOKIE_MAX_AGE": 31_536_000,  # 1 year in seconds.
    "COOKIE_PREFIX": "dst:",
    "COOKIE_SECURE": True,
    "COOKIE_HTTPONLY": False,
    "COOKIE_SAMESITE": "Lax",
    "SESSION_KEY": "split_tests",
}


def get_app_settings():
    """Return any user-defined settings merged with the app defaults."""
    value = getattr(settings, SETTINGS_NAME, None)
    if value is None:
        return DEFAULTS
    if not isinstance(value, dict):
        raise ImproperlyConfigured(f"{SETTINGS_NAME} must be a dictionary if it exists.")
    return DEFAULTS | value
