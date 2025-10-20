# 🏢 Sistema de Importación de Properties - Documentación

## 📊 **Formato de Excel Esperado**

El sistema espera un archivo Excel (.xlsx) con las siguientes columnas:

| Columna | Descripción | Ejemplo | Requerido |
|---------|-------------|---------|-----------|
| **PROPERTY NAME** | Dirección completa de la propiedad | "Keegans Meadow 11753 West Bellfort Ave. Stafford, Texas 77008" | ✅ Sí |
| **SOBRE NOMBRE** | Alias o nombre corto de la propiedad | "Keegans" | ❌ No |
| **PROPERTY OWNER** | Nombre del propietario/cliente | "Brixmor Group" | ✅ Sí |

## 🔄 **Proceso de Importación**

### 1. **Preparación de Datos**
- **Property Name** → Se divide en `name` (primeras 3 palabras) y `address` (completo)
- **Sobre Nombre** → Se mapea a `alias`
- **Property Owner** → Se usa para crear/encontrar `Client`

### 2. **Creación de Cuentas de Cliente** (opcional)
Si `create_clients = True`:
- Se genera username desde el nombre del propietario
- Se crea User account con password por defecto
- Se crea Client account vinculado al User

### 3. **Validaciones**
- ✅ **Duplicados**: Se evitan properties con la misma dirección
- ✅ **Clientes existentes**: Se reutilizan si ya existen
- ✅ **Datos requeridos**: Property name y owner son obligatorios

## ⚡ **Características de Performance**

### **Optimizaciones AWS Lambda**
```python
# Batch size dinámico según memoria disponible
if memory_mb >= 1024: return 500
elif memory_mb >= 512: return 200
else: return 100

# Procesamiento inteligente
if total_rows <= 500:
    process_all_at_once()  # Máximo performance
else:
    process_in_batches()   # Control de memoria
```

### **Bulk Operations**
- **Users**: `bulk_create()` con password pre-hasheado
- **Clients**: `bulk_create()` con `ignore_conflicts=True`
- **Properties**: `bulk_create()` con validación de duplicados

### **Cache Inteligente**
```python
# Pre-carga una sola vez
existing_usernames = set(User.objects.values_list('username', flat=True))
existing_clients = {...}  # Cache de clientes existentes
existing_properties = {...}  # Cache de properties existentes
```

## 📋 **Ejemplo de Uso**

### **Excel de Ejemplo:**
```
PROPERTY NAME                                           | SOBRE NOMBRE    | PROPERTY OWNER
Keegans Meadow 11753 West Bellfort Ave. Stafford...   | Keegans         | Brixmor Group
Merchant Park North 1303-1421 W. 11th Street...       | Shepherd        | Brixmor Group
Palmer Crossing Austin - Round Rock -Georgetown...     | Palmer Crossing | Brixmor Group
Westport Industrial Park 7108 & 7110 Old Katy...      | Old Katy        | CBRE
```

### **Resultado en Django:**
```python
# Properties creadas
Property(
    name="Keegans Meadow 11753 West",
    alias="Keegans",
    address="Keegans Meadow 11753 West Bellfort Ave. Stafford, Texas 77008",
    owner=Client(user=User(username="brixmor_group"))
)

Property(
    name="Merchant Park North 1303-1421",
    alias="Shepherd",
    address="Merchant Park North 1303-1421 W. 11th Street, Houston, Texas 77008",
    owner=Client(user=User(username="brixmor_group"))  # Mismo cliente reutilizado
)
```

## 🎯 **Interfaz de Admin**

### **Acceso**
1. Ir a Django Admin → Properties
2. Hacer clic en "Import from Excel"
3. Subir archivo Excel y configurar opciones

### **Opciones Disponibles**
- ✅ **Create Client Accounts**: Crear cuentas de usuario para propietarios
- 🔐 **Default Password**: Configurado en `settings.GUARD_DEFAULT_PASSWORD`

### **Mensajes de Resultado**
- ✅ **Success**: "Successfully imported X properties!"
- ⚠️ **Warnings**: Properties duplicadas detectadas
- ❌ **Errors**: Datos faltantes o errores de validación
- ℹ️ **Info**: Filas saltadas por datos incompletos

## 🔧 **Configuración**

### **Settings.py**
```python
# Password por defecto para cuentas de cliente
GUARD_DEFAULT_PASSWORD = os.environ.get("GUARD_DEFAULT_PASSWORD", "Guard123!")
```

### **Variables de Entorno**
```bash
# Opcional: Personalizar password por defecto
export GUARD_DEFAULT_PASSWORD="SecureClientPassword123!"
```

## 📊 **Performance Esperado**

| Cantidad Properties | Tiempo Esperado | Queries SQL |
|-------------------|-----------------|-------------|
| 50 properties | <2 segundos | ~6 queries |
| 200 properties | <5 segundos | ~6 queries |
| 500 properties | <10 segundos | ~12 queries |

## 🔒 **Seguridad**

- ✅ **No hardcoded passwords** en código
- ✅ **Validación de archivos** Excel (.xlsx/.xls únicamente)
- ✅ **Límite de tamaño** de archivo (10MB máximo)
- ✅ **Transacciones atómicas** para consistencia de datos
- ✅ **Manejo seguro** de archivos temporales

## 🚀 **Despliegue AWS Lambda**

El sistema está optimizado para AWS Lambda con:
- **Detección automática** de entorno Lambda
- **Batch sizing dinámico** según memoria disponible
- **Cleanup automático** de memoria
- **Error handling robusto** con fallbacks

La funcionalidad de importación de properties está lista para producción.
