# QU Security Backend - Sistema de Gestión de Seguridad

Sistema backend completo para gestión de servicios de seguridad con arquitectura de microservicios, sistema de permisos granular y despliegue en AWS Lambda.

## 🏗️ Arquitectura del Sistema

### Estructura del Proyecto

```
qu_security_backend/
├── core/                      # Módulo principal de la aplicación
│   ├── api.py                # Endpoints REST principales
│   ├── models.py             # Modelos de datos (User, Guard, Client, Property, Shift, Expense)
│   ├── serializers.py        # Serializadores DRF
│   └── urls.py               # URLs del módulo core
├── permissions/              # Sistema de permisos granular
│   ├── api.py               # API administrativa de permisos
│   ├── models.py            # Modelos de permisos (UserRole, ResourcePermission, PropertyAccess)
│   ├── utils.py             # Utilidades y decoradores de permisos
│   ├── permissions.py       # Clases de permisos personalizadas
│   └── management/commands/ # Comandos para configuración inicial
├── qu_security/             # Configuración del proyecto Django
└── requirements.txt         # Dependencias del proyecto
```

### Tecnologías Utilizadas

- **Backend**: Django 5.2.5 + Django REST Framework 3.16.1
- **Base de Datos**: PostgreSQL (local) / Amazon RDS (producción)
- **Autenticación**: JWT con djangorestframework-simplejwt
- **Despliegue**: AWS Lambda con Zappa
- **Almacenamiento**: Amazon S3 para archivos estáticos y media
- **Calidad de Código**: Ruff para linting y formateo
- **Documentación**: Swagger/OpenAPI con drf-spectacular

## 🔐 Sistema de Permisos

### Arquitectura de Permisos

El sistema implementa un **modelo de permisos granular** centrado en el administrador:

1. **Administrador**: Tiene acceso completo y puede asignar permisos a otros usuarios
2. **Gestión Centralizada**: Todos los permisos se gestionan desde la API administrativa
3. **Permisos Granulares**: Control a nivel de recurso, acción y objeto específico
4. **Auditoría Completa**: Registro de todos los cambios de permisos

### Modelos de Permisos

#### UserRole
- **admin**: Acceso total al sistema
- **manager**: Gestión de operaciones
- **client**: Propietario de propiedades
- **guard**: Personal de seguridad
- **supervisor**: Supervisión de guardias

#### ResourcePermission
Permisos específicos por recurso y acción:
- **Recursos**: property, shift, expense, guard, client
- **Acciones**: create, read, update, delete, approve, assign

#### PropertyAccess
Acceso granular a propiedades específicas:
- **Tipos de acceso**: owner, assigned_guard, supervisor, viewer
- **Permisos específicos**: can_create_shifts, can_edit_shifts, can_create_expenses, etc.

### API de Gestión de Permisos

La API administrativa permite al administrador:

```bash
# Listar usuarios con sus permisos
GET /api/v1/permissions/admin/list_users_with_permissions/

# Asignar rol a usuario
POST /api/v1/permissions/admin/assign_user_role/
{
  "user_id": 1,
  "role": "manager",
  "reason": "Promoción a gerente"
}

# Otorgar permiso de recurso
POST /api/v1/permissions/admin/grant_resource_permission/
{
  "user_id": 1,
  "resource_type": "property",
  "action": "create",
  "expires_at": "2024-12-31T23:59:59Z"
}

# Otorgar acceso a propiedad
POST /api/v1/permissions/admin/grant_property_access/
{
  "user_id": 2,
  "property_id": 1,
  "access_type": "assigned_guard",
  "permissions": {
    "can_create_shifts": true,
    "can_edit_shifts": true
  }
}

# Registro de auditoría
GET /api/v1/permissions/admin/permission_audit_log/
```

## 🚀 Configuración y Despliegue

### Prerrequisitos

1. **AWS CLI configurado** con credenciales apropiadas
2. **Python 3.11** instalado
3. **PostgreSQL** para desarrollo local
4. **Cuenta de AWS** con permisos para Lambda, S3, RDS, VPC

### Configuración Inicial

#### 1. Clonar y configurar el proyecto

```bash
git clone <repository-url>
cd qu_security_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores reales
```

Variables requeridas:
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/qu_security_db

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=qu-security-static
AWS_S3_REGION_NAME=us-east-1

# JWT
JWT_SECRET_KEY=your-jwt-secret
```

#### 3. Configurar base de datos y permisos iniciales

```bash
# Crear base de datos PostgreSQL
createdb qu_security_db

# Ejecutar migraciones
python manage.py migrate

# Configurar permisos iniciales
python manage.py setup_permissions

# Crear superusuario administrador
python manage.py createsuperuser

