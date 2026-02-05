import uuid

from random import choices

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import help_text


class SplitTest(models.Model):
    name = models.CharField(_("name"), max_length=50)
    slug = models.SlugField(_("slug"), max_length=50)
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, db_index=True, editable=False)
    is_active = models.BooleanField(default=False, db_index=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="split_tests",
        verbose_name=_("site"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    class Meta:
        verbose_name = _("split test")
        verbose_name_plural = _("split tests")

        constraints = (models.UniqueConstraint(fields=("site", "slug"), name="unique_site_slug"),)

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<SplitTest: id={self.id} name={self.name} slug={self.slug} uuid={self.uuid}>"

    def get_cohort(self, user):
        """Return a cohort of this SplitTest for the given user.

        If the user is authenticated, check to see if they have already been
        assigned to an active cohort. If not, assign them to one.
        """
        cohort = None
        if not self.is_active:
            return cohort

        if user.is_authenticated:
            cohort = (
                self.cohorts.filter(users=user, is_active=True)
                .order_by("assignments__assigned_at")
                .first()
            )

        if not cohort:
            cohort = self._assign_cohort(user=user)

        return cohort

    def _assign_cohort(self, user):
        """Assign a random active cohort of this SplitTest to the given user.

        If the user is authenticated, update the cohort's user list.
        """
        cohorts = self.cohorts.filter(is_active=True).order_by("-weight")
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


class Cohort(models.Model):
    split_test = models.ForeignKey(
        SplitTest,
        on_delete=models.CASCADE,
        related_name="cohorts",
        verbose_name=_("split test"),
    )
    name = models.CharField(_("name"), max_length=50)
    slug = models.SlugField(_("slug"), max_length=50)
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, db_index=True, editable=False)
    is_active = models.BooleanField(default=False, db_index=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="cohorts",
        through="Assignment",
        verbose_name=_("users"),
    )
    weight = models.PositiveSmallIntegerField(
        help_text=help_text.COHORT["weight"], validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    class Meta:
        verbose_name = _("cohort")
        verbose_name_plural = _("cohorts")

        constraints = (
            models.UniqueConstraint(fields=("split_test", "slug"), name="unique_split_test_slug"),
        )

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<Cohort: id={self.id} name={self.name} slug={self.slug} uuid={self.uuid}>"


class Assignment(models.Model):
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("cohort"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("user"),
    )
    assigned_at = models.DateTimeField(_("assigned at"), auto_now_add=True)

    class Meta:
        verbose_name = _("assignment")
        verbose_name_plural = _("assignments")

        constraints = (
            models.UniqueConstraint(fields=("cohort", "user"), name="unique_cohort_user"),
        )

    def __str__(self):
        return f"{self.cohort} - {self.user}"

    def __repr__(self):
        return f"<Assignment: id={self.id} cohort={self.cohort} user={self.user} assigned_at={self.assigned_at}>"
