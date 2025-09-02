# API Ordering Reference

Ordering is enabled globally via Django REST Framework’s `OrderingFilter` in `qu_security/settings.py` under `REST_FRAMEWORK.DEFAULT_FILTER_BACKENDS`.

- Query param: `ordering`
  - Ascending: `?ordering=field`
  - Descending: `?ordering=-field`
- Base API path (i18n): `/<lang>/api/...` (e.g., `/en/api/...`, `/es/api/...`). See `qu_security/urls.py`.
- Default ordering comes from each viewset’s `queryset.order_by(...)`.
- If a viewset does not declare `ordering_fields`, DRF allows ordering by any readable serializer fields (per DRF docs). Prefer model-backed fields; read-only nested "details" fields are not suitable for ordering.

---

## Users
- Path: `/<lang>/api/users/`
- ViewSet: `core/api/users.py::UserViewSet`
- Allowed ordering fields (declared): `id`, `username`, `first_name`, `last_name`, `email`, `date_joined`
- Default ordering: `-date_joined`
- Example: `/en/api/users/?ordering=last_name`

## Clients
- Path: `/<lang>/api/clients/`
- ViewSet: `core/api/clients.py::ClientViewSet`
- Allowed ordering fields (declared): `id`, `user__first_name`, `user__last_name`, `user__username`, `user__email`, `phone`, `balance`
- Default ordering: `id`
- Example: `/en/api/clients/?ordering=-balance`

## Guards
- Path: `/<lang>/api/guards/`
- ViewSet: `core/api/guards.py::GuardViewSet`
- Allowed ordering fields (declared): `id`, `user__first_name`, `user__last_name`, `user__username`, `user__email`, `phone`
- Default ordering: `id`
- Example: `/en/api/guards/?ordering=user__first_name`

## Properties
- Path: `/<lang>/api/properties/`
- ViewSet: `core/api/properties.py::PropertyViewSet`
- Allowed ordering fields (declared): `id`, `name`, `alias`, `contract_start_date`
- Default ordering: `id`
- Example: `/en/api/properties/?ordering=-contract_start_date`

## Expenses
- Path: `/<lang>/api/expenses/`
- ViewSet: `core/api/expenses.py::ExpenseViewSet`
- Serializer: `core/serializers/expenses.py::ExpenseSerializer`
- Allowed ordering fields (derived from serializer): `id`, `property`, `description`, `amount`
  - Note: `property_details` is read-only/nested; not suitable for ordering
- Default ordering: `-id`
- Example: `/en/api/expenses/?ordering=amount`

## Shifts
- Path: `/<lang>/api/shifts/`
- ViewSet: `core/api/shifts.py::ShiftViewSet`
- Serializer: `core/serializers/shifts.py::ShiftSerializer`
- Allowed ordering fields (derived): `id`, `guard`, `property`, `start_time`, `end_time`, `hours_worked`, `status`
- Default ordering: `-start_time`
- Example: `/en/api/shifts/?ordering=-end_time`

## Property Types of Service
- Path: `/<lang>/api/property-types-of-service/`
- ViewSet: `core/api/property_types.py::PropertyTypeOfServiceViewSet`
- Serializer: `core/serializers/property_types.py::PropertyTypeOfServiceSerializer`
- Allowed ordering fields (derived): `id`, `name`
- Default ordering: `name`
- Example: `/en/api/property-types-of-service/?ordering=-name`

## Guard-Property Tariffs
- Path: `/<lang>/api/guard-property-tariffs/`
- ViewSet: `core/api/tariffs.py::GuardPropertyTariffViewSet`
- Serializer: `core/serializers/tariffs.py::GuardPropertyTariffSerializer`
- Allowed ordering fields (derived): `id`, `guard`, `property`, `rate`, `is_active`, `created_at`, `updated_at`
- Default ordering: `-id`
- Example: `/en/api/guard-property-tariffs/?ordering=rate`

---

## Notes
- Nested ordering like `user__first_name` is supported only where explicitly listed (e.g., `clients`, `guards`).
- Custom list-like actions (e.g., `by_property`, `by_guard` in some viewsets) return lists but do not apply DRF filter backends automatically; the `ordering` query param may not affect those responses. They will use the viewset’s default `order_by(...)`. Sort client-side if needed.
- Global configuration reference: `qu_security/settings.py` → `REST_FRAMEWORK.DEFAULT_FILTER_BACKENDS` includes `rest_framework.filters.OrderingFilter`.
