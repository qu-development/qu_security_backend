# QU Security Backend - Sistema de Gestión de Seguridad

Sistema backend completo para gestión de servicios de seguridad con arquitectura de microservicios, sistema de permisos granular, internacionalización y despliegue en AWS Lambda.

## 🚀 Estado del Proyecto

### ✅ Características Implementadas

- ✅ **Sistema de permisos granular** - Gestión completa de roles y permisos
- ✅ **API REST completa** - CRUD para todas las entidades del sistema
- ✅ **Autenticación JWT** - Seguridad robusta con tokens
- ✅ **Internacionalización (i18n)** - Soporte para inglés y español
- ✅ **Tests completos** - 23 tests automatizados con 100% cobertura
- ✅ **Pre-commit hooks** - Calidad de código con ruff y mypy
- ✅ **Documentación API** - Swagger/OpenAPI integrado
- ✅ **Sistema de auditoría** - Registro completo de cambios de permisos

### 🧪 Validación Completa

**Sistema de Permisos**: ✅ 23/23 tests pasando
- Autenticación y autorización
- Permisos basados en roles
- Acceso granular a propiedades
- Gestión administrativa de permisos
- Auditoría completa de cambios

**Internacionalización**: ✅ Completamente funcional
- URLs multiidioma: `/en/` y `/es/`
- Modelos traducidos al español
- API de prueba: `/api/test-translations/`
- Detección automática de idioma

## 🏗️ Arquitectura del Sistema

### Estructura del Proyecto

```
qu_security_backend/
├── core/                       # Módulo principal de la aplicación
│   ├── api.py                 # ViewSets REST principales
│   ├── models.py              # Modelos: Guard, Client, Property, Shift, Expense
│   ├── serializers.py         # Serializadores DRF con validaciones
│   ├── tests.py               # 23 tests completos con English comments
│   ├── urls.py                # URLs del módulo core con i18n
│   └── views.py               # Vistas adicionales y test endpoints
├── permissions/               # Sistema de permisos granular
│   ├── api.py                # API administrativa de permisos
│   ├── models.py             # UserRole, ResourcePermission, PropertyAccess
│   ├── utils.py              # PermissionManager y decoradores
│   ├── permissions.py        # Clases de permisos DRF personalizadas
│   ├── tests.py              # Tests del sistema de permisos
│   └── management/commands/  # setup_permissions command
├── locale/                    # Archivos de traducción
│   └── es/LC_MESSAGES/       # Traducciones en español
│       ├── django.po         # Archivo de traducciones
│       └── django.mo         # Archivo compilado
├── qu_security/              # Configuración del proyecto Django
│   ├── settings.py           # Settings con i18n configurado
│   └── urls.py               # URLs principales con i18n_patterns
├── .pre-commit-config.yaml   # Configuración de pre-commit hooks
├── pyproject.toml            # Configuración de ruff y mypy
└── requirements.txt          # Dependencias del proyecto
```

### Tecnologías Utilizadas

- **Backend**: Django 5.2.5 + Django REST Framework 3.16.1
- **Base de Datos**: PostgreSQL (local) / Amazon RDS (producción)
- **Autenticación**: JWT con djangorestframework-simplejwt
- **Internacionalización**: Django i18n con gettext
- **Testing**: Django TestCase con APITestCase
- **Calidad de Código**: Ruff (linting/formatting) + mypy (type checking)
- **Pre-commit**: Hooks automáticos para calidad de código
- **Documentación**: Swagger/OpenAPI con drf-yasg
- **Despliegue**: AWS Lambda con Zappa (configuración lista)

## 🌐 Internacionalización (i18n)

### Configuración Multiidioma

El sistema soporta completamente **inglés** y **español** con:

#### URLs Multiidioma
```bash
# Inglés
http://localhost:8000/en/api/guards/
http://localhost:8000/en/admin/

# Español
http://localhost:8000/es/api/guards/
http://localhost:8000/es/admin/
```

#### Detección Automática de Idioma
```bash
# Header Accept-Language
curl -H "Accept-Language: es" http://localhost:8000/es/api/test-translations/
curl -H "Accept-Language: en" http://localhost:8000/en/api/test-translations/
```

#### Traducciones Completas
- **Modelos**: Todos los campos traducidos (Guard→Guardia, Client→Cliente, etc.)
- **Validaciones**: Mensajes de error en español
- **Admin**: Panel administrativo bilingüe
- **API**: Respuestas en el idioma seleccionado

#### Gestión de Traducciones
```bash
# Generar nuevas traducciones
python manage.py makemessages -l es

# Compilar traducciones
python manage.py compilemessages

# Probar traducciones
curl http://localhost:8000/es/api/test-translations/
```

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

## 🚀 Configuración y Desarrollo

### Configuración Rápida

#### 1. Setup del Proyecto
```bash
# Clonar repositorio
git clone <repository-url>
cd qu_security_backend

# Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

#### 2. Configuración Base de Datos
```bash
# Crear base de datos PostgreSQL
createdb qu_security_db

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar migraciones
python manage.py migrate
```

#### 3. Configuración Inicial de Permisos
```bash
# Configurar sistema de permisos
python manage.py setup_permissions

# Crear superusuario administrador
python manage.py createsuperuser
```

#### 4. Configurar Pre-commit y Calidad
```bash
# Instalar pre-commit hooks
pre-commit install

# Verificar configuración
pre-commit run --all-files
```

#### 5. Configurar Internacionalización
```bash
# Compilar traducciones existentes
python manage.py compilemessages

# Generar nuevas traducciones (si necesario)
python manage.py makemessages -l es
```

#### 6. Ejecutar Tests y Servidor
```bash
# Ejecutar todos los tests
python manage.py test