# Probar el servidor local
python manage.py runserver
```

### Recursos AWS Necesarios

#### 1. Crear buckets S3

```bash
aws s3 mb s3://qu-security-static
aws s3 mb s3://qu-security-zappa-deployments
```

#### 2. Configurar RDS PostgreSQL

```bash
aws rds create-db-instance 
  --db-instance-identifier qu-security-db 
  --db-instance-class db.t3.micro 
  --engine postgres 
  --master-username postgres 
  --master-user-password YOUR_PASSWORD 
  --allocated-storage 20 
  --vpc-security-group-ids sg-xxxxxxxxx
```

### Deployment

#### Primer deployment

```bash
./deploy.sh init
```

#### Actualizaciones

```bash
./deploy.sh
```

#### Comandos de gestión en AWS

```bash
# Ejecutar migraciones
zappa manage dev migrate

# Configurar permisos
zappa manage dev setup_permissions

# Crear superusuario
zappa manage dev createsuperuser

# Recopilar archivos estáticos
zappa manage dev collectstatic
```

## 📚 API Endpoints

### Autenticación

```bash
# Iniciar sesión
POST /auth/login/
{
  "username": "admin",
  "password": "password"
}

# Renovar token
POST /auth/refresh/
{
  "refresh": "refresh_token"
}
```

### Gestión de Usuarios

```bash
# Listar usuarios (con permisos)
GET /users/

# Crear usuario
POST /users/
{
  "username": "nuevo_usuario",
  "email": "usuario@example.com",
  "password": "password123",
  "first_name": "Nombre",
  "last_name": "Apellido"
}

# Obtener perfil propio
GET /users/me/

# Asignar rol (Admin/Manager)
POST /users/{id}/assign_role/
{
  "role": "guard"
}

# Ver permisos de usuario
GET /users/{id}/permissions/
```

### Gestión de Guardias

```bash
# Listar guardias
GET /guards/

# Crear guardia
POST /guards/
{
  "user_id": 2,
  "phone": "123-456-7890",
  "emergency_contact": "987-654-3210",
  "hire_date": "2024-01-01"
}

# Obtener disponibilidad
GET /guards/{id}/availability/

# Asignar a propiedad
POST /guards/{id}/assign_property/
{
  "property_id": 1,
  "start_date": "2024-01-01"
}
```

### Gestión de Clientes

```bash
# Listar clientes
GET /clients/

# Crear cliente
POST /clients/
{
  "user_id": 3,
  "phone": "555-0123",
  "address": "123 Client St",
  "company_name": "Security Corp"
}

# Propiedades del cliente
GET /clients/{id}/properties/
```

### Gestión de Propiedades

```bash
# Listar propiedades
GET /properties/

# Crear propiedad
POST /properties/
{
  "owner_id": 1,
  "address": "456 Property Ave",
  "description": "Edificio comercial",
  "security_requirements": "Vigilancia 24/7"
}

# Turnos de la propiedad
GET /properties/{id}/shifts/

# Gastos de la propiedad
GET /properties/{id}/expenses/

# Otorgar acceso (Client/Admin)
POST /properties/{id}/grant_access/
{
  "user_id": 4,
  "access_type": "assigned_guard",
  "permissions": {
    "can_create_shifts": true
  }
}
```

### Gestión de Turnos

```bash
# Listar turnos
GET /shifts/

# Crear turno
POST /shifts/
{
  "guard_id": 1,
  "property_id": 1,
  "start_time": "2024-01-01T08:00:00Z",
  "end_time": "2024-01-01T16:00:00Z",
  "status": "scheduled"
}

# Turnos por guardia
GET /shifts/by_guard/?guard_id=1

# Turnos por propiedad
GET /shifts/by_property/?property_id=1
```

### Gestión de Gastos

```bash
# Listar gastos
GET /expenses/

# Crear gasto
POST /expenses/
{
  "property_id": 1,
  "description": "Mantenimiento de cámaras",
  "amount": 150.00,
  "date": "2024-01-01",
  "category": "maintenance"
}

# Gastos por propiedad
GET /expenses/by_property/?property_id=1
```

### API Administrativa de Permisos

```bash
# Listar todos los usuarios con permisos
GET /api/v1/permissions/admin/list_users_with_permissions/

# Asignar rol
POST /api/v1/permissions/admin/assign_user_role/

# Otorgar permiso de recurso
POST /api/v1/permissions/admin/grant_resource_permission/

# Revocar permiso de recurso
POST /api/v1/permissions/admin/revoke_resource_permission/

# Otorgar acceso a propiedad
POST /api/v1/permissions/admin/grant_property_access/

