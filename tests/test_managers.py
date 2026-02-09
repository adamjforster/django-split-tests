import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core.cache import cache

from split_tests import cache as cache_config
from split_tests.models import Cohort, SplitTest


User = get_user_model()


@pytest.mark.django_db
def test_cache_manager_update_excludes_inactive_split_tests():
    """Test that inactive split tests and their cohorts are excluded from the
    cache.
    """
    current_site = Site.objects.get_current()
    inactive_split_test = SplitTest.objects.create(
        name="Inactive",
        slug="inactive",
        site=current_site,
        is_active=False,
    )
    active_cohort = Cohort.objects.create(
        split_test=inactive_split_test,
        name="Inactive Split Test Cohort",
        slug="inactive-split-test-cohort",
        weight=1,
        is_active=True,
    )

    split_test_active_uuids, split_test_uuid_slug_map, cohort_active_uuids, cohort_uuid_slug_map = (
        SplitTest.cache.update()
    )

    assert str(inactive_split_test.uuid) not in split_test_active_uuids
    assert str(inactive_split_test.uuid) not in split_test_uuid_slug_map
    assert str(active_cohort.uuid) not in cohort_active_uuids
    assert str(active_cohort.uuid) not in cohort_uuid_slug_map


@pytest.mark.django_db
def test_cache_manager_update_excludes_other_sites_split_tests():
    """Test that split tests and their cohorts from other sites are excluded
    from the cache.
    """
    other_site = Site.objects.create(domain="other.example.com", name="Other")
    split_test = SplitTest.objects.create(
        name="Other Site",
        slug="other-site",
        site=other_site,
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Other Site Cohort",
        slug="other-site-cohort",
        weight=1,
        is_active=True,
    )

    split_test_active_uuids, split_test_uuid_slug_map, cohort_active_uuids, cohort_uuid_slug_map = (
        SplitTest.cache.update()
    )

    assert str(split_test.uuid) not in split_test_active_uuids
    assert str(split_test.uuid) not in split_test_uuid_slug_map
    assert str(cohort.uuid) not in cohort_active_uuids
    assert str(cohort.uuid) not in cohort_uuid_slug_map


@pytest.mark.django_db
def test_cache_manager_update_excludes_split_tests_with_no_cohorts():
    """Test that split tests with no cohorts are excluded from the cache."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="No Active Cohorts",
        slug="no-active",
        site=current_site,
        is_active=True,
    )

    split_test_active_uuids, split_test_uuid_slug_map, cohort_active_uuids, cohort_uuid_slug_map = (
        SplitTest.cache.update()
    )

    assert str(split_test.uuid) not in split_test_active_uuids
    assert str(split_test.uuid) not in split_test_uuid_slug_map
    assert cohort_active_uuids == set()
    assert cohort_uuid_slug_map == {}


@pytest.mark.django_db
def test_cache_manager_update_excludes_split_tests_with_no_active_cohorts():
    """Test that split tests with no active cohorts are excluded from the
    cache.
    """
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="No Active Cohorts",
        slug="no-active",
        site=current_site,
        is_active=True,
    )
    Cohort.objects.create(
        split_test=split_test,
        name="No Active Cohort",
        slug="no-active-cohort",
        weight=1,
        is_active=False,
    )

    split_test_active_uuids, split_test_uuid_slug_map, cohort_active_uuids, cohort_uuid_slug_map = (
        SplitTest.cache.update()
    )

    assert str(split_test.uuid) not in split_test_active_uuids
    assert str(split_test.uuid) not in split_test_uuid_slug_map
    assert cohort_active_uuids == set()
    assert cohort_uuid_slug_map == {}


@pytest.mark.django_db
def test_cache_manager_update_includes_only_active_cohorts():
    """Test that only active cohorts are included in the cache."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Active",
        slug="active",
        site=current_site,
        is_active=True,
    )

    active_cohort_one = Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort One",
        slug="active-cohort-one",
        weight=1,
        is_active=True,
    )
    active_cohort_two = Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort Two",
        slug="active-cohort-two",
        weight=1,
        is_active=True,
    )
    Cohort.objects.create(
        split_test=split_test,
        name="Inactive Cohort",
        slug="inactive-cohort",
        weight=1,
        is_active=False,
    )

    split_test_active_uuids, split_test_uuid_slug_map, cohort_active_uuids, cohort_uuid_slug_map = (
        SplitTest.cache.update()
    )

    assert str(split_test.uuid) in split_test_active_uuids
    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert cohort_active_uuids == {str(active_cohort_one.uuid), str(active_cohort_two.uuid)}
    assert cohort_uuid_slug_map == {
        str(active_cohort_one.uuid): active_cohort_one.slug,
        str(active_cohort_two.uuid): active_cohort_two.slug,
    }