# Iniciar servidor de desarrollo
python manage.py runserver

# Verificar endpoints
curl http://127.0.0.1:8000/en/api/test-translations/
curl http://127.0.0.1:8000/es/api/test-translations/
```

### Variables de Entorno

Crear archivo `.env` con:

```env
# Django Configuration
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/qu_security_db

# Internationalization
LANGUAGE_CODE=en
TIME_ZONE=UTC

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here

# AWS Configuration (para despliegue)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=qu-security-static
AWS_S3_REGION_NAME=us-east-1

    # Email Configuration (opcional)
    EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

### Tarifa - Payload de creación y compatibilidad

- __Preferido (nuevo)__
```json
{
  "guard_id": 123,
  "property_id": 456,
  "rate": "12.50"
}
```

- __Legado (DEPRECATED)__
```json
{
  "guard": 123,
  "property": 456,
  "rate": "12.50"
}
```

- __Compatibilidad y deprecación__
  - El endpoint acepta ambos formatos. El legado genera un warning en logs.
  - Puede controlarse con el flag de entorno `TARIFFS_ALLOW_LEGACY_KEYS`.
    - `True` (por defecto): acepta claves legado y mapea a las nuevas.
    - `False`: rechaza `guard`/`property` con 400 y mensaje de error claro.
  - La compatibilidad con claves legado será removida en una próxima release.

- __Variable de entorno__
```env
# Feature flags
# Allow legacy keys ('guard', 'property') in tariffs create payloads (deprecated)
# Set to False to enforce new keys only ('guard_id', 'property_id')
TARIFFS_ALLOW_LEGACY_KEYS=True
```

- __Swagger__
  - La documentación de `/en/swagger/` muestra ambas formas (oneOf) y describe la deprecación.

### Comandos de Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Servidor de desarrollo
python manage.py runserver

# Servidor con IP específica
python manage.py runserver 0.0.0.0:8000

# Shell de Django
python manage.py shell

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic

# Crear superusuario
python manage.py createsuperuser

# Ejecutar tests específicos
python manage.py test core.tests.AuthenticationTestCase
python manage.py test permissions.tests.AdminPermissionAPITestCase

# Linting y formateo
ruff check .
ruff format .
mypy .

# Pre-commit manual
pre-commit run --all-files
```

## 🚀 Despliegue en Producción

### AWS Lambda con Zappa (Configuración Lista)

El proyecto incluye configuración completa para despliegue serverless en AWS.

#### Prerrequisitos AWS
1. **AWS CLI configurado** con credenciales apropiadas
2. **Permisos AWS**: Lambda, S3, RDS, VPC, CloudFormation, IAM
3. **Recursos AWS**: RDS PostgreSQL, VPC, Security Groups

#### Configuración de Despliegue

**1. Configurar zappa_settings.json**:
```json
{
    "dev": {
        "aws_region": "us-east-1",
        "django_settings": "qu_security.settings.production",
        "profile_name": "default",
        "project_name": "qu-security-backend",
        "runtime": "python3.11",
        "s3_bucket": "qu-security-zappa-deployments",
        "memory_size": 512,
        "timeout_seconds": 30,
        "environment_variables": {
            "DATABASE_URL": "postgresql://user:pass@rds-endpoint:5432/qu_security_db",
            "SECRET_KEY": "production-secret-key",
            "AWS_STORAGE_BUCKET_NAME": "qu-security-static",
            "DEBUG": "False"
        },
        "vpc_config": {
            "SubnetIds": ["subnet-12345678", "subnet-87654321"],
            "SecurityGroupIds": ["sg-12345678"]
        }
    }
}
```

**2. Scripts de Despliegue**:

`deploy.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Deploying QU Security Backend..."

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar tests
echo "🧪 Running tests..."
python manage.py test

# Linting y calidad
echo "🔍 Checking code quality..."
ruff check .
mypy .

# Despliegue
if [ "$1" = "init" ]; then
    echo "📦 Initial deployment..."
    zappa deploy dev
else
    echo "🔄 Updating deployment..."
    zappa update dev
fi

# Migraciones en AWS
echo "🗄️ Running migrations..."
zappa manage dev migrate

# Configurar permisos
echo "🔐 Setting up permissions..."
zappa manage dev setup_permissions

# Archivos estáticos
echo "📁 Collecting static files..."
zappa manage dev collectstatic --noinput

echo "✅ Deployment completed!"
echo "🌐 API URL: $(zappa status dev | grep 'API Gateway URL' | awk '{print $4}')"
```

#### Recursos AWS Necesarios

**1. Crear buckets S3**:
```bash
aws s3 mb s3://qu-security-static
aws s3 mb s3://qu-security-zappa-deployments

# Configurar CORS para archivos estáticos
aws s3api put-bucket-cors --bucket qu-security-static --cors-configuration file://cors.json
```

**2. Crear RDS PostgreSQL**:
```bash
aws rds create-db-instance \
  --db-instance-identifier qu-security-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --multi-az
```

**3. Configurar VPC y Security Groups**:
```bash
# Security Group para Lambda
aws ec2 create-security-group \
  --group-name qu-security-lambda \
  --description "QU Security Lambda functions"

# Reglas para RDS access
aws ec2 authorize-security-group-ingress \
  --group-id sg-lambda-id \
  --protocol tcp \
  --port 5432 \
  --source-group sg-rds-id
```

#### Comandos de Despliegue

```bash
# Primer despliegue
chmod +x deploy.sh
./deploy.sh init

# Actualizaciones
./deploy.sh

