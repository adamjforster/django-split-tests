import pytest

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.test import RequestFactory

from split_tests.middleware import SplitTestMiddleware
from split_tests.models import Cohort, SplitTest


@pytest.fixture
def split_test_factory():
    def _create(**kwargs):
        current_site = kwargs.pop("site", Site.objects.get_current())
        defaults = {
            "name": "Split Test",
            "slug": "split-test",
            "site": current_site,
            "is_active": True,
        }
        defaults.update(kwargs)
        return SplitTest.objects.create(**defaults)

    return _create


@pytest.fixture
def cohort_factory():
    def _create(split_test, **kwargs):
        defaults = {
            "name": "Cohort",
            "slug": "cohort",
            "weight": 1,
            "is_active": True,
            "split_test": split_test,
        }
        defaults.update(kwargs)
        return Cohort.objects.create(**defaults)

    return _create


def make_request():
    request = RequestFactory().get("/")
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


def make_middleware():
    return SplitTestMiddleware(lambda request: HttpResponse())


def set_cached_maps(middleware, split_tests, cohorts):
    middleware.split_test_active_uuids = {str(split_test.uuid) for split_test in split_tests}
    middleware.split_test_uuid_slug_map = {
        str(split_test.uuid): split_test.slug for split_test in split_tests
    }
    middleware.cohort_active_uuids = {str(cohort.uuid) for cohort in cohorts}
    middleware.cohort_uuid_slug_map = {str(cohort.uuid): cohort.slug for cohort in cohorts}
    middleware.cohort_uuid_split_test_uuid_map = {
        str(cohort.uuid): str(cohort.split_test.uuid) for cohort in cohorts
    }


def get_session_cohort_uuid(request, session_key, split_test_uuid):
    return str(request.session[session_key][str(split_test_uuid)])


@pytest.mark.django_db
def test_get_cohort_uuid_from_cookie_rejects_mismatched_split_test(
    split_test_factory, cohort_factory
):
    split_test_one = split_test_factory(name="Split Test One", slug="split-test-one")
    split_test_two = split_test_factory(name="Split Test Two", slug="split-test-two")
    cohort_factory(
        split_test_one,
        name="Cohort One",
        slug="cohort-one",
    )
    cohort_two = cohort_factory(
        split_test_two,
        name="Cohort Two",
        slug="cohort-two",
    )

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test_one, split_test_two], [cohort_two])
    request = make_request()
    cookie_key = f"{middleware.cookie_prefix}{split_test_one.uuid}"
    request.COOKIES[cookie_key] = str(cohort_two.uuid)

    assert middleware.get_cohort_uuid_from_cookie(request, str(split_test_one.uuid)) is None


@pytest.mark.django_db
def test_get_cohort_uuid_from_cookie_accepts_matching_split_test(
    split_test_factory, cohort_factory
):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test], [cohort])
    request = make_request()
    cookie_key = f"{middleware.cookie_prefix}{split_test.uuid}"
    request.COOKIES[cookie_key] = str(cohort.uuid)

    assert middleware.get_cohort_uuid_from_cookie(request, str(split_test.uuid)) == str(cohort.uuid)


@pytest.mark.django_db
def test_check_cohort_assignments_creates_session_key(split_test_factory, cohort_factory):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test], [cohort])
    request = make_request()

    middleware.check_cohort_assignments(request)

    assert middleware.session_key in request.session


@pytest.mark.django_db
def test_remove_inactive_split_tests_from_session_removes_inactive_uuid(
    split_test_factory,
):
    inactive_split_test = split_test_factory(
        name="Inactive Split Test",
        slug="inactive-split-test",
        is_active=False,
    )
    active_split_test = split_test_factory(
        name="Active Split Test",
        slug="active-split-test",
        is_active=True,
    )

    middleware = make_middleware()
    middleware.split_test_active_uuids = {str(active_split_test.uuid)}
    request = make_request()
    request.session[middleware.session_key] = {
        str(inactive_split_test.uuid): "stale",
        str(active_split_test.uuid): "active",
    }

    middleware.remove_inactive_split_tests_from_session(request)

    assert str(inactive_split_test.uuid) not in request.session[middleware.session_key]


@pytest.mark.django_db
def test_check_cohort_assignments_sets_session_from_cookie(split_test_factory, cohort_factory):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test], [cohort])
    request = make_request()
    cookie_key = f"{middleware.cookie_prefix}{split_test.uuid}"
    request.COOKIES[cookie_key] = str(cohort.uuid)

    middleware.check_cohort_assignments(request)

    assert get_session_cohort_uuid(request, middleware.session_key, split_test.uuid) == str(
        cohort.uuid
    )


@pytest.mark.django_db
def test_check_cohort_assignments_assigns_cohort_when_no_cookie(split_test_factory, cohort_factory):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test], [cohort])
    request = make_request()

    middleware.check_cohort_assignments(request)

    assert get_session_cohort_uuid(request, middleware.session_key, split_test.uuid) == str(
        cohort.uuid
    )


@pytest.mark.django_db
def test_update_user_split_test_cohort_slug_map_sets_slug_map(split_test_factory, cohort_factory):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    set_cached_maps(middleware, [split_test], [cohort])
    request = make_request()
    request.session[middleware.session_key] = {str(split_test.uuid): str(cohort.uuid)}

    middleware.update_user_split_test_cohort_slug_map(request)

    assert request.user.split_test_slug_map == {split_test.slug: cohort.slug}


def test_update_split_test_cookies_no_session_key_no_cookies_set():
    middleware = make_middleware()
    request = make_request()
    response = HttpResponse()

    middleware.update_split_test_cookies(request, response)

    assert len(response.cookies) == 0


@pytest.mark.django_db
def test_update_split_test_cookies_sets_cookie_for_assignment(split_test_factory, cohort_factory):
    split_test = split_test_factory()
    cohort = cohort_factory(split_test)

    middleware = make_middleware()
    request = make_request()
    request.session[middleware.session_key] = {str(split_test.uuid): str(cohort.uuid)}
    response = HttpResponse()

    middleware.update_split_test_cookies(request, response)

    cookie_key = f"{middleware.cookie_prefix}{split_test.uuid}"
    assert response.cookies[cookie_key].value == str(cohort.uuid)


def test_update_split_test_cookies_deletes_stale_cookie():
    middleware = make_middleware()
    request = make_request()
    request.session[middleware.session_key] = {}
    stale_key = f"{middleware.cookie_prefix}stale"
    request.COOKIES[stale_key] = "stale"
    response = HttpResponse()

    middleware.update_split_test_cookies(request, response)

    assert response.cookies[stale_key]["max-age"] == 0
