# Django Split Tests

> [!WARNING]
> This project is under initial development and is not yet ready for any use.

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
