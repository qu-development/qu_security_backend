# Bulk Operations API Documentation

## Overview

The QU Security backend provides comprehensive bulk operations functionality across all major entities (Guards, Services, Shifts, Properties, etc.) through a unified `BulkActionMixin` implementation.

## Features

- **Bulk Create**: Create multiple records in a single request
- **Bulk Delete**: Delete multiple records by IDs
- **Bulk Update**: Update multiple records with different values
- **Transaction Safety**: All bulk operations are atomic
- **Performance Optimized**: Efficient database queries with minimal round trips
- **Swagger Documentation**: Full API documentation with request/response schemas

## Available Endpoints

All ViewSets that inherit from `BulkActionMixin` support the following bulk operations:

### Bulk Create
- **Endpoint**: `POST /{entity}/bulk_create/`
- **Description**: Create multiple records in a single transaction
- **Request Body**: Array of objects to create
- **Response**: Array of created objects with generated IDs

### Bulk Delete
- **Endpoint**: `POST /{entity}/bulk_delete/`
- **Description**: Delete multiple records by their IDs
- **Request Body**: `{"ids": [1, 2, 3, ...]}`
- **Response**: Summary of deletion operation

### Bulk Update
- **Endpoint**: `POST /{entity}/bulk_update/`
- **Description**: Update multiple records with different values
- **Request Body**: Array of objects with IDs and updated fields
- **Response**: Array of updated objects

## Supported Entities

The following entities support bulk operations:

- Guards (`/guards/`)
- Services (`/services/`)
- Shifts (`/shifts/`)
- Properties (`/properties/`)
- Guard Reports (`/guard_reports/`)
- Mobile API endpoints

## Request/Response Examples

### Bulk Create Example
```json
POST /shifts/bulk_create/
{
  "objects": [
    {
      "guard": 1,
      "service": 1,
      "start_time": "2025-09-22T08:00:00Z",
      "end_time": "2025-09-22T16:00:00Z"
    },
    {
      "guard": 2,
      "service": 1,
      "start_time": "2025-09-22T16:00:00Z",
      "end_time": "2025-09-23T00:00:00Z"
    }
  ]
}
```

### Bulk Delete Example
```json
POST /shifts/bulk_delete/
{
  "ids": [1, 2, 3, 4, 5]
}
```

Response:
```json
{
  "message": "Successfully deleted 5 shifts",
  "deleted_count": 5
}
```

### Bulk Update Example
```json
POST /shifts/bulk_update/
{
  "objects": [
    {
      "id": 1,
      "status": "completed",
      "notes": "Shift completed successfully"
    },
    {
      "id": 2,
      "status": "cancelled",
      "notes": "Guard called in sick"
    }
  ]
}
```

## Performance Benefits

- **Database Optimization**: Uses `bulk_create()`, `bulk_update()`, and efficient filtering
- **Query Reduction**: Minimal database round trips
- **Transaction Safety**: All operations are wrapped in database transactions
- **Memory Efficiency**: Handles large datasets without memory issues

## Error Handling

- **Validation Errors**: Individual record validation with detailed error messages
- **Transaction Rollback**: Failed operations rollback completely
- **Permission Checks**: Standard Django REST framework permissions apply
- **Rate Limiting**: Standard API rate limiting applies

## Implementation Details

The bulk operations are implemented through:

1. **BulkActionMixin** (`common/mixins.py`): Core mixin providing bulk functionality
2. **BulkSerializers** (`common/bulk_serializers.py`): Swagger documentation schemas
3. **ViewSet Integration**: All major ViewSets inherit from the mixin
4. **Database Optimizations**: Select/prefetch related queries for performance

## Usage in Frontend

These endpoints are designed to be used by:
- Admin panels for bulk management operations
- Mobile apps for offline sync capabilities
- Data migration and import tools
- Batch processing workflows

## Testing

Comprehensive test coverage includes:
- Unit tests for each bulk operation
- Integration tests with real data
- Performance benchmarks
- Error condition testing

See `common/tests/test_bulk_actions.py` for detailed test examples.