# Revocar acceso a propiedad
POST /api/v1/permissions/admin/revoke_property_access/

# Registro de auditoría
GET /api/v1/permissions/admin/permission_audit_log/

# Actualización masiva de permisos
POST /api/v1/permissions/admin/bulk_permission_update/

# Opciones disponibles
GET /api/v1/permissions/admin/available_options/
```

## 🛡️ Seguridad y Permisos

### Flujo de Autorización

1. **Autenticación JWT**: Todos los endpoints requieren token válido
2. **Verificación de Rol**: Se verifica el rol del usuario (UserRole)
3. **Permisos de Recurso**: Se evalúan permisos específicos (ResourcePermission)
4. **Acceso a Propiedades**: Se verifica acceso granular (PropertyAccess)
5. **Filtrado de Queryset**: Los datos se filtran según permisos del usuario

### Decoradores de Permisos

```python
from permissions.utils import permission_required

@permission_required('property', 'create')
def create_property(request):
    # Solo usuarios con permiso 'create' en 'property'
    pass

@permission_required('shift', 'update', resource_id_field='property_id')
def update_shift(request, shift_id):
    # Verifica permiso específico para la propiedad del turno
    pass
```

### Middlewares de Seguridad

- **Filtrado automático**: Los querysets se filtran automáticamente según permisos
- **Logging de auditoría**: Todas las acciones se registran en PermissionLog
- **Validación de expiración**: Los permisos con fecha de expiración se validan automáticamente

## 🧪 Testing y Calidad

### Linting con Ruff

```bash
# Ejecutar linting
ruff check .

# Formatear código
ruff format .

# Configuración en .ruff.toml
```

### Testing

```bash
# Ejecutar tests
python manage.py test

# Tests específicos
python manage.py test core.tests
python manage.py test permissions.tests
```

## 📖 Documentación

### Swagger/OpenAPI

Una vez desplegado, la documentación estará disponible en:
- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### Desarrollo Local

Con el servidor local ejecutándose:
- **API Base**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Swagger**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/

## 🚨 Monitoreo y Troubleshooting

### Comandos de Monitoreo

```bash
# Ver logs en tiempo real
zappa tail dev

# Estado de la función Lambda
aws lambda get-function --function-name qu-security-backend-dev

# Métricas de CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/qu-security"
```

### Problemas Comunes

#### Error de conexión a base de datos
- Verificar configuración de RDS y VPC
- Comprobar security groups
- Validar variables de entorno

#### Error 502 Bad Gateway
- Revisar logs con `zappa tail dev`
- Verificar timeout de Lambda
- Comprobar dependencias en requirements.txt

#### Permisos insuficientes
- Verificar rol del usuario con `/users/{id}/permissions/`
- Comprobar configuración inicial con `setup_permissions`
- Revisar logs de auditoría

## 🔧 Desarrollo y Contribución

### Configuración de Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Ejecutar servidor de desarrollo
python manage.py runserver
```

### Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Shell de Django
python manage.py shell

# Recopilar archivos estáticos
python manage.py collectstatic

# Crear datos de prueba
python manage.py setup_test_data
```

### Estructura de Commits

```bash
# Formato recomendado
git commit -m "feat(permissions): add bulk permission update endpoint"
git commit -m "fix(auth): resolve JWT token expiration issue"
git commit -m "docs(readme): update API documentation"
```

## 📊 Datos de Prueba

### Crear Datos de Ejemplo

```python
# python manage.py shell
from django.contrib.auth.models import User
from core.models import Guard, Client, Property, Shift, Expense
from permissions.models import UserRole

# Crear usuario administrador
admin_user = User.objects.create_user(
    username='admin', 
    password='admin123',
    email='admin@example.com',
    is_superuser=True
)
UserRole.objects.create(user=admin_user, role='admin')

# Crear usuario guardia
guard_user = User.objects.create_user(
    username='guard1', 
    password='guard123',
    email='guard1@example.com'
)
UserRole.objects.create(user=guard_user, role='guard')
guard = Guard.objects.create(user=guard_user, phone='123-456-7890')

# Crear usuario cliente
client_user = User.objects.create_user(
    username='client1', 
    password='client123',
    email='client1@example.com'
)
UserRole.objects.create(user=client_user, role='client')
client = Client.objects.create(user=client_user, phone='098-765-4321')

# Crear propiedad
property = Property.objects.create(
    owner=client, 
    address='123 Main St, City, State',
    description='Oficina principal'
)
```

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

## 📞 Soporte

Para soporte técnico o consultas:
- **Email**: soporte@qusecurity.com
- **Documentación**: [Wiki del proyecto](link-to-wiki)
- **Issues**: [GitHub Issues](link-to-issues)
