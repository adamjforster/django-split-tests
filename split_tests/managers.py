from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import Exists, Manager, OuterRef, Prefetch

from .cache import NEVER, SPLIT_TEST_COHORT_MAP_KEY, UUID_COHORT_MAP


class SplitTestCacheManager(Manager):
    """A Manager for the SplitTest model which keeps caches of active
    SplitTest instances and their active Cohort instances.
    """

    def update(self):
        """Update the cached maps of active split tests and cohorts."""
        split_test_cohort_map = {}
        uuid_cohort_map = {}

        current_site = Site.objects.get_current()
        Cohort = self.model._meta.get_field("cohorts").related_model
        active_cohorts = Cohort.objects.filter(split_test_id=OuterRef("id"), is_active=True)
        split_tests = (
            self.get_queryset()
            # The `Exists` check is more performant than filtering on
            # `cohorts__is_active=True` and then later calling `distinct()`.
            .filter(Exists(active_cohorts), is_active=True, site=current_site)
            .prefetch_related(Prefetch("cohorts", queryset=Cohort.objects.filter(is_active=True)))
        )
        for split_test in split_tests:
            cohorts = set(split_test.cohorts.all())
            uuid_cohort_map.update({cohort.uuid: cohort for cohort in cohorts})
            split_test_cohort_map[split_test] = cohorts

        cache.set(SPLIT_TEST_COHORT_MAP_KEY, split_test_cohort_map, timeout=NEVER)
        cache.set(UUID_COHORT_MAP, uuid_cohort_map, timeout=NEVER)

        return split_test_cohort_map, uuid_cohort_map

    def split_test_cohort_map(self):
        """Return a dict of active SplitTest instances and their active Cohort
        instances from the cache.

        {split_test: {cohort, cohort, ...}}
        """
        split_test_cohort_map = cache.get(SPLIT_TEST_COHORT_MAP_KEY)
        if split_test_cohort_map is None:
            split_test_cohort_map, _ = self.update()
        return split_test_cohort_map

    def uuid_cohort_map(self):
        """Return a dict of UUIDs and Cohort instances for all active Cohorts
        from the cache.

        {uuid: cohort}
        """
        uuid_cohort_map = cache.get(UUID_COHORT_MAP)
        if uuid_cohort_map is None:
            _, uuid_cohort_map = self.update()
        return uuid_cohort_map
