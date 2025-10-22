# 📊 Sistema de Generación de Reportes en Excel

## 🎯 **Descripción**

Sistema API que permite generar reportes en Excel basados en modelos de datos específicos. Los usuarios pueden solicitar datos de múltiples modelos y recibir un archivo Excel con cada modelo en una hoja separada.

## 🚀 **Características**

- ✅ **Multi-modelo**: Exporta datos de múltiples modelos en un solo Excel
- ✅ **Hojas organizadas**: Cada modelo se exporta en una hoja separada
- ✅ **Columnas auto-ajustadas**: Ancho de columnas optimizado automáticamente
- ✅ **API RESTful**: Endpoints JSON para integración con frontends
- ✅ **Autenticación**: Requiere usuario autenticado
- ✅ **Interfaz web**: Template HTML para usar desde el navegador

## 📋 **Modelos Disponibles**

### 1. **Guards** (`guard`)
```
Campos: ID, Username, First Name, Last Name, Email, Phone, Address, SSN, Is Armed, Is Active, Date Joined
```

### 2. **Properties** (`property`)
```
Campos: ID, Name, Alias, Address, Owner, Owner Email, Owner Phone, Created, Updated
```

### 3. **Shifts** (`shift`)
```
Campos: ID, Guard Name, Property, Start Time, End Time, Status, Notes, Created
```

### 4. **Clients** (`client`)
```
Campos: ID, Name, Email, Phone, Address, Contact Person, Properties Count, Created, Updated
```

### 5. **Users** (`user`)
```
Campos: ID, Username, First Name, Last Name, Email, Is Staff, Is Superuser, Is Active, Has Guard Profile, Date Joined, Last Login
```

## 🔗 **Endpoints API**

### 1. **Generar Reporte Excel**
```
POST /api/reports/generate-excel/
```

**Payload:**
```json
{
    "models": ["guard", "property", "shift"],
    "filename": "monthly_report_2025_10.xlsx"
}
```

**Response:** Archivo Excel descargable

### 2. **Modelos Disponibles**
```
GET /api/reports/available-models/
```

**Response:**
```json
{
    "available_models": {
        "guard": {
            "name": "Guards",
            "description": "Security guard profiles with user information",
            "fields": ["ID", "Username", "First Name", ...]
        },
        ...
    },
    "total_count": 5
}
```

## 🖥️ **Interfaz Web**

### **URL:** `/api/report-generator/`

La interfaz web permite:
- ✅ Seleccionar modelos con checkboxes
- ✅ Personalizar nombre del archivo
- ✅ Descargar archivo Excel directamente
- ✅ Ver mensajes de estado y errores

## 📝 **Ejemplos de Uso**

### **1. cURL - Generar Reporte Completo**
```bash
curl -X POST /api/reports/generate-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["guard", "property", "shift", "client", "user"],
    "filename": "complete_report_2025_10_22.xlsx"
  }' \
  --output report.xlsx
```

### **2. Python - Usando requests**
```python
import requests

response = requests.post(
    'https://your-domain.com/api/reports/generate-excel/',
    headers={
        'Authorization': 'Bearer YOUR_TOKEN',
        'Content-Type': 'application/json'
    },
    json={
        'models': ['guard', 'property'],
        'filename': 'guards_and_properties.xlsx'
    }
)

with open('report.xlsx', 'wb') as f:
    f.write(response.content)
```

### **3. JavaScript - Frontend**
```javascript
const generateReport = async () => {
    const response = await fetch('/api/reports/generate-excel/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            models: ['guard', 'shift'],
            filename: 'daily_report.xlsx'
        })
    });

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'daily_report.xlsx';
    a.click();
};
```

## 🛡️ **Seguridad**

- **Autenticación Requerida**: Todos los endpoints requieren usuario autenticado
- **Validación de Modelos**: Solo modelos predefinidos son permitidos
- **Sanitización**: Nombres de archivos son validados
- **Límites**: Se puede implementar rate limiting según necesidades

## ⚡ **Rendimiento**

- **Optimización de Queries**: Uso de `select_related()` para minimizar queries
- **Streaming**: Los archivos se generan en memoria para mejor rendimiento
- **Auto-dimensionado**: Columnas se ajustan automáticamente
- **Formato eficiente**: Uso de pandas + openpyxl para máxima eficiencia

## 🔧 **Personalización**

### **Agregar Nuevo Modelo:**
1. Agregar el modelo a `available_models` en `report_views.py`
2. Crear función `_get_MODELO_data()`
3. Definir campos y formateo de datos

### **Modificar Campos Exportados:**
Editar las funciones `_get_*_data()` para cambiar qué campos se incluyen.

### **Personalizar Formato:**
Modificar el writer de Excel en `generate_excel_report()` para styling avanzado.

## 📊 **Estructura del Excel Generado**

```
📁 report_2025_10_22.xlsx
├── 📄 Guards (121 registros)
│   ├── ID | Username | First Name | Last Name | ...
├── 📄 Properties (45 registros)
│   ├── ID | Name | Alias | Address | Owner | ...
├── 📄 Shifts (890 registros)
│   ├── ID | Guard Name | Property | Start Time | ...
└── ...
```

## 🎯 **Casos de Uso**

1. **Reportes Mensuales**: Exportar todos los datos para análisis
2. **Auditorías**: Generar reportes específicos por modelo
3. **Backups**: Crear respaldos de datos en formato Excel
4. **Análisis**: Datos estructurados para análisis en Excel/BI tools
5. **Integraciones**: Proporcionar datos a sistemas externos

El sistema está listo para uso en producción y se puede extender fácilmente para nuevos modelos y formatos.
