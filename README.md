# Django Split Tests

> [!WARNING]
> This project is under initial development and is not yet ready for any use.

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/adamjforster/django-split-tests/main.svg)](https://results.pre-commit.ci/latest/github/adamjforster/django-split-tests/main)

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
```
