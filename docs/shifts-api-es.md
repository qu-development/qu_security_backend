# API de Turnos (Shifts)

Esta guía explica cómo interactuar con la API de turnos para asignar guardias a propiedades dentro de rangos de fecha y hora, consultar, actualizar y anular/restaurar turnos.

- Base path con i18n: `/<idioma>/api/`
  - Ejemplo en español: `/es/api/shifts/`
  - Ejemplo en inglés: `/en/api/shifts/`
- Autenticación: JWT Bearer (DRF SimpleJWT).
  - Incluye el encabezado: `Authorization: Bearer <token>`

## Modelo de datos
Un turno (`Shift`) contiene:
- `guard` (ID del guardia)
- `property` (ID de la propiedad)
- `start_time` (DateTime ISO 8601)
- `end_time` (DateTime ISO 8601, debe ser posterior a `start_time`)
- `status` (scheduled, completed, voided)
- `hours_worked` (entero; calculado automáticamente a partir de start/end)

Serializer: `core/serializers/shifts.py`.

## Endpoints principales
Recursos registrados en `core/urls.py` bajo `basename="shift"`.

- Listar (paginado):
  - GET `/shifts/`
- Crear:
  - POST `/shifts/`
- Detalle:
  - GET `/shifts/{id}/`
- Actualizar:
  - PUT `/shifts/{id}/`
  - PATCH `/shifts/{id}/`
- Eliminar (borrado real):
  - DELETE `/shifts/{id}/`

### Acciones personalizadas
- Suavemente eliminar (soft delete):
  - POST `/shifts/{id}/soft_delete/`
- Restaurar un turno eliminado lógicamente:
  - POST `/shifts/{id}/restore/`
- Filtrar por guardia:
  - GET `/shifts/by_guard/?guard_id={guard_id}`
- Filtrar por propiedad:
  - GET `/shifts/by_property/?property_id={property_id}`

## Permisos y visibilidad
- Autenticación requerida para todas las operaciones.
- Crear: permitido a usuarios autenticados (según la implementación actual de `ShiftViewSet`).
- Actualizar/Eliminar: restringido por `IsGuardAssigned` (el guardia asignado, managers o administradores).
- Visibilidad (listado/consulta):
  - Administradores/Managers: ven todos los turnos.
  - Guards: ven solo sus propios turnos.
  - Clients: ven turnos de sus propiedades.

Referencia: `permissions/utils.py::PermissionManager.filter_queryset_by_permissions` y `permissions/permissions.py`.

## Paginación, búsqueda y ordenamiento
- Paginación: `common.pagination.SettingsPageNumberPagination`.
  - Respuesta incluye: `count`, `next`, `previous`, `results`.
  - Parámetro opcional: `?page_size=...`.
- Búsqueda: habilitada por DRF SearchFilter, no hay `search_fields` definidos para shifts (sin efecto por ahora).
- Ordenamiento: DRF OrderingFilter.
  - Usar `?ordering=<campo>` o `?ordering=-<campo>`.
  - Campos típicos: `id`, `guard`, `property`, `start_time`, `end_time`, `hours_worked`, `status`.

## Soft delete y elementos inactivos
- Los listados devuelven por defecto solo registros activos (`is_active=True`).
- Para incluir registros inactivos (soft-deleted): usar `?include_inactive=true`.

## Validaciones clave
- `end_time` debe ser posterior a `start_time`.
- `hours_worked` se calcula automáticamente (entero, redondeo por piso de horas).

## Ejemplos

### Obtener token JWT
```bash
curl -X POST \
  "/es/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario",
    "password": "secreto"
  }'
```

### Crear un turno
```bash
curl -X POST \
  "/es/api/shifts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "guard": 12,
    "property": 34,
    "start_time": "2025-01-01T08:00:00Z",
    "end_time": "2025-01-01T16:00:00Z",
    "status": "scheduled"
  }'
```

### Listar turnos (paginado) y ordenar por inicio descendente
```bash
curl -X GET \
  "/es/api/shifts/?ordering=-start_time" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtrar por guardia
```bash
curl -X GET \
  "/es/api/shifts/by_guard/?guard_id=12" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtrar por propiedad
```bash
curl -X GET \
  "/es/api/shifts/by_property/?property_id=34" \
  -H "Authorization: Bearer $TOKEN"
```

### Actualizar estado del turno (PATCH)
```bash
curl -X PATCH \
  "/es/api/shifts/55/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

### Soft delete
```bash
curl -X POST \
  "/es/api/shifts/55/soft_delete/" \
  -H "Authorization: Bearer $TOKEN"
```

### Restaurar
```bash
curl -X POST \
  "/es/api/shifts/55/restore/" \
  -H "Authorization: Bearer $TOKEN"
```

## Notas
- Las rutas reales dependerán del prefijo de idioma (`/es/` o `/en/`).
- Fechas/horas deben estar en formato ISO 8601. El backend opera en zona horaria UTC (`USE_TZ=True`).
- En despliegues productivos, las políticas de quién puede crear turnos pueden endurecerse (e.g., solo dueños de la propiedad o guards con acceso). Revise `ShiftViewSet` y clases de permisos antes de cambios.
