# QU Security Backend - AWS Lambda Deployment

Este proyecto está configurado para desplegarse en AWS Lambda usando Zappa, con archivos estáticos y media almacenados en S3.

## Prerrequisitos

1. **AWS CLI configurado** con credenciales apropiadas
2. **Python 3.11** instalado
3. **PostgreSQL** para desarrollo local
4. **Cuenta de AWS** con permisos para:
   - Lambda
   - S3
   - RDS
   - VPC (si es necesario)

## Configuración Inicial

### 1. Clonar y configurar el proyecto

```bash
git clone <repository-url>
cd qu_security_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores reales
```

### 3. Configurar base de datos local (desarrollo)

```bash
# Crear base de datos PostgreSQL
createdb qu_security_db

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Probar el servidor local
python manage.py runserver
```

### 4. Configurar AWS

```bash
aws configure
# Ingresar Access Key ID, Secret Access Key, region, y output format
```

## Recursos AWS Necesarios

### 1. Crear bucket S3 para archivos estáticos

```bash
aws s3 mb s3://qu-security-static
aws s3 mb s3://qu-security-zappa-deployments
```

### 2. Configurar políticas de bucket S3

Política para archivos estáticos (permitir lectura pública):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::qu-security-static/*"
        }
    ]
}
```

### 3. Crear RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier qu-security-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxxx
```

## Deployment

### Primer deployment

```bash
./deploy.sh init
```

### Actualizaciones

```bash
./deploy.sh
```

### Comandos de gestión

```bash
# Ejecutar migraciones
zappa manage dev migrate

# Crear superusuario
zappa manage dev createsuperuser

# Recopilar archivos estáticos
zappa manage dev collectstatic

# Ver logs
zappa tail dev

# Ejecutar shell de Django
zappa invoke dev "from django.core.management import execute_from_command_line; execute_from_command_line(['manage.py', 'shell'])"
```

## Endpoints de la API

Una vez desplegado, la API estará disponible en:

```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/
```

### Autenticación

```
POST /auth/login/
POST /auth/refresh/
```

### Usuarios

```
GET    /users/          # Listar usuarios
POST   /users/          # Crear usuario
GET    /users/{id}/     # Obtener usuario
PUT    /users/{id}/     # Actualizar usuario
DELETE /users/{id}/     # Eliminar usuario
GET    /users/me/       # Perfil del usuario actual
```

### Guards

```
GET    /guards/         # Listar guardias
POST   /guards/         # Crear guardia
GET    /guards/{id}/    # Obtener guardia
PUT    /guards/{id}/    # Actualizar guardia
DELETE /guards/{id}/    # Eliminar guardia
```

### Clients

```
GET    /clients/                # Listar clientes
POST   /clients/                # Crear cliente
GET    /clients/{id}/           # Obtener cliente
PUT    /clients/{id}/           # Actualizar cliente
DELETE /clients/{id}/           # Eliminar cliente
GET    /clients/{id}/properties/ # Propiedades del cliente
```

### Properties

```
GET    /properties/             # Listar propiedades
POST   /properties/             # Crear propiedad
GET    /properties/{id}/        # Obtener propiedad
PUT    /properties/{id}/        # Actualizar propiedad
DELETE /properties/{id}/        # Eliminar propiedad
GET    /properties/{id}/shifts/ # Turnos de la propiedad
GET    /properties/{id}/expenses/ # Gastos de la propiedad
```

### Shifts

```
GET    /shifts/                 # Listar turnos
POST   /shifts/                 # Crear turno
GET    /shifts/{id}/            # Obtener turno
PUT    /shifts/{id}/            # Actualizar turno
DELETE /shifts/{id}/            # Eliminar turno
GET    /shifts/by_guard/?guard_id={id}     # Turnos por guardia
GET    /shifts/by_property/?property_id={id} # Turnos por propiedad
```

### Expenses

```
GET    /expenses/               # Listar gastos
POST   /expenses/               # Crear gasto
GET    /expenses/{id}/          # Obtener gasto
PUT    /expenses/{id}/          # Actualizar gasto
DELETE /expenses/{id}/          # Eliminar gasto
GET    /expenses/by_property/?property_id={id} # Gastos por propiedad
```

## Documentación API

Swagger UI estará disponible en:
- `/swagger/` - Interfaz Swagger
- `/redoc/` - Documentación ReDoc

## Monitoreo

```bash
# Ver logs en tiempo real
zappa tail dev

# Ver métricas de CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=qu-security-backend-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## Configuración de Producción

Para el ambiente de producción, actualizar `zappa_settings.json` y usar:

```bash
zappa deploy production
zappa update production
```

## Troubleshooting

### Error de conexión a base de datos
- Verificar que el RDS esté en la misma VPC que Lambda
- Configurar security groups correctamente
- Verificar variables de entorno de RDS

### Error 502 Bad Gateway
- Revisar logs con `zappa tail dev`
- Verificar que todas las dependencias estén en requirements.txt
- Aumentar timeout si es necesario

### Archivos estáticos no se cargan
- Verificar configuración de S3
- Ejecutar `zappa manage dev collectstatic`
- Verificar permisos de bucket S3

## Desarrollo Local

### Comandos útiles para desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Ejecutar shell de Django
python manage.py shell

# Ejecutar tests
python manage.py test
```

### Endpoints de desarrollo

Con el servidor local ejecutándose, puedes acceder a:

- **API Base**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Swagger Documentation**: http://127.0.0.1:8000/swagger/
- **ReDoc Documentation**: http://127.0.0.1:8000/redoc/

### Datos de prueba

Para crear datos de prueba, puedes usar el shell de Django:

```python
# python manage.py shell
from django.contrib.auth.models import User
from core.models import Guard, Client, Property, Shift, Expense

# Crear usuarios
guard_user = User.objects.create_user(username='guard1', password='password123')
client_user = User.objects.create_user(username='client1', password='password123')

# Crear guardia
guard = Guard.objects.create(user=guard_user, phone='123-456-7890')

# Crear cliente
client = Client.objects.create(user=client_user, phone='098-765-4321')

# Crear propiedad
property = Property.objects.create(
    owner=client, 
    address='123 Main St, City, State'
)
```
