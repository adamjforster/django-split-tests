from random import choices

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import Exists, Manager, OuterRef

from . import cache as cache_config


class SplitTestCacheManager(Manager):
    """A Manager for the SplitTest model which keeps caches of active
    split tests and cohorts in memory for performance reasons.
    """

    def update(self):
        """Update the caches of active split tests and cohorts UUIDs and slugs."""
        split_test_active_uuids = set()
        split_test_uuid_slug_map = {}
        cohort_active_uuids = set()
        cohort_uuid_slug_map = {}
        cohort_uuid_split_test_uuid_map = {}

        current_site = Site.objects.get_current()
        Cohort = self.model._meta.get_field("cohorts").related_model
        active_cohorts = Cohort.objects.filter(split_test_id=OuterRef("id"), is_active=True)
        split_tests = (
            self.get_queryset()
            # The `Exists` check is more performant than filtering on
            # `cohorts__is_active=True` and then later calling `distinct()`.
            .filter(Exists(active_cohorts), is_active=True, site=current_site)
            .values_list("id", "uuid", "slug")
        )
        split_test_ids = []
        for split_test_id, split_test_uuid, split_test_slug in split_tests:
            split_test_uuid = str(split_test_uuid)

            split_test_ids.append(split_test_id)
            split_test_active_uuids.add(split_test_uuid)
            split_test_uuid_slug_map[split_test_uuid] = split_test_slug

        if split_test_ids:
            cohorts = Cohort.objects.filter(
                split_test_id__in=split_test_ids, is_active=True
            ).values_list("uuid", "slug", "split_test__uuid")
            for cohort_uuid, cohort_slug, split_test_uuid in cohorts:
                cohort_uuid = str(cohort_uuid)
                split_test_uuid = str(split_test_uuid)

                cohort_active_uuids.add(cohort_uuid)
                cohort_uuid_slug_map[cohort_uuid] = cohort_slug
                cohort_uuid_split_test_uuid_map[cohort_uuid] = split_test_uuid

        cache.set(
            cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY,
            split_test_active_uuids,
            timeout=cache_config.NEVER,
        )
        cache.set(
            cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY,
            split_test_uuid_slug_map,
            timeout=cache_config.NEVER,
        )
        cache.set(
            cache_config.COHORT_ACTIVE_UUIDS_KEY,
            cohort_active_uuids,
            timeout=cache_config.NEVER,
        )
        cache.set(
            cache_config.COHORT_UUID_SLUG_MAP_KEY,
            cohort_uuid_slug_map,
            timeout=cache_config.NEVER,
        )
        cache.set(
            cache_config.COHORT_UUID_SPLIT_TEST_UUID_MAP_KEY,
            cohort_uuid_split_test_uuid_map,
            timeout=cache_config.NEVER,
        )

        return (
            split_test_active_uuids,
            split_test_uuid_slug_map,
            cohort_active_uuids,
            cohort_uuid_slug_map,
            cohort_uuid_split_test_uuid_map,
        )

    def split_test_active_uuids(self):
        """Return a set of UUIDs for all active SplitTests from the cache."""
        split_test_active_uuids = cache.get(cache_config.SPLIT_TEST_ACTIVE_UUIDS_KEY)
        if split_test_active_uuids is None:
            split_test_active_uuids, _, _, _, _ = self.update()
        return split_test_active_uuids

    def split_test_uuid_slug_map(self):
        """Return a dict mapping UUIDs to slugs for all active SplitTests from the cache."""
        split_test_uuid_slug_map = cache.get(cache_config.SPLIT_TEST_UUID_SLUG_MAP_KEY)
        if split_test_uuid_slug_map is None:
            _, split_test_uuid_slug_map, _, _, _ = self.update()
        return split_test_uuid_slug_map

    def cohort_active_uuids(self):
        """Return a set of UUIDs for all active Cohorts from the cache."""
        cohort_active_uuids = cache.get(cache_config.COHORT_ACTIVE_UUIDS_KEY)
        if cohort_active_uuids is None:
            _, _, cohort_active_uuids, _, _ = self.update()
        return cohort_active_uuids

    def cohort_uuid_slug_map(self):
        """Return a dict mapping UUIDs to slugs for all active Cohorts from the cache."""
        cohort_uuid_slug_map = cache.get(cache_config.COHORT_UUID_SLUG_MAP_KEY)
        if cohort_uuid_slug_map is None:
            _, _, _, cohort_uuid_slug_map, _ = self.update()
        return cohort_uuid_slug_map

    def cohort_uuid_split_test_uuid_map(self):
        """Return a dict mapping Cohort UUIDs to SplitTest UUIDs from the cache."""
        cohort_uuid_split_test_uuid_map = cache.get(
            cache_config.COHORT_UUID_SPLIT_TEST_UUID_MAP_KEY
        )
        if cohort_uuid_split_test_uuid_map is None:
            _, _, _, _, cohort_uuid_split_test_uuid_map = self.update()
        return cohort_uuid_split_test_uuid_map


class CohortManager(Manager):
    def get_for_user_and_split_test(self, user, split_test_uuid):
        """Return a cohort for the given user and split test UUID.

        If the user is authenticated, check to see if they have already been
        assigned to an active cohort. If not, assign them to one.
        """
        cohort = None

        if user.is_authenticated:
            cohort = (
                self.get_queryset()
                .filter(
                    is_active=True,
                    users=user,
                    split_test__uuid=split_test_uuid,
                    split_test__is_active=True,
                )
                .order_by("assignments__assigned_at")
                .first()
            )

        if not cohort:
            cohort = self._assign_cohort(user, split_test_uuid)

        return cohort

    def _assign_cohort(self, user, split_test_uuid):
        """Assign a random active cohort given user and split test UUID.

        If the user is authenticated, update the cohort's user list.
        """
        cohorts = list(
            self.get_queryset()
            .filter(is_active=True, split_test__uuid=split_test_uuid, split_test__is_active=True)
            .order_by("-weight")
        )
        if not cohorts:
            return None

        # Make a weighted random choice.
        weights = [c.weight for c in cohorts]
        try:
            cohort = choices(cohorts, weights)[0]
        except ValueError:
            # Handle the case where all cohorts have a weight of 0.
            return None

        if cohort and user.is_authenticated:
            # Use get_or_create to avoid an IntegrityError.
            cohort.assignments.get_or_create(user=user)

        return cohort
