import pytest

from django.core.exceptions import ImproperlyConfigured

from split_tests.config import DEFAULTS, SETTINGS_NAME, get_app_settings


def _clear_setting(settings):
    if hasattr(settings, SETTINGS_NAME):
        delattr(settings, SETTINGS_NAME)


def test_get_app_settings_returns_defaults_when_unset(settings):
    """Return defaults when the app setting is not configured."""
    _clear_setting(settings)
    assert get_app_settings() == DEFAULTS


def test_get_app_settings_merges_overrides(settings):
    """Merge user overrides with defaults."""
    _clear_setting(settings)
    overrides = {"COOKIE_PREFIX": "dst-test:", "SESSION_KEY": "custom"}
    setattr(settings, SETTINGS_NAME, overrides)
    assert get_app_settings() == DEFAULTS | overrides


def test_get_app_settings_rejects_non_dict(settings):
    """Reject non-dict settings values."""
    setattr(settings, SETTINGS_NAME, ["not-a-dict"])
    with pytest.raises(ImproperlyConfigured):
        get_app_settings()
