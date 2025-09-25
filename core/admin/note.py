from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin interface for Note model"""

    list_display = [
        "name",
        "amount_display",
        "amount_type_display",
        "related_entities_display",
        "created_at",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
        "client",
        "property_obj",
        "guard",
        "service",
    ]

    search_fields = [
        "name",
        "description",
        "client__user__username",
        "client__user__email",
        "property_obj__name",
        "property_obj__address",
        "guard__user__username",
        "guard__user__email",
        "service__name",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
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
                    "client",
                    "property_obj",
                    "guard",
                    "service",
                    "shift",
                    "expense",
                    "weapon",
                    "guard_property_tariff",
                    "property_type_of_service",
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
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
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

        count = len(entities)
        entities_str = ", ".join([entity["type"].title() for entity in entities[:3]])
        if len(entities) > 3:
            entities_str += f", +{len(entities) - 3} more"

        return format_html(
            '<span title="{}">{} relation{}</span>',
            entities_str,
            count,
            "s" if count != 1 else "",
        )

    @admin.display(description=_("Related Entities Count"))
    def related_entities_count(self, obj):
        """Count of related entities (read-only field)"""
        return len(obj.get_related_entities())

    @admin.display(description=_("Related Entities Summary"))
    def related_entities_summary(self, obj):
        """Summary of all related entities (read-only field)"""
        entities = obj.get_related_entities()
        if not entities:
            return _("No related entities")

        summary_lines = []
        for entity in entities:
            summary_lines.append(f"• {entity['type'].title()}: {entity['str']}")

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
                client=note.client,
                property_obj=note.property_obj,
                guard=note.guard,
                service=note.service,
                shift=note.shift,
                expense=note.expense,
                weapon=note.weapon,
                guard_property_tariff=note.guard_property_tariff,
                property_type_of_service=note.property_type_of_service,
            )
            duplicated_count += 1

        self.message_user(
            request,
            f"{duplicated_count} note(s) were successfully duplicated.",
        )

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