@pytest.mark.django_db
def test_split_test_active_uuids_populates_empty_cache():
    """Test that split_test_active_uuids populates the cache when it misses."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Active",
        slug="active",
        site=current_site,
        is_active=True,
    )
    Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort",
        slug="active-cohort",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY) is None

    split_test_active_uuids = SplitTest.cache.split_test_active_uuids()

    assert str(split_test.uuid) in split_test_active_uuids
    assert cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY) == split_test_active_uuids


@pytest.mark.django_db
def test_cohort_active_uuids_populates_empty_cache():
    """Test that cohort_active_uuids populates the cache when it misses."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Active",
        slug="active",
        site=current_site,
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort",
        slug="active-cohort",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY) is None

    cohort_active_uuids = SplitTest.cache.cohort_active_uuids()

    assert str(cohort.uuid) in cohort_active_uuids
    assert cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY) == cohort_active_uuids


@pytest.mark.django_db
def test_split_test_active_uuids_returns_cached_value():
    """Test that split_test_active_uuids returns the cached value without
    recomputing.
    """
    cached_uuids = {"split_test"}
    cache.set(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY, cached_uuids)

    split_test_active_uuids = SplitTest.cache.split_test_active_uuids()

    assert split_test_active_uuids == cached_uuids
    assert cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY) == cached_uuids


@pytest.mark.django_db
def test_cohort_active_uuids_returns_cached_value():
    """Test that cohort_active_uuids returns the cached value without
    recomputing.
    """
    cached_uuids = {"uuid"}
    cache.set(cache_config.COHORT_ACTIVE_UUIDS_KEY, cached_uuids)

    cohort_active_uuids = SplitTest.cache.cohort_active_uuids()

    assert cohort_active_uuids == cached_uuids
    assert cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY) == cached_uuids


