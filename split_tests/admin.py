from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cohort, SplitTest


class CohortInline(admin.TabularInline):
    model = Cohort

    extra = 1
    fields = (
        "name",
        "slug",
        "uuid",
        "is_active",
        "weight",
    )
    prepopulated_fields = {"slug": ("name",)}
    # Allow the form to show the `uuid` field despite it being `editable=False`.
    readonly_fields = ("uuid",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # Make `slug` read-only when editing an existing object.
            return self.readonly_fields + ("slug",)
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj:
            # Since `slug` is read-only when editing an existing object, we
            # need to remove it from the prepopulated fields to prevent a
            # KeyError.
            return {}
        else:
            return self.prepopulated_fields


@admin.register(SplitTest)
class SplitTestAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = (
        "id",
        "name",
        "slug",
        "uuid",
        "site",
        "is_active",
        "created_at",
        "modified_at",
    )
    list_filter = (
        "is_active",
        "site",
    )
    ordering = ("-created_at",)
    search_fields = (
        "name",
        "slug",
        "uuid",
    )

    fieldsets = (
        (
            _("Details"),
            {
                "fields": [
                    "name",
                    "slug",
                    "uuid",
                    "site",
                    "is_active",
                ],
            },
        ),
        (
            _("Meta data"),
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "modified_at"),
            },
        ),
    )
    inlines = (CohortInline,)
    prepopulated_fields = {"slug": ("name",)}
    # Force the inclusion of these fields in the form so they can be displayed.
    readonly_fields = ("id", "uuid", "created_at", "modified_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # Make `slug` and `site` read-only when editing an existing object.
            return self.readonly_fields + (
                "slug",
                "site",
            )
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj:
            # Since `slug` is read-only when editing an existing object, we
            # need to remove it from the prepopulated fields to prevent a
            # KeyError.
            return {}
        else:
            return self.prepopulated_fields