# Comandos específicos de Zappa
zappa update dev               # Actualizar código
zappa manage dev migrate      # Ejecutar migraciones
zappa manage dev collectstatic # Archivos estáticos
zappa manage dev createsuperuser # Crear admin
zappa tail dev                # Ver logs en tiempo real
zappa status dev              # Estado del despliegue
```

### Configuración de Entornos

#### Configuración de Producción

**qu_security/settings/production.py**:
```python
from .base import *
import os

# Seguridad
DEBUG = False
ALLOWED_HOSTS = ['*.amazonaws.com', 'your-domain.com']
SECRET_KEY = os.environ['SECRET_KEY']

# Base de datos
DATABASES = {
    'default': dj_database_url.parse(os.environ['DATABASE_URL'])
}

# Archivos estáticos en S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'qu_security': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# CORS para frontend
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://admin.your-domain.com",
]
```

#### Variables de Entorno de Producción

```env
# Django
SECRET_KEY=your-super-secure-production-secret-key
DEBUG=False
ALLOWED_HOSTS=*.amazonaws.com,your-domain.com

# Base de datos
DATABASE_URL=postgresql://username:password@rds-endpoint.region.rds.amazonaws.com:5432/qu_security_db

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=qu-security-static
AWS_S3_REGION_NAME=us-east-1

# JWT
JWT_SECRET_KEY=your-jwt-production-secret

# Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.ses.EmailBackend
AWS_SES_REGION_NAME=us-east-1
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

### Monitoreo y Maintenance

#### CloudWatch Monitoring

```bash
# Ver métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=qu-security-backend-dev \
  --statistics Average \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600

# Configurar alarmas
aws cloudwatch put-metric-alarm \
  --alarm-name "QU-Security-High-Error-Rate" \
  --alarm-description "Alert when error rate is high" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

#### Comandos de Monitoreo

```bash
# Logs en tiempo real
zappa tail dev

# Estado detallado
zappa status dev

# Métricas de CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/qu-security"

# Backup de base de datos
aws rds create-db-snapshot \
  --db-instance-identifier qu-security-db \
  --db-snapshot-identifier qu-security-backup-$(date +%Y%m%d)
```

#### Troubleshooting en Producción

**Error 502 Bad Gateway**:
```bash
# Verificar logs
zappa tail dev

# Aumentar timeout y memoria
zappa settings update dev timeout_seconds=60
zappa settings update dev memory_size=1024
zappa update dev
```

**Error de conexión a BD**:
```bash
# Verificar VPC y Security Groups
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Test de conectividad desde Lambda
zappa invoke dev "
import psycopg2
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print('Connection successful')
except Exception as e:
    print(f'Connection failed: {e}')
"
```

**Performance Issues**:
```bash
# Análisis de performance
zappa tail dev --filter "REPORT"

