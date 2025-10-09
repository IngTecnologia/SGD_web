# ===============================================
# Dockerfile para SGD Web Backend
# FastAPI + PostgreSQL + Microsoft 365 Integration
# ===============================================

# === STAGE 1: Base Python Image ===
FROM python:3.11-slim as base

# Información del mantenedor
LABEL maintainer="SGD Web Team"
LABEL description="Sistema de Gestión Documental Web - Backend API"
LABEL version="1.0.0"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# === STAGE 2: System Dependencies ===
FROM base as system-deps

# Actualizar lista de paquetes e instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Dependencias para compilación
    build-essential \
    gcc \
    g++ \
    # Dependencias para PostgreSQL
    libpq-dev \
    # Dependencias para procesamiento de imágenes
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    # Dependencias para OpenCV
    libopencv-dev \
    python3-opencv \
    # Dependencias para detección de tipos MIME
    libmagic1 \
    libmagic-dev \
    # Dependencias para zbar (códigos QR)
    libzbar0 \
    libzbar-dev \
    # Herramientas del sistema
    curl \
    wget \
    git \
    # Dependencias para procesamiento de archivos
    poppler-utils \
    # Limpieza de cache
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# === STAGE 3: Python Dependencies ===
FROM system-deps as python-deps

# Actualizar pip y instalar herramientas básicas
RUN pip install --upgrade pip setuptools wheel

# Crear usuario no-root para mayor seguridad
RUN groupadd -r sgduser && useradd -r -g sgduser sgduser

# Crear directorio de aplicación
WORKDIR /app

# Copiar archivo de requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# === STAGE 4: Application Setup ===
FROM python-deps as app-setup

# Crear directorios necesarios
RUN mkdir -p /app/storage/documents \
    && mkdir -p /app/storage/temp \
    && mkdir -p /app/templates \
    && mkdir -p /app/logs \
    && mkdir -p /app/static

# Copiar código de la aplicación
COPY ./app /app/app

# Copiar templates y static si existen
COPY ./templates /app/templates
COPY ./static /app/static

# Copiar archivos de configuración de Alembic
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /app/alembic

# === STAGE 5: Production Image ===
FROM app-setup as production

# Variables de entorno específicas para producción
ENV ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO

# Establecer permisos correctos
RUN chown -R sgduser:sgduser /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/storage \
    && chmod -R 777 /app/logs \
    && chmod -R 777 /app/templates

# Cambiar a usuario no-root
USER sgduser

# Exponer puerto de la aplicación
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# === STAGE 6: Development Image ===
FROM app-setup as development

# Variables de entorno para desarrollo
ENV ENVIRONMENT=development \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=DEBUG

# Instalar dependencias adicionales para desarrollo
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy \
    httpx \
    ipython

# Crear directorio para tests
RUN mkdir -p /app/tests

# Establecer permisos para desarrollo (más permisivos)
RUN chown -R sgduser:sgduser /app \
    && chmod -R 777 /app

# Cambiar a usuario no-root
USER sgduser

# Exponer puerto de la aplicación
EXPOSE 8000

# Comando para desarrollo con reload automático
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/app"]

# === STAGE 7: Testing Image ===
FROM development as testing

# Variables de entorno para testing
ENV ENVIRONMENT=testing \
    POSTGRES_DB=sgd_test_db

# Instalar dependencias adicionales para testing
RUN pip install --no-cache-dir \
    factory-boy \
    faker \
    pytest-xdist \
    pytest-mock

# Comando para ejecutar tests
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=app", "--cov-report=html"]

# ===============================================
# Instrucciones de uso:
# ===============================================
#
# 1. Para desarrollo:
#    docker build --target development -t sgd-web-backend:dev .
#    docker run -p 8000:8000 -v $(pwd):/app sgd-web-backend:dev
#
# 2. Para producción:
#    docker build --target production -t sgd-web-backend:prod .
#    docker run -p 8000:8000 sgd-web-backend:prod
#
# 3. Para testing:
#    docker build --target testing -t sgd-web-backend:test .
#    docker run sgd-web-backend:test
#
# 4. Con docker-compose (recomendado):
#    docker-compose up --build
#
# ===============================================