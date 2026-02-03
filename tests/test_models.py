import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site

from split_tests.models import Cohort, SplitTest


User = get_user_model()


@pytest.fixture
def setup():
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
        name="Cohort One",
        slug="cohort-two",
        weight=1,
        is_active=True,
    )

    return user, split_test, cohort_one, cohort_two


@pytest.mark.django_db
def test_get_cohort_with_new_assignment_for_authenticated_user(setup):
    """Test that `get_cohort` tracks the new cohort assignment for an
    authenticated user without an existing cohort.
    """
    user, split_test, cohort_one, cohort_two = setup
    assert user.is_authenticated

    # Ensure that cohort_two is returned.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort == cohort_two

    # Ensure that cohort_two was assigned to the user.
    assert Cohort.objects.get(users=user, split_test=split_test, is_active=True) == cohort_two


@pytest.mark.django_db
def test_get_cohort_with_existing_active_assignment_for_authenticated_user(setup):
    """Test that `get_cohort` returns the previously assigned cohort for an
    authenticated user with an existing active cohort.
    """
    user, split_test, cohort_one, cohort_two = setup
    assert user.is_authenticated

    # Assign the user to cohort_one.
    cohort_one.users.add(user)

    # Ensure that cohort_one is returned.
    assert split_test.get_cohort(user) == cohort_one


@pytest.mark.django_db
def test_get_cohort_with_existing_inactive_assignment_for_authenticated_user(setup):
    """Test that `get_cohort` tracks the new cohort assignment for an
    authenticated user with an existing inactive cohort.
    """
    user, split_test, cohort_one, cohort_two = setup
    assert user.is_authenticated

    # Assign the user to cohort_one.
    cohort_one.users.add(user)

    # Deactivate cohort_one.
    cohort_one.is_active = False
    cohort_one.save()

    # Ensure that cohort_two is returned, despite the assignment of the
    # inactive cohort_one.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort == cohort_two

    # Ensure that cohort_two was assigned to the user.
    assert Cohort.objects.get(users=user, split_test=split_test, is_active=True) == cohort_two


@pytest.mark.django_db
def test_get_cohort_with_multiple_active_cohorts_for_an_authenticated_user(setup):
    """Test that `get_cohort` returns the first assigned active cohort when an
    authenticated user has been assigned multiple active cohorts for a split
    test.

    This covers cases where a user's assigned cohort has been deactivated and
    then reactivated after they have been assigned to another cohort.
    """
    user, split_test, cohort_one, cohort_two = setup
    assert user.is_authenticated

    # Assign the user to both cohorts.
    cohort_two.users.add(user)
    cohort_one.users.add(user)

    # Ensure that the oldest assigned cohort is returned.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort == cohort_two


@pytest.mark.django_db
def test_get_cohort_for_unauthenticated_user(setup):
    """Test that `get_cohort` returns a cohort for an unauthenticated user and
    does not track the assignment.
    """
    _, split_test, cohort_one, cohort_two = setup

    user = AnonymousUser()
    assert not user.is_authenticated

    # Ensure that cohort_two is returned.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort == cohort_two

    # Ensure that the cohorts user assignment was not changed.
    assert cohort_two.users.count() == 0


@pytest.mark.django_db
def test_get_cohort_with_inactive_split_test(setup):
    """Test that `get_cohort` returns None for an inactive split test."""
    user, split_test, cohort_one, cohort_two = setup

    # Deactivate the split test.
    split_test.is_active = False
    split_test.save()

    # Ensure that inactive split tests don't return a cohort.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort is None


@pytest.mark.django_db
def test_get_cohort_with_no_active_cohorts(setup):
    """Test that `get_cohort` returns None for a split test with no active
    cohorts.
    """
    user, split_test, cohort_one, cohort_two = setup

    # Deactivate both cohorts.
    cohort_one.is_active = False
    cohort_one.save()
    cohort_two.is_active = False
    cohort_two.save()

    # Ensure that inactive cohorts are not returned.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort is None


@pytest.mark.django_db
def test_get_cohort_with_only_zero_weight_cohorts(setup):
    """Test that `get_cohort` returns None for a split test with only cohorts
    with weights of 0.
    """
    user, split_test, cohort_one, cohort_two = setup

    # Deactivate both cohorts.
    cohort_one.weight = 0
    cohort_one.save()
    cohort_two.weight = 0
    cohort_two.save()

    # Ensure that inactive cohorts are not returned.
    selected_cohort = split_test.get_cohort(user)
    assert selected_cohort is None