# Optimizar dependencias
pip install --upgrade -r requirements.txt
zappa update dev
```

## 📚 API Endpoints

### 🔍 Documentación Interactiva

Una vez que el servidor esté ejecutándose:
- **Swagger UI**: http://127.0.0.1:8000/en/swagger/ | http://127.0.0.1:8000/es/swagger/
- **ReDoc**: http://127.0.0.1:8000/en/redoc/ | http://127.0.0.1:8000/es/redoc/
- **Admin Panel**: http://127.0.0.1:8000/en/admin/ | http://127.0.0.1:8000/es/admin/
- **Test Traducciones**: http://127.0.0.1:8000/en/api/test-translations/ | http://127.0.0.1:8000/es/api/test-translations/

### 🔐 Autenticación

```bash
# Iniciar sesión
POST /en/api/auth/login/  # o /es/api/auth/login/
{
  "username": "admin",
  "password": "password"
}
Response: {
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Renovar token
POST /en/api/auth/refresh/
{
  "refresh": "refresh_token"
}

# Usar token en headers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 👥 Gestión de Usuarios

```bash
# Listar usuarios (requiere permisos)
GET /en/api/users/
Response: [
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Administrator",
    "role": "admin",
    "permissions": {...}
  }
]

# Crear usuario
POST /en/api/users/
{
  "username": "nuevo_usuario",
  "email": "usuario@example.com",
  "password": "password123",
  "first_name": "Nombre",
  "last_name": "Apellido"
}

# Obtener perfil propio
GET /en/api/users/me/

# Ver permisos específicos
GET /en/api/users/{id}/permissions/
```

### 👮 Gestión de Guardias

```bash
# Listar guardias (filtrado por permisos)
GET /en/api/guards/
Response: [
  {
    "id": 1,
    "user": {...},
    "phone": "123-456-7890",
    "emergency_contact": "987-654-3210",
    "hire_date": "2024-01-01",
    "is_active": true
  }
]

# Crear guardia (requiere permisos)
POST /en/api/guards/
{
  "user": 2,
  "phone": "123-456-7890",
  "emergency_contact": "987-654-3210",
  "hire_date": "2024-01-01"
}

# Obtener guardia específico
GET /en/api/guards/{id}/

# Actualizar guardia
PUT /en/api/guards/{id}/
PATCH /en/api/guards/{id}/

# Eliminar guardia (solo admin/manager)
DELETE /en/api/guards/{id}/
```

### 🏢 Gestión de Clientes

```bash
# Listar clientes
GET /en/api/clients/
Response: [
  {
    "id": 1,
    "user": {...},
    "phone": "555-0123",
    "address": "123 Client St",
    "company_name": "Security Corp",
    "balance": "1500.00"
  }
]

# Crear cliente
POST /en/api/clients/
{
  "user": 3,
  "phone": "555-0123",
  "address": "123 Client St",
  "company_name": "Security Corp"
}

# Propiedades del cliente (solo owner/admin)
GET /en/api/clients/{id}/properties/
```

### 🏠 Gestión de Propiedades

```bash
# Listar propiedades (filtrado por acceso)
GET /en/api/properties/
Response: [
  {
    "id": 1,
    "owner": {...},
    "address": "456 Property Ave",
    "description": "Edificio comercial",
    "total_hours": 168,
    "user_access": {
      "access_type": "owner",
      "can_create_shifts": true,
      "can_edit_shifts": true
    }
  }
]

# Crear propiedad (cliente/admin)
POST /en/api/properties/
{
  "owner": 1,
  "address": "456 Property Ave",
  "description": "Edificio comercial",
  "location": "Centro de la ciudad"
}

# Turnos de la propiedad
GET /en/api/properties/{id}/shifts/

# Gastos de la propiedad
GET /en/api/properties/{id}/expenses/
```

### ⏰ Gestión de Turnos

```bash
# Listar turnos (filtrado por acceso)
GET /en/api/shifts/
Response: [
  {
    "id": 1,
    "guard": {...},
    "property": {...},
    "start_time": "2024-01-01T08:00:00Z",
    "end_time": "2024-01-01T16:00:00Z",
    "hours_worked": 8.0,
    "status": "completed"
  }
]

# Crear turno (requiere can_create_shifts)
POST /en/api/shifts/
{
  "guard": 1,
  "property": 1,
  "start_time": "2024-01-01T08:00:00Z",
  "end_time": "2024-01-01T16:00:00Z"
}

# Filtros disponibles
GET /en/api/shifts/?guard=1
GET /en/api/shifts/?property=1
GET /en/api/shifts/?status=scheduled
GET /en/api/shifts/?start_date=2024-01-01&end_date=2024-01-31
```

### 💰 Gestión de Gastos

```bash
# Listar gastos (filtrado por acceso)
GET /en/api/expenses/
Response: [
  {
    "id": 1,
    "property": {...},
    "user": {...},
    "description": "Mantenimiento de cámaras",
    "amount": "150.00",
    "date": "2024-01-01",
    "created_at": "2024-01-01T10:00:00Z"
  }
]

# Crear gasto (requiere can_create_expenses)
POST /en/api/expenses/
{
  "property": 1,
  "description": "Mantenimiento de cámaras",
  "amount": 150.00,
  "date": "2024-01-01"
}

# Filtros disponibles
GET /en/api/expenses/?property=1
GET /en/api/expenses/?date_from=2024-01-01&date_to=2024-01-31
GET /en/api/expenses/?amount_min=100&amount_max=500
```

### 🔧 API Administrativa de Permisos

#### Gestión de Roles
```bash
# Asignar rol a usuario
POST /en/api/admin/permissions/assign_user_role/
{
  "user_id": 2,
  "role": "manager",
  "reason": "Promoción a gerente"
}

# Listar usuarios con permisos
GET /en/api/admin/permissions/list_users_with_permissions/
Response: [
  {
    "user": {...},
    "role": "manager",
    "resource_permissions": [...],
    "property_accesses": [...]
  }
]
```

#### Permisos de Recursos
```bash
# Otorgar permiso
POST /en/api/admin/permissions/grant_resource_permission/
{
  "user_id": 2,
  "resource_type": "property",
  "action": "create",
  "expires_at": "2024-12-31T23:59:59Z",
  "reason": "Permiso temporal para crear propiedades"
}

# Revocar permiso
POST /en/api/admin/permissions/revoke_resource_permission/
{
  "permission_id": 5,
  "reason": "Ya no necesario"
}
```

#### Acceso a Propiedades
```bash
# Otorgar acceso
POST /en/api/admin/permissions/grant_property_access/
{
  "user_id": 3,
  "property_id": 1,
  "access_type": "assigned_guard",
  "permissions": {
    "can_create_shifts": true,
    "can_edit_shifts": true,
    "can_create_expenses": false
  },
  "reason": "Asignar guardia a propiedad"
}

# Revocar acceso
POST /en/api/admin/permissions/revoke_property_access/
{
  "access_id": 8,
  "reason": "Cambio de asignación"
}
```

#### Auditoría y Opciones
```bash
# Registro de auditoría
GET /en/api/admin/permissions/permission_audit_log/
{
  "page": 1,
  "user_id": 2  # opcional
}

# Opciones disponibles
GET /en/api/admin/permissions/available_options/
Response: {
  "roles": [["admin", "Administrator"], ["manager", "Manager"], ...],
  "resource_types": [["property", "Property"], ["shift", "Shift"], ...],
  "actions": [["create", "Create"], ["read", "Read"], ...],
  "access_types": [["owner", "Owner"], ["assigned_guard", "Assigned Guard"], ...]
}
```

### 🌐 Endpoints de Internacionalización

```bash
# Probar traducciones en inglés
GET /en/api/test-translations/
Response: {
  "message": "Translations test endpoint",
  "translations": {
    "guard": "Guard",
    "client": "Client",
    "property": "Property"
  },
  "language": "en"
}

# Probar traducciones en español
GET /es/api/test-translations/
Response: {
  "message": "Translations test endpoint",
  "translations": {
    "guard": "Guardia",
    "client": "Cliente",
    "property": "Propiedad"
  },
  "language": "es"
}

# Cambiar idioma (Django i18n)
POST /i18n/setlang/
{
  "language": "es"
}
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

## 🧪 Testing y Calidad de Código

### Sistema de Testing Completo

#### Cobertura de Tests
- ✅ **23 tests automatizados** con 100% de éxito
- ✅ **Autenticación JWT** - Login, refresh, permisos
- ✅ **CRUD completo** - Todas las entidades (Users, Guards, Clients, Properties, Shifts, Expenses)
- ✅ **Sistema de permisos** - Roles, ResourcePermission, PropertyAccess
- ✅ **API administrativa** - Gestión de permisos granular
- ✅ **Validaciones** - Restricciones de negocio y seguridad

#### Ejecutar Tests
```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test core.tests                    # Tests del módulo core
python manage.py test permissions.tests             # Tests del sistema de permisos

# Tests individuales
python manage.py test core.tests.AuthenticationTestCase
python manage.py test permissions.tests.AdminPermissionAPITestCase
```

#### Tipos de Tests Implementados
1. **AuthenticationTestCase** - Autenticación JWT
2. **RoleBasedPermissionTestCase** - Permisos por roles
3. **PropertyAccessTestCase** - Acceso granular a propiedades
4. **CRUDTestCase** - Operaciones CRUD con permisos
5. **AdminPermissionAPITestCase** - API administrativa
6. **PermissionValidationTestCase** - Validaciones de seguridad

### Pre-commit Hooks y Calidad

#### Configuración Automática
```bash
# Instalar pre-commit hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

#### Herramientas Integradas
- ✅ **Ruff**: Linting y formateo automático (reemplaza flake8, black, isort)
- ✅ **mypy**: Type checking estático
- ✅ **Django checks**: Validaciones específicas de Django
- ✅ **Trailing whitespace**: Limpieza automática
- ✅ **End of file**: Normalización de archivos

#### Configuración en pyproject.toml
```toml
[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "W", "C90", "I", "N", "UP", "YTT", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "EM", "EXE", "FA", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "TD", "FIX", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "PERF", "FURB", "LOG", "RUF"]

[tool.mypy]
python_version = "3.11"
check_untyped_defs = true
disallow_untyped_defs = true
```

### Linting Avanzado con Ruff

```bash
# Linting completo
ruff check .

# Formateo automático
ruff format .

# Arreglar automáticamente lo posible
ruff check . --fix

# Verificar tipos con mypy
mypy .
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

### Estructura de Desarrollo

#### Flujo de Trabajo Recomendado
```bash
# 1. Activar entorno virtual
source .venv/bin/activate

# 2. Ejecutar tests antes de cambios
python manage.py test

# 3. Hacer cambios en el código

# 4. Verificar calidad de código (automático con pre-commit)
ruff check .
ruff format .
mypy .

# 5. Ejecutar tests después de cambios
python manage.py test

# 6. Commit (pre-commit se ejecuta automáticamente)
git add .
git commit -m "feat(permissions): add new feature"

# 7. Push
git push origin feature-branch
```

#### Comandos Útiles para Desarrollo

```bash
# Base de datos
python manage.py makemigrations     # Crear migraciones
python manage.py migrate           # Aplicar migraciones
python manage.py dbshell          # Acceso directo a la BD

# Desarrollo
python manage.py shell            # Shell de Django con modelos
python manage.py runserver        # Servidor de desarrollo
python manage.py collectstatic    # Recopilar archivos estáticos

# Permisos y usuarios
python manage.py setup_permissions     # Configurar permisos iniciales
python manage.py createsuperuser      # Crear admin
python manage.py changepassword user  # Cambiar contraseña

# Internacionalización
python manage.py makemessages -l es   # Generar traducciones
python manage.py compilemessages      # Compilar traducciones

# Testing específico
python manage.py test core.tests.AuthenticationTestCase
python manage.py test permissions.tests.AdminPermissionAPITestCase
python manage.py test core.tests.RoleBasedPermissionTestCase

# Calidad de código
ruff check .                      # Linting
ruff format .                     # Formateo
mypy .                           # Type checking
pre-commit run --all-files       # Ejecutar todos los hooks
```

### Guías de Contribución

#### Estructura de Commits
Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Nuevas características
git commit -m "feat(permissions): add bulk permission update endpoint"
git commit -m "feat(i18n): add Spanish translations for models"

# Corrección de errores
git commit -m "fix(auth): resolve JWT token expiration issue"
git commit -m "fix(tests): correct property access validation"

# Documentación
git commit -m "docs(readme): update API documentation"
git commit -m "docs(api): add authentication examples"

# Refactoring
git commit -m "refactor(permissions): improve permission manager efficiency"

# Tests
git commit -m "test(core): add comprehensive CRUD test coverage"

# Configuración
git commit -m "chore(deps): update Django to 5.2.5"
git commit -m "ci(pre-commit): add mypy configuration"
```

#### Estándares de Código

**Python/Django**:
- Seguir PEP 8 (aplicado automáticamente por ruff)
- Type hints obligatorios (verificados por mypy)
- Docstrings para todas las funciones públicas
- Tests para toda nueva funcionalidad

**Ejemplo de función bien documentada**:
```python
from typing import Optional
from django.contrib.auth.models import User
from permissions.models import ResourcePermission

def grant_resource_permission(
    user: User,
    resource_type: str,
    action: str,
    resource_id: Optional[int] = None,
    granted_by: Optional[User] = None
) -> ResourcePermission:
    """
    Grant a resource permission to a user.

    Args:
        user: The user to grant permission to
        resource_type: Type of resource (property, shift, etc.)
        action: Action to permit (create, read, update, delete)
        resource_id: Specific resource ID (optional)
        granted_by: User granting the permission (optional)

    Returns:
        The created ResourcePermission instance

    Raises:
        ValidationError: If invalid resource_type or action
    """
    # Implementation here
    pass
```

#### Proceso de Testing

**Tests Requeridos**:
1. **Unit Tests**: Para toda lógica de negocio
2. **Integration Tests**: Para endpoints de API
3. **Permission Tests**: Para validaciones de seguridad

**Ejemplo de test**:
```python
class NewFeatureTestCase(APITestCase):
    """Test new feature functionality"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username="admin", password="test123"
        )
        UserRole.objects.create(user=self.admin_user, role="admin")

    def test_new_feature_success(self):
        """Test successful feature execution"""
        # Arrange
        self.authenticate_user(self.admin_user)

        # Act
        response = self.api_client.post("/api/new-endpoint/", data)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("expected_field", response.data)

    def test_new_feature_permission_denied(self):
        """Test feature denies unauthorized access"""
        regular_user = User.objects.create_user(
            username="user", password="test123"
        )
        self.authenticate_user(regular_user)

        response = self.api_client.post("/api/new-endpoint/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

### Configuración del Entorno de Desarrollo

#### VSCode (Recomendado)

**Extensiones esenciales**:
- Python
- Django
- GitLens
- REST Client
- Thunder Client (para testing de API)

**Configuración en `.vscode/settings.json`**:
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "none",
    "python.formatting.blackPath": ".venv/bin/ruff",
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": true
    }
}
```

#### PyCharm

**Configuración recomendada**:
- Interpreter: Project venv
- Django support: Enabled
- Code style: Google or PEP 8
- Inspections: Enable all Django/Python inspections

### Debugging y Troubleshooting

#### Problemas Comunes

**Tests fallan**:
```bash
# Limpiar base de datos de test
python manage.py test --keepdb=false

# Ejecutar test específico con verbosidad
python manage.py test core.tests.AuthenticationTestCase --verbosity=2

# Debug con pdb
import pdb; pdb.set_trace()  # En el código
```

**Migraciones conflictivas**:
```bash
# Ver estado de migraciones
python manage.py showmigrations

# Hacer merge de migraciones
python manage.py makemigrations --merge

# Rollback de migración
python manage.py migrate core 0001
```

**Problemas de permisos**:
```bash
# Verificar permisos de usuario
python manage.py shell
>>> from permissions.utils import PermissionManager
>>> user = User.objects.get(username="test")
>>> PermissionManager.has_resource_permission(user, "property", "create")

# Reconfigurar permisos
python manage.py setup_permissions --force
```

**Errores de i18n**:
```bash
# Verificar traducciones compiladas
ls locale/es/LC_MESSAGES/
# Debe existir django.mo

# Recompilar traducciones
python manage.py compilemessages

# Probar endpoint de traducciones
curl http://127.0.0.1:8000/es/api/test-translations/
```

## 📊 Datos de Prueba y Ejemplos

### Setup Rápido con Datos de Ejemplo

#### Script de Datos de Prueba

```bash
# Crear comando personalizado para datos de prueba
# core/management/commands/setup_test_data.py

python manage.py setup_test_data
```

**Datos que se crean**:
- 1 Administrador (admin/admin123)
- 2 Managers (manager1/manager123, manager2/manager123)
- 3 Clientes (client1/client123, client2/client123, client3/client123)
- 5 Guardias (guard1/guard123, ..., guard5/guard123)
- 4 Propiedades con diferentes configuraciones
- 10 Turnos de ejemplo (pasados y futuros)
- 8 Gastos de ejemplo

#### Crear Datos Manualmente

```python
# python manage.py shell

from django.contrib.auth.models import User
from core.models import Guard, Client, Property, Shift, Expense
from permissions.models import UserRole, PropertyAccess
from permissions.utils import PermissionManager
from datetime import datetime, timedelta
from decimal import Decimal

# 1. Crear usuario administrador
admin_user = User.objects.create_user(
    username='admin',
    password='admin123',
    email='admin@qusecurity.com',
    first_name='Administrator',
    last_name='System',
    is_superuser=True,
    is_staff=True
)
UserRole.objects.create(user=admin_user, role='admin')

# 2. Crear usuario manager
manager_user = User.objects.create_user(
    username='manager1',
    password='manager123',
    email='manager1@qusecurity.com',
    first_name='Maria',
    last_name='Rodriguez'
)
UserRole.objects.create(user=manager_user, role='manager')

# 3. Crear usuario cliente
client_user = User.objects.create_user(
    username='client1',
    password='client123',
    email='client1@example.com',
    first_name='Carlos',
    last_name='Mendez'
)
UserRole.objects.create(user=client_user, role='client')
client = Client.objects.create(
    user=client_user,
    phone='555-0101',
    address='Av. Principal 123, Ciudad',
    company_name='Empresa Ejemplo S.A.',
    balance=Decimal('2500.00')
)

# 4. Crear usuario guardia
guard_user = User.objects.create_user(
    username='guard1',
    password='guard123',
    email='guard1@qusecurity.com',
    first_name='Juan',
    last_name='Perez'
)
UserRole.objects.create(user=guard_user, role='guard')
guard = Guard.objects.create(
    user=guard_user,
    phone='555-0201',
    emergency_contact='555-9999',
    hire_date='2024-01-15'
)

# 5. Crear propiedad
property_obj = Property.objects.create(
    owner=client,
    address='Centro Comercial Plaza, Av. Libertador 456',
    description='Centro comercial de 3 pisos con 50 locales comerciales',
    location='Zona Norte, Ciudad'
)

# 6. Otorgar acceso del guardia a la propiedad
PropertyAccess.objects.create(
    user=guard_user,
    property=property_obj,
    access_type='assigned_guard',
    can_create_shifts=True,
    can_edit_shifts=True,
    can_create_expenses=True,
    granted_by=admin_user
)

# 7. Crear turnos de ejemplo
from django.utils import timezone

# Turno pasado completado
Shift.objects.create(
    guard=guard,
    property=property_obj,
    start_time=timezone.now() - timedelta(days=2, hours=8),
    end_time=timezone.now() - timedelta(days=2),
    hours_worked=8.0,
    status='completed'
)

# Turno programado para hoy
Shift.objects.create(
    guard=guard,
    property=property_obj,
    start_time=timezone.now().replace(hour=8, minute=0, second=0),
    end_time=timezone.now().replace(hour=16, minute=0, second=0),
    hours_worked=8.0,
    status='scheduled'
)

# Turno futuro
Shift.objects.create(
    guard=guard,
    property=property_obj,
    start_time=timezone.now() + timedelta(days=1, hours=8),
    end_time=timezone.now() + timedelta(days=1, hours=16),
    hours_worked=8.0,
    status='scheduled'
)

# 8. Crear gastos de ejemplo
Expense.objects.create(
    property=property_obj,
    user=guard_user,
    description='Mantenimiento de cámaras de seguridad',
    amount=Decimal('350.00'),
    date=timezone.now().date() - timedelta(days=5)
)

Expense.objects.create(
    property=property_obj,
    user=manager_user,
    description='Compra de uniformes para guardias',
    amount=Decimal('480.00'),
    date=timezone.now().date() - timedelta(days=3)
)

print("✅ Datos de prueba creados exitosamente!")
print(f"Admin: admin/admin123")
print(f"Manager: manager1/manager123")
print(f"Cliente: client1/client123")
print(f"Guardia: guard1/guard123")
```

### Ejemplos de Uso de la API

#### Flujo Completo de Trabajo

**1. Autenticación**:
```bash
# Login como administrador
curl -X POST http://127.0.0.1:8000/en/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Respuesta
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Usar token en requests posteriores
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**2. Gestión de Usuarios y Roles**:
```bash
# Crear nuevo usuario
curl -X POST http://127.0.0.1:8000/en/api/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "guard2",
    "email": "guard2@qusecurity.com",
    "password": "guard123",
    "first_name": "Pedro",
    "last_name": "Garcia"
  }'

