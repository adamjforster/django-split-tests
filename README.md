# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/adamjforster/django-split-tests/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                     |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| split\_tests/\_\_init\_\_.py             |        0 |        0 |        0 |        0 |    100% |           |
| split\_tests/admin.py                    |       36 |       36 |        8 |        0 |      0% |     1-104 |
| split\_tests/apps.py                     |        5 |        0 |        0 |        0 |    100% |           |
| split\_tests/cache.py                    |        3 |        0 |        0 |        0 |    100% |           |
| split\_tests/help\_text.py               |        2 |        0 |        0 |        0 |    100% |           |
| split\_tests/managers.py                 |       29 |        0 |        6 |        0 |    100% |           |
| split\_tests/migrations/0001\_initial.py |        9 |        0 |        0 |        0 |    100% |           |
| split\_tests/migrations/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| split\_tests/models.py                   |       92 |        6 |       10 |        0 |     94% |40, 43, 134, 137, 173, 176 |
| **TOTAL**                                |  **176** |   **42** |   **24** |    **0** | **75%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/adamjforster/django-split-tests/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/adamjforster/django-split-tests/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/adamjforster/django-split-tests/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/adamjforster/django-split-tests/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fadamjforster%2Fdjango-split-tests%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/adamjforster/django-split-tests/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.