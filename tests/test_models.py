import pytest

from django.contrib.sites.models import Site
from django.core.cache import cache

from split_tests import cache as cache_config
from split_tests.models import Cohort, SplitTest


@pytest.mark.django_db
def test_split_test_save_refreshes_cache():
    """Test that SplitTest.save triggers a cache refresh."""
    split_test = SplitTest.objects.create(
        name="Test One",
        slug="test-one",
        site=Site.objects.get_current(),
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Cohort One",
        slug="cohort-one",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY) is None
    assert cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY) is None
    assert cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY) is None
    assert cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY) is None

    split_test.save()

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) in split_test_active_uuids
    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert str(cohort.uuid) in cohort_active_uuids
    assert cohort_uuid_slug_map[str(cohort.uuid)] == cohort.slug


@pytest.mark.django_db
def test_split_test_delete_refreshes_cache():
    """Test that SplitTest.delete triggers a cache refresh."""
    split_test = SplitTest.objects.create(
        name="Test One",
        slug="test-one",
        site=Site.objects.get_current(),
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Cohort One",
        slug="cohort-one",
        weight=1,
        is_active=True,
    )

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) in split_test_active_uuids
    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert str(cohort.uuid) in cohort_active_uuids
    assert cohort_uuid_slug_map[str(cohort.uuid)] == cohort.slug

    split_test.delete()

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) not in split_test_active_uuids
    assert str(split_test.uuid) not in split_test_uuid_slug_map
    assert str(cohort.uuid) not in cohort_active_uuids
    assert str(cohort.uuid) not in cohort_uuid_slug_map


@pytest.mark.django_db
def test_cohort_save_refreshes_cache():
    """Test that Cohort.save triggers a cache refresh."""
    split_test = SplitTest.objects.create(
        name="Test One",
        slug="test-one",
        site=Site.objects.get_current(),
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Cohort One",
        slug="cohort-one",
        weight=1,
        is_active=True,
    )

    cache.clear()
    assert cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY) is None
    assert cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY) is None
    assert cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY) is None
    assert cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY) is None

    cohort.save()

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) in split_test_active_uuids
    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert str(cohort.uuid) in cohort_active_uuids
    assert cohort_uuid_slug_map[str(cohort.uuid)] == cohort.slug


@pytest.mark.django_db
def test_cohort_delete_refreshes_cache():
    """Test that Cohort.delete triggers a cache refresh."""
    split_test = SplitTest.objects.create(
        name="Test One",
        slug="test-one",
        site=Site.objects.get_current(),
        is_active=True,
    )
    cohort = Cohort.objects.create(
        split_test=split_test,
        name="Cohort One",
        slug="cohort-one",
        weight=1,
        is_active=True,
    )

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) in split_test_active_uuids
    assert split_test_uuid_slug_map[str(split_test.uuid)] == split_test.slug
    assert str(cohort.uuid) in cohort_active_uuids
    assert cohort_uuid_slug_map[str(cohort.uuid)] == cohort.slug

    cohort.delete()

    split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
    split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
    cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
    cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
    assert str(split_test.uuid) not in split_test_active_uuids
    assert str(split_test.uuid) not in split_test_uuid_slug_map
    assert str(cohort.uuid) not in cohort_active_uuids
    assert str(cohort.uuid) not in cohort_uuid_slug_map
