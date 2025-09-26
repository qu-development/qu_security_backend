from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.models import Note


# Custom list filters
class AmountRangeFilter(admin.SimpleListFilter):
    """Filter notes by amount ranges"""

    title = _("Amount Range")
    parameter_name = "amount_range"

    def lookups(self, request, model_admin):
        return (
            ("positive", _("Income (> $0)")),
            ("negative", _("Expense (< $0)")),
            ("zero", _("Neutral (= $0)")),
            ("small_positive", _("Small Income ($0-$100)")),
            ("large_positive", _("Large Income (> $100)")),
            ("small_negative", _("Small Expense ($0 to -$100)")),
            ("large_negative", _("Large Expense (< -$100)")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "positive":
            return queryset.filter(amount__gt=0)
        elif value == "negative":
            return queryset.filter(amount__lt=0)
        elif value == "zero":
            return queryset.filter(amount=0)
        elif value == "small_positive":
            return queryset.filter(amount__gt=0, amount__lte=100)
        elif value == "large_positive":
            return queryset.filter(amount__gt=100)
        elif value == "small_negative":
            return queryset.filter(amount__lt=0, amount__gte=-100)
        elif value == "large_negative":
            return queryset.filter(amount__lt=-100)
        return queryset


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin interface for Note model"""

    list_display = [
        "name",
        "amount_display",
        "amount_type_display",
        "related_entities_display",
        "created_by",
        "created_at",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
        "created_by",
        AmountRangeFilter,
    ]

    search_fields = [
        "name",
        "description",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__email",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "amount_type",
        "is_income",
        "is_expense",
        "related_entities_count",
        "related_entities_summary",
    ]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "description", "amount", "is_active")},
        ),
        (
            _("Relations"),
            {
                "fields": (
                    "clients",
                    "properties",
                    "guards",
                    "services",
                    "shifts",
                    "weapons",
                    "type_of_services",
                    "viewed_by_ids",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Computed Fields"),
            {
                "fields": (
                    "amount_type",
                    "is_income",
                    "is_expense",
                    "related_entities_count",
                    "related_entities_summary",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    # Actions
    actions = [
        "activate_notes",
        "deactivate_notes",
        "duplicate_notes",
    ]

    @admin.display(description=_("Amount"), ordering="amount")
    def amount_display(self, obj):
        """Display amount with formatting and color coding"""
        if obj.amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
                obj.amount,
            )
        elif obj.amount < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">${:,.2f}</span>',
                obj.amount,
            )
        else:
            return format_html('<span style="color: gray;">${:,.2f}</span>', obj.amount)

    @admin.display(description=_("Type"))
    def amount_type_display(self, obj):
        """Display amount type with color coding"""
        if obj.is_income:
            return format_html(
                '<span style="color: green; font-weight: bold;">📈 {}</span>',
                obj.amount_type,
            )
        elif obj.is_expense:
            return format_html(
                '<span style="color: red; font-weight: bold;">📉 {}</span>',
                obj.amount_type,
            )
        else:
            return format_html(
                '<span style="color: gray;">⚖️ {}</span>', obj.amount_type
            )

    @admin.display(description=_("Relations"))
    def related_entities_display(self, obj):
        """Display count of related entities"""
        entities = obj.get_related_entities()
        if not entities:
            return format_html('<span style="color: gray;">No relations</span>')

        total_count = sum(len(ids) for ids in entities.values())
        if total_count == 0:
            return format_html('<span style="color: gray;">No relations</span>')

        # Show summary of relation types with counts
        summary_parts = []
        for relation_type, ids in entities.items():
            if ids:
                summary_parts.append(f"{relation_type}: {len(ids)}")

        summary_str = ", ".join(summary_parts[:3])
        if len(summary_parts) > 3:
            summary_str += f", +{len(summary_parts) - 3} more"

        return format_html(
            '<span title="{}">{} total relation{}</span>',
            summary_str,
            total_count,
            "s" if total_count != 1 else "",
        )

    @admin.display(description=_("Related Entities Count"))
    def related_entities_count(self, obj):
        """Count of related entities (read-only field)"""
        entities = obj.get_related_entities()
        return sum(len(ids) for ids in entities.values())

    @admin.display(description=_("Related Entities Summary"))
    def related_entities_summary(self, obj):
        """Summary of all related entities (read-only field)"""
        entities = obj.get_related_entities()
        if not entities:
            return _("No related entities")

        summary_lines = []
        for relation_type, ids in entities.items():
            if ids:
                summary_lines.append(
                    f"• {relation_type.replace('_', ' ').title()}: {len(ids)} item(s) - IDs: {ids}"
                )

        return format_html("<br>".join(summary_lines))

    # Custom actions
    @admin.action(description=_("Activate selected notes"))
    def activate_notes(self, request, queryset):
        """Activate selected notes"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{count} note(s) were successfully activated.",
        )

    @admin.action(description=_("Deactivate selected notes"))
    def deactivate_notes(self, request, queryset):
        """Deactivate selected notes"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{count} note(s) were successfully deactivated.",
        )

    @admin.action(description=_("Duplicate selected notes"))
    def duplicate_notes(self, request, queryset):
        """Duplicate selected notes"""
        duplicated_count = 0
        for note in queryset:
            Note.objects.create(
                name=f"{note.name} (Copy)",
                description=note.description,
                amount=note.amount,
                clients=note.clients.copy() if note.clients else [],
                properties=note.properties.copy() if note.properties else [],
                guards=note.guards.copy() if note.guards else [],
                services=note.services.copy() if note.services else [],
                shifts=note.shifts.copy() if note.shifts else [],
                weapons=note.weapons.copy() if note.weapons else [],
                type_of_services=note.type_of_services.copy()
                if note.type_of_services
                else [],
                viewed_by_ids=[],  # Reset viewed_by for duplicated note
                created_by=request.user,  # Set the current user as creator
            )
            duplicated_count += 1

        self.message_user(
            request,
            f"{duplicated_count} note(s) were successfully duplicated.",
        )
