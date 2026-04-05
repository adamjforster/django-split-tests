# Django Split Tests

> [!WARNING]
> This project is under initial development and is not yet ready for any use.

[![pytest](https://github.com/adamjforster/django-split-tests/actions/workflows/pytest.yaml/badge.svg)](https://github.com/adamjforster/django-split-tests/actions/workflows/pytest.yaml)
[![Coverage badge](https://raw.githubusercontent.com/adamjforster/django-split-tests/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/adamjforster/django-split-tests/blob/python-coverage-comment-action-data/htmlcov/index.html)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/adamjforster/django-split-tests/main.svg)](https://results.pre-commit.ci/latest/github/adamjforster/django-split-tests/main)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/adamjforster/django-split-tests?utm_source=oss&utm_medium=github&utm_campaign=adamjforster%2Fdjango-split-tests&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

A Django app for managing split (A/B) tests.

## Setup

Update your settings.py with:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'split_tests',
]

SITE_ID = 1
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'split_tests.middleware.SplitTestMiddleware',  # Must come after AuthenticationMiddleware.
    # ...
]
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}
```
