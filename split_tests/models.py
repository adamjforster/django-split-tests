import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import help_text
from .managers import CohortManager, SplitTestCacheManager


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

    objects = models.Manager()
    cache = SplitTestCacheManager()

    class Meta:
        verbose_name = _("split test")
        verbose_name_plural = _("split tests")

        constraints = (models.UniqueConstraint(fields=("site", "slug"), name="unique_site_slug"),)

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<SplitTest: id={self.id} name={self.name} slug={self.slug} uuid={self.uuid}>"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        SplitTest.cache.update()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        SplitTest.cache.update()
        return result


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

    objects = CohortManager()

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        SplitTest.cache.update()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        SplitTest.cache.update()
        return result


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