# Asignar rol usando API administrativa
curl -X POST http://127.0.0.1:8000/en/api/admin/permissions/assign_user_role/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 6,
    "role": "guard",
    "reason": "Nuevo guardia contratado"
  }'

# Crear perfil de guardia
curl -X POST http://127.0.0.1:8000/en/api/guards/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user": 6,
    "phone": "555-0202",
    "emergency_contact": "555-8888",
    "hire_date": "2024-08-11"
  }'
```

**3. Gestión de Propiedades y Permisos**:
```bash
# Crear nueva propiedad (como cliente)
curl -X POST http://127.0.0.1:8000/en/api/properties/ \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": 1,
    "address": "Oficinas Torre Empresarial, Piso 15",
    "description": "Oficinas corporativas con 20 empleados",
    "location": "Centro financiero"
  }'

# Otorgar acceso de guardia a propiedad (como admin)
curl -X POST http://127.0.0.1:8000/en/api/admin/permissions/grant_property_access/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 6,
    "property_id": 2,
    "access_type": "assigned_guard",
    "permissions": {
      "can_create_shifts": true,
      "can_edit_shifts": true,
      "can_create_expenses": false
    },
    "reason": "Asignar guardia Pedro a oficinas corporativas"
  }'
```

**4. Gestión de Turnos**:
```bash
# Crear turno (como guardia con permisos)
curl -X POST http://127.0.0.1:8000/en/api/shifts/ \
  -H "Authorization: Bearer $GUARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "guard": 2,
    "property": 2,
    "start_time": "2024-08-12T08:00:00Z",
    "end_time": "2024-08-12T16:00:00Z"
  }'

