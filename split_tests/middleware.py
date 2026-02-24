from .config import get_app_settings
from .models import Cohort, SplitTest


class SplitTestMiddleware:
    """A middleware class to manage split test and cohort assignments for all
    users.
    """

    def __init__(self, get_response):
        app_settings = get_app_settings()
        self.cookie_domain = app_settings["COOKIE_DOMAIN"]
        self.cookie_httponly = app_settings["COOKIE_HTTPONLY"]
        self.cookie_max_age = app_settings["COOKIE_MAX_AGE"]
        self.cookie_prefix = app_settings["COOKIE_PREFIX"]
        self.cookie_samesite = app_settings["COOKIE_SAMESITE"]
        self.cookie_secure = app_settings["COOKIE_SECURE"]
        self.session_key = app_settings["SESSION_KEY"]

        self.get_response = get_response

    def __call__(self, request):
        self.split_test_active_uuids = SplitTest.cache.split_test_active_uuids()
        self.split_test_uuid_slug_map = SplitTest.cache.split_test_uuid_slug_map()
        self.cohort_active_uuids = SplitTest.cache.cohort_active_uuids()
        self.cohort_uuid_slug_map = SplitTest.cache.cohort_uuid_slug_map()
        self.cohort_uuid_split_test_uuid_map = SplitTest.cache.cohort_uuid_split_test_uuid_map()

        self.check_cohort_assignments(request)

        response = self.get_response(request)

        self.update_split_test_cookies(request, response)

        return response

    def check_cohort_assignments(self, request):
        """Check if the current user (authenticated or not) is assigned to an
        active cohort for each active split test and ensure they are set in the
        current session.
        """
        # Ensure that the split tests session key exists.
        if self.session_key not in request.session:
            request.session[self.session_key] = {}

        self.remove_inactive_split_tests_from_session(request)

        # Ensure that the session has an active cohort set for each active
        # split test.
        for split_test_uuid in self.split_test_active_uuids:
            # Skip split tests that already have an active cohort assigned.
            if (
                split_test_uuid in request.session[self.session_key]
                and request.session[self.session_key][split_test_uuid] in self.cohort_active_uuids
            ):
                continue

            cohort_uuid = self.get_cohort_uuid_from_cookie(request, split_test_uuid)

            # Get an active cohort UUID for the user from the current split test. If
            # the user is authenticated, this will check the database for an
            # active assignment, otherwise it will assign them a new one.
            if not cohort_uuid:
                cohort = Cohort.objects.get_for_user_and_split_test(request.user, split_test_uuid)
                if cohort:
                    cohort_uuid = str(cohort.uuid)

            # Set the new cohort in the session.
            if cohort_uuid:
                request.session[self.session_key][split_test_uuid] = cohort_uuid
                request.session.modified = True

        self.update_user_split_test_cohort_slug_map(request)

    def remove_inactive_split_tests_from_session(self, request):
        """Remove inactive split test UUIDs from the current session."""
        # We need two loops as you can't alter a dict's size whilst iterating
        # over it.
        keys_to_delete = set()
        for split_test_uuid in request.session[self.session_key].keys():
            if split_test_uuid not in self.split_test_active_uuids:
                keys_to_delete.add(split_test_uuid)

        for split_test_uuid in keys_to_delete:
            del request.session[self.session_key][split_test_uuid]
            request.session.modified = True

    def get_cohort_uuid_from_cookie(self, request, split_test_uuid):
        """Return the UUID of the active cohort assigned to the user for the
        given split test UUID.
        """
        cookie_key = f"{self.cookie_prefix}{split_test_uuid}"
        if cookie_key in request.COOKIES:
            cohort_uuid = request.COOKIES[cookie_key]
            # Ensure that the cohort is still active and belongs to split test.
            if (
                cohort_uuid in self.cohort_active_uuids
                and self.cohort_uuid_split_test_uuid_map.get(cohort_uuid) == split_test_uuid
            ):
                return cohort_uuid
        return None

    def update_user_split_test_cohort_slug_map(self, request):
        """Update the current session's user object with a map of split test
        and cohort slugs.

        This map allows us to check the user's cohort assignments via their
        slugs rather than looping the cached object maps.
        """
        slug_map = {}

        split_tests_assignments = request.session[self.session_key]
        for split_test_uuid, cohort_uuid in split_tests_assignments.items():
            try:
                slug_map[self.split_test_uuid_slug_map[split_test_uuid]] = (
                    self.cohort_uuid_slug_map[cohort_uuid]
                )
            except KeyError:
                continue

        request.user.split_test_slug_map = slug_map

    def update_split_test_cookies(self, request, response):
        """Set cookies to track the user's cohort assignment for each split
        test.
        """
        if self.session_key not in request.session:
            return

        # Delete existing cohort cookies to ensure any stale assignments are
        # removed.
        for cookie_key in request.COOKIES:
            if cookie_key.startswith(self.cookie_prefix):
                response.delete_cookie(
                    cookie_key,
                    domain=self.cookie_domain,
                    samesite=self.cookie_samesite,
                )

        # Set cookies for split test cohort assignments.
        for split_test, cohort in request.session[self.session_key].items():
            cookie_key = f"{self.cookie_prefix}{split_test}"
            response.set_cookie(
                cookie_key,
                value=str(cohort),
                max_age=self.cookie_max_age,
                domain=self.cookie_domain,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )
