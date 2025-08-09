#!/bin/bash

# Script de inicialización para desarrollo local

echo "🔧 Configurando QU Security Backend para desarrollo local..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv .venv
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source .venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Verificar si existe .env
if [ ! -f ".env" ]; then
    echo "📄 Creando archivo .env..."
    cp .env.example .env
    echo "✏️  Edita el archivo .env con tus configuraciones locales"
fi

# Ejecutar migraciones
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Verificar configuración
echo "✅ Verificando configuración..."
python manage.py check

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "Próximos pasos:"
echo "1. Crear superusuario: python manage.py createsuperuser"
echo "2. Iniciar servidor: python manage.py runserver"
echo "3. Abrir en navegador: http://127.0.0.1:8000/"
echo ""
echo "Documentación API:"
echo "- Swagger: http://127.0.0.1:8000/swagger/"
echo "- ReDoc: http://127.0.0.1:8000/redoc/"
echo "- Admin: http://127.0.0.1:8000/admin/"