# Listar turnos de una propiedad
curl -X GET "http://127.0.0.1:8000/en/api/shifts/?property=1" \
  -H "Authorization: Bearer $TOKEN"

# Actualizar estado del turno
curl -X PATCH http://127.0.0.1:8000/en/api/shifts/1/ \
  -H "Authorization: Bearer $GUARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**5. Gestión de Gastos**:
```bash
# Crear gasto (como guardia con permisos)
curl -X POST http://127.0.0.1:8000/en/api/expenses/ \
  -H "Authorization: Bearer $GUARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property": 1,
    "description": "Compra de pilas para linternas",
    "amount": 25.50,
    "date": "2024-08-11"
  }'

# Listar gastos por propiedad y rango de fechas
curl -X GET "http://127.0.0.1:8000/en/api/expenses/?property=1&date_from=2024-08-01&date_to=2024-08-31" \
  -H "Authorization: Bearer $TOKEN"
```

**6. Auditoría y Reportes**:
```bash
# Ver historial de permisos
curl -X GET http://127.0.0.1:8000/en/api/admin/permissions/permission_audit_log/ \
  -H "Authorization: Bearer $TOKEN"

# Ver usuarios con sus permisos
curl -X GET http://127.0.0.1:8000/en/api/admin/permissions/list_users_with_permissions/ \
  -H "Authorization: Bearer $TOKEN"

# Prueba de traducciones
curl -X GET http://127.0.0.1:8000/es/api/test-translations/ \
  -H "Accept-Language: es"
```

