import pytest

from django.contrib.sites.models import Site
from django.core.cache import cache

from split_tests.cache import SPLIT_TEST_COHORT_MAP_KEY, UUID_COHORT_MAP
from split_tests.models import Cohort, SplitTest


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

    split_test_cohort_map, uuid_cohort_map = SplitTest.cache.update()

    assert inactive_split_test not in split_test_cohort_map
    assert active_cohort.uuid not in uuid_cohort_map


@pytest.mark.django_db
def test_cache_manager_update_excludes_other_sites_split_tests():
    """Test that split tests, and their cohorts, from other sites are excluded
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

    split_test_cohort_map, uuid_cohort_map = SplitTest.cache.update()

    assert split_test not in split_test_cohort_map
    assert cohort.uuid not in uuid_cohort_map


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

    split_test_cohort_map, uuid_cohort_map = SplitTest.cache.update()

    assert split_test not in split_test_cohort_map
    assert uuid_cohort_map == {}


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

    split_test_cohort_map, uuid_cohort_map = SplitTest.cache.update()

    assert split_test not in split_test_cohort_map
    assert uuid_cohort_map == {}


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

    split_test_cohort_map, uuid_cohort_map = SplitTest.cache.update()

    assert split_test_cohort_map[split_test] == {active_cohort_one, active_cohort_two}
    assert set(uuid_cohort_map.keys()) == {active_cohort_one.uuid, active_cohort_two.uuid}


@pytest.mark.django_db
def test_split_test_cohort_map_populates_empty_cache():
    """Test that split_test_cohort_map populates the cache when it misses."""
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
    assert cache.get(SPLIT_TEST_COHORT_MAP_KEY) is None

    split_test_cohort_map = SplitTest.cache.split_test_cohort_map()

    assert split_test in split_test_cohort_map
    assert split_test_cohort_map[split_test] == {cohort}
    assert cache.get(SPLIT_TEST_COHORT_MAP_KEY) == split_test_cohort_map


@pytest.mark.django_db
def test_uuid_cohort_map_populates_empty_cache():
    """Test that uuid_cohort_map populates the cache when it misses."""
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
    assert cache.get(UUID_COHORT_MAP) is None

    uuid_cohort_map = SplitTest.cache.uuid_cohort_map()

    assert uuid_cohort_map[cohort.uuid] == cohort
    assert cache.get(UUID_COHORT_MAP) == uuid_cohort_map


@pytest.mark.django_db
def test_split_test_cohort_map_returns_cached_value():
    """Test that split_test_cohort_map returns the cached value without
    recomputing.
    """
    cached_map = {"split_test": {"cohort"}}
    cache.set(SPLIT_TEST_COHORT_MAP_KEY, cached_map)

    split_test_cohort_map = SplitTest.cache.split_test_cohort_map()

    assert split_test_cohort_map == cached_map
    assert cache.get(SPLIT_TEST_COHORT_MAP_KEY) == cached_map


@pytest.mark.django_db
def test_uuid_cohort_map_returns_cached_value():
    """Test that uuid_cohort_map returns the cached value without
    recomputing.
    """
    cached_map = {"uuid": "cohort"}
    cache.set(UUID_COHORT_MAP, cached_map)

    uuid_cohort_map = SplitTest.cache.uuid_cohort_map()

    assert uuid_cohort_map == cached_map
    assert cache.get(UUID_COHORT_MAP) == cached_map