@pytest.mark.django_db
def test_split_test_uuid_slug_map_populates_empty_cache():
    """Test that split_test_uuid_slug_map populates the cache when it misses."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Active",
        slug="active",
        site=current_site,
        is_active=True,
    )
    Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort",
        slug="active-cohort",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY) is None

    split_test_uuid_slug_map = SplitTest.cache.split_test_uuid_slug_map()

    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY) == split_test_uuid_slug_map


@pytest.mark.django_db
def test_split_test_uuid_slug_map_returns_cached_value():
    """Test that split_test_uuid_slug_map returns the cached value without
    recomputing.
    """
    cached_map = {"uuid": "slug"}
    cache.set(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY, cached_map)

    split_test_uuid_slug_map = SplitTest.cache.split_test_uuid_slug_map()

    assert split_test_uuid_slug_map == cached_map
    assert cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY) == cached_map


@pytest.mark.django_db
def test_cohort_uuid_slug_map_populates_empty_cache():
    """Test that cohort_uuid_slug_map populates the cache when it misses."""
    current_site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Active",
        slug="active",
        site=current_site,
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Active Cohort",
        slug="active-cohort",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY) is None

    cohort_uuid_slug_map = SplitTest.cache.cohort_uuid_slug_map()

    assert cohort_uuid_slug_map[str(cohort.uuid)] == cohort.slug
    assert cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY) == cohort_uuid_slug_map


@pytest.mark.django_db
def test_cohort_uuid_slug_map_returns_cached_value():
    """Test that cohort_uuid_slug_map returns the cached value without
    recomputing.
    """
    cached_map = {"uuid": "slug"}
    cache.set(cache_config.COHORT_UUID_SLUG_MAP_KEY, cached_map)

    cohort_uuid_slug_map = SplitTest.cache.cohort_uuid_slug_map()

    assert cohort_uuid_slug_map == cached_map
    assert cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY) == cached_map


@pytest.fixture
def setup_get_for_user_and_split_test_tests():
    user = User.objects.create_user(username="testuser", email="test@example.com")

    site = Site.objects.get_current()
    split_test = SplitTest.objects.create(
        name="Test One",
        slug="test-one",
        site=site,
        is_active=True,
    )

    # Create a cohort with a weight of 0 to ensure that it cannot be "randomly"
    # selected.
    cohort_one = Cohort.objects.create(
        split_test=split_test,
        name="Cohort One",
        slug="cohort-one",
        weight=0,
        is_active=True,
    )

    # Create a cohort with a weight of 1 to ensure that it is always "randomly"
    # selected.
    cohort_two = Cohort.objects.create(
        split_test=split_test,
        name="Cohort Two",
        slug="cohort-two",
        weight=1,
        is_active=True,
    )

    return user, split_test, cohort_one, cohort_two


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_new_assignment_for_authenticated_user(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` tracks the new cohort assignment
    for an authenticated user without an existing cohort.
    """
    user, split_test, _, cohort_two = setup_get_for_user_and_split_test_tests
    assert user.is_authenticated

    # Ensure that cohort_two is returned.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort == cohort_two

    # Ensure that cohort_two was assigned to the user.
    assert Cohort.objects.get(users=user, split_test=split_test, is_active=True) == cohort_two


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_existing_active_assignment_for_authenticated_user(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns the previously assigned
    cohort for an authenticated user with an existing active cohort.
    """
    user, split_test, cohort_one, _ = setup_get_for_user_and_split_test_tests
    assert user.is_authenticated

    # Assign the user to cohort_one.
    cohort_one.users.add(user)

    # Ensure that cohort_one is returned.
    assert Cohort.objects.get_for_user_and_split_test(user, split_test.uuid) == cohort_one


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_existing_inactive_assignment_for_authenticated_user(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` tracks the new cohort assignment
    for an authenticated user with an existing inactive cohort.
    """
    user, split_test, cohort_one, cohort_two = setup_get_for_user_and_split_test_tests
    assert user.is_authenticated

    # Assign the user to cohort_one.
    cohort_one.users.add(user)

    # Deactivate cohort_one.
    cohort_one.is_active = False
    cohort_one.save()

    # Ensure that cohort_two is returned, despite the assignment of the
    # inactive cohort_one.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort == cohort_two

    # Ensure that cohort_two was assigned to the user.
    assert Cohort.objects.get(users=user, split_test=split_test, is_active=True) == cohort_two


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_multiple_active_cohorts_for_an_authenticated_user(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns the first assigned active
    cohort when an authenticated user has been assigned multiple active cohorts
    for a split test.

    This covers cases where a user's assigned cohort has been deactivated and
    then reactivated after they have been assigned to another cohort.
    """
    user, split_test, cohort_one, cohort_two = setup_get_for_user_and_split_test_tests
    assert user.is_authenticated

    # Assign the user to both cohorts.
    cohort_two.users.add(user)
    cohort_one.users.add(user)

    # Ensure that the oldest assigned cohort is returned.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort == cohort_two


@pytest.mark.django_db
def test_get_for_user_and_split_test_for_unauthenticated_user(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns a cohort for an
    unauthenticated user and does not track the assignment.
    """
    _, split_test, _, cohort_two = setup_get_for_user_and_split_test_tests

    user = AnonymousUser()
    assert not user.is_authenticated

    # Ensure that cohort_two is returned.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort == cohort_two

    # Ensure that the cohorts user assignment was not changed.
    assert cohort_two.users.count() == 0


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_inactive_split_test(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns None for an inactive
    split test.
    """
    user, split_test, _, _ = setup_get_for_user_and_split_test_tests

    # Deactivate the split test.
    split_test.is_active = False
    split_test.save()

    # Ensure that inactive split tests don't return a cohort.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort is None


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_no_active_cohorts(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns None for a split test
    with no active cohorts.
    """
    user, split_test, cohort_one, cohort_two = setup_get_for_user_and_split_test_tests

    # Deactivate both cohorts.
    cohort_one.is_active = False
    cohort_one.save()
    cohort_two.is_active = False
    cohort_two.save()

    # Ensure that inactive cohorts are not returned.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort is None


@pytest.mark.django_db
def test_get_for_user_and_split_test_with_only_zero_weighted_cohorts(
    setup_get_for_user_and_split_test_tests,
):
    """Test that `get_for_user_and_split_test` returns None for a split test
    with only cohorts with weights of 0.
    """
    user, split_test, cohort_one, cohort_two = setup_get_for_user_and_split_test_tests

    cohort_one.weight = 0
    cohort_one.save()
    cohort_two.weight = 0
    cohort_two.save()

    # Ensure that zero-weighted cohorts are not returned.
    selected_cohort = Cohort.objects.get_for_user_and_split_test(user, split_test.uuid)
    assert selected_cohort is None