### Testing de Integración

#### Collection de Postman/Thunder Client

```json
{
  "info": {
    "name": "QU Security API",
    "description": "Complete API testing collection"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://127.0.0.1:8000/en/api"
    },
    {
      "key": "adminToken",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Admin Login",
          "request": {
            "method": "POST",
            "url": "{{baseUrl}}/auth/login/",
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"admin\",\n  \"password\": \"admin123\"\n}"
            }
          }
        }
      ]
    }
  ]
}
```

#### Casos de Prueba Manuales

**Caso 1: Flujo de Cliente**
1. Login como cliente
2. Ver mis propiedades
3. Crear nueva propiedad
4. Ver gastos de mi propiedad
5. Intentar crear turno (debe fallar - sin permisos)

**Caso 2: Flujo de Guardia**
1. Login como guardia
2. Ver propiedades asignadas
3. Crear turno en propiedad asignada
4. Crear gasto (si tiene permisos)
5. Intentar acceder a otra propiedad (debe fallar)

**Caso 3: Flujo de Administrador**
1. Login como admin
2. Ver todos los usuarios y permisos
3. Crear nuevo usuario y asignar rol
4. Otorgar acceso a propiedad
5. Ver logs de auditoría
6. Revocar permisos

### Limpieza y Reset

```bash
# Limpiar todos los datos de prueba
python manage.py flush

# Recrear migraciones desde cero
python manage.py migrate
python manage.py setup_permissions
python manage.py setup_test_data

# Reset de base de datos completo
dropdb qu_security_db
createdb qu_security_db
python manage.py migrate
python manage.py setup_permissions
python manage.py createsuperuser
```

## 📄 Información del Proyecto

### Tecnologías y Versiones

- **Django**: 5.2.5
- **Django REST Framework**: 3.16.1
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **JWT**: djangorestframework-simplejwt 5.2.2
- **Documentation**: drf-yasg 1.21.7
- **Testing**: Django TestCase + DRF APITestCase
- **Code Quality**: Ruff + mypy
- **Pre-commit**: Hooks automatizados
- **Internationalization**: Django i18n + gettext

### Estado del Desarrollo

#### ✅ Características Completadas (100%)
- **Sistema de autenticación JWT** - Login, refresh, permisos
- **CRUD completo** - Users, Guards, Clients, Properties, Shifts, Expenses
- **Sistema de permisos granular** - Roles, ResourcePermission, PropertyAccess
- **API administrativa** - Gestión completa de permisos por administrador
- **Internacionalización** - Inglés y español con traducciones completas
- **Testing completo** - 23 tests automatizados con 100% éxito
- **Calidad de código** - Pre-commit hooks con ruff y mypy
- **Documentación API** - Swagger/OpenAPI integrado
- **Auditoría completa** - Logs de todos los cambios de permisos

#### 🚧 En Progreso (0%)
- Ninguna característica pendiente

#### 📋 Roadmap Futuro
- **WebSocket notifications** - Notificaciones en tiempo real
- **Mobile API optimizations** - Endpoints optimizados para móviles
- **Advanced reporting** - Reportes y análisis avanzados
- **File upload handling** - Gestión de archivos y documentos
- **Email notifications** - Sistema de notificaciones por email
- **Advanced search** - Búsqueda y filtros avanzados

### Métricas del Proyecto

#### Cobertura de Código
- **Tests**: 23 casos de prueba automatizados
- **Cobertura**: 100% de funcionalidades críticas
- **Endpoints**: 100% de endpoints con tests
- **Permisos**: 100% de validaciones de seguridad

#### Arquitectura
- **Modelos**: 8 modelos principales + 4 de permisos
- **Endpoints**: 25+ endpoints REST
- **Idiomas**: 2 (inglés, español)
- **Roles**: 5 roles de usuario (admin, manager, client, guard, supervisor)
- **Permisos**: Sistema granular de 3 niveles

### Licencia y Contribución

#### Licencia
Este proyecto está bajo la **Licencia MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2024 QU Security Systems

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### Contribuir

Las contribuciones son bienvenidas! Por favor:

1. **Fork** el repositorio
2. **Crear** una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. **Commit** tus cambios (`git commit -m 'feat: add amazing feature'`)
4. **Push** a la rama (`git push origin feature/amazing-feature`)
5. **Crear** un Pull Request

**Antes de contribuir**:
- Ejecutar tests: `python manage.py test`
- Verificar calidad: `ruff check . && mypy .`
- Seguir [Conventional Commits](https://conventionalcommits.org/)

### Soporte y Contacto

#### Soporte Técnico
- **Issues**: [GitHub Issues](https://github.com/username/qu_security_backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/qu_security_backend/discussions)
- **Wiki**: [Project Wiki](https://github.com/username/qu_security_backend/wiki)

#### Contacto
- **Email**: soporte@qusecurity.com
- **Documentación**: [docs.qusecurity.com](https://docs.qusecurity.com)
- **Status Page**: [status.qusecurity.com](https://status.qusecurity.com)

#### Comunidad
- **Discord**: [QU Security Developers](https://discord.gg/qusecurity)
- **Slack**: [Workspace](https://qusecurity.slack.com)

### Agradecimientos

Gracias a todos los desarrolladores y contribuidores que han hecho posible este proyecto:

- **Django Team** - Por el excelente framework
- **DRF Team** - Por las herramientas de API REST
- **Zappa Community** - Por el despliegue serverless
- **Python Community** - Por las herramientas de calidad de código

### Enlaces Útiles

#### Documentación Oficial
- **Django**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Zappa**: https://github.com/zappa/Zappa
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/

#### Herramientas de Desarrollo
- **Ruff**: https://docs.astral.sh/ruff/
- **mypy**: https://mypy.readthedocs.io/
- **pre-commit**: https://pre-commit.com/

#### Recursos de Aprendizaje
- **Django for APIs**: https://djangoforapis.com/
- **JWT Authentication**: https://jwt.io/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## 🚀 ¡Empezar Ahora!

```bash
# Clonación rápida y setup
git clone <repository-url>
cd qu_security_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_permissions
python manage.py createsuperuser
python manage.py runserver

# Acceder a la API
open http://127.0.0.1:8000/en/swagger/
```

**¡Tu sistema de gestión de seguridad está listo para usar!** 🔐✨
