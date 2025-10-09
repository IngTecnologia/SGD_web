# Sistema de Gestión Documental (SGD) - Brief del Proyecto y Especificaciones

## 📌 CONTEXTO DEL PROYECTO

### Sobre INEMEC y el Sistema Actual
Este es un **Sistema de Gestión Documental (SGD)** desarrollado para INEMEC, una organización que maneja grandes volúmenes de documentos físicos manuscritos que necesitan ser digitalizados y gestionados eficientemente.

### Versión Actual (v1.2.0)
- **Plataforma**: Aplicación de escritorio en Python con tkinter/ttkbootstrap
- **Almacenamiento**: Google Drive + Google Sheets
- **Funcionalidades principales**:
  1. **Generación de Documentos**: Crea documentos Word con códigos QR únicos
  2. **Registro de Documentos**: Escanea documentos, lee QR y los sube a la nube
  3. **Búsqueda de Documentos**: Busca y descarga documentos por cédula

### Desafío Actual
La mayoría de los documentos son **manuscritos escaneados**, lo que dificulta:
- Búsqueda por contenido
- Extracción de información
- Análisis de datos
- Procesamiento semántico

### Visión a Futuro
Existe un plan de **migración completa a aplicación web** con servidor propio y PostgreSQL. El trabajo actual es un **prototipo/transición** para validar nuevas funcionalidades antes de la migración definitiva.

---

## 🎯 OBJETIVOS DE LA REFACTORIZACIÓN (Prototipo Actual)

### Prioridad 1: Migración de Almacenamiento
**DE:** Google Drive + Google Sheets
**A:** Microsoft OneDrive + SQLite local

**Razones:**
- Mayor control sobre permisos y accesos
- Integración más sencilla con entorno corporativo
- SQLite es más adecuado para migración futura a PostgreSQL
- OneDrive tiene mejor API para metadatos

### Prioridad 2: QR Opcional
**Problema actual**: El sistema rechaza documentos sin código QR, pero hay miles de documentos históricos sin QR pendientes de ser subidos.

**Solución requerida**:
- El sistema debe **intentar** leer el QR
- Si encuentra QR → Registrarlo y marcar `tiene_qr = True`
- Si NO encuentra QR → Permitir continuar y marcar `tiene_qr = False`
- Mostrar indicador visual claro del estado del QR

**Implementación**: Debe ser simple, solo un indicador visual (ej: ícono ✓ o ✗) sin mensajes de error intrusivos.

### Prioridad 3: Campos Parametrizables por Tipo de Documento
**Problema actual**: Solo se registra la cédula. La información del documento se pierde.

**Solución requerida**:
Los documentos corporativos tienen estructura definida con campos específicos. El sistema debe:
1. Permitir definir **tipos de documentos** (ej: GCO-REG-009, GCO-REG-010, etc.)
2. Para cada tipo, definir **qué campos tiene**
3. Al subir un documento, el usuario:
   - Selecciona el tipo de documento
   - El sistema muestra automáticamente los campos correspondientes
   - El usuario digita manualmente lo que ve en el documento escaneado
4. Estos datos se guardan:
   - En la **base de datos** para búsqueda
   - Como **metadatos del archivo** en OneDrive

**Habrán cientos de tipos de documentos**, por lo que:
- La configuración debe ser **externa al código** (JSON)
- Un administrador debe poder agregar nuevos tipos sin modificar código
- No es necesario un módulo de administración por ahora (se editará el JSON directamente)

---

## 🏗️ ARQUITECTURA PROPUESTA

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│                    (Menú Principal)                         │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┬─────────────────┬───────────────┐
    ▼                       ▼                 ▼               ▼
┌─────────┐         ┌──────────────┐   ┌─────────────┐  ┌─────────────┐
│Generator│         │   Register   │   │   Search    │  │  Types      │
│         │         │              │   │             │  │  Config     │
└─────────┘         └──────┬───────┘   └──────┬──────┘  └─────────────┘
                           │                  │
                    ┌──────┴──────┬───────────┴──────┐
                    ▼             ▼                  ▼
            ┌──────────────┐  ┌────────────┐  ┌──────────────┐
            │  OneDrive    │  │  Database  │  │ Document     │
            │  Manager     │  │  Manager   │  │ Types JSON   │
            └──────────────┘  └────────────┘  └──────────────┘
                    │             │
                    ▼             ▼
            ┌──────────────┐  ┌────────────┐
            │  OneDrive    │  │  SQLite    │
            │  (Cloud)     │  │  (Local)   │
            └──────────────┘  └────────────┘
```

### Stack Tecnológico

**Backend/Lógica:**
- Python 3.8+
- SQLite (base de datos local)
- Microsoft Graph API (OneDrive)
- MSAL (autenticación Microsoft)

**Frontend/UI:**
- tkinter (base)
- ttkbootstrap (tema moderno)

**Procesamiento:**
- PyMuPDF (PDFs)
- Pillow (imágenes)
- OpenCV + pyzbar (lectura de QR)
- python-docx (generación de documentos)

---

## 📊 MODELO DE DATOS

### Base de Datos SQLite

#### Tabla: `documentos`
```sql
CREATE TABLE documentos (
    id INTEGER PRIMARY KEY,
    qr_code TEXT,                    -- Código QR (puede ser NULL)
    tipo_documento TEXT NOT NULL,    -- Ej: "GCO-REG-009"
    archivo_onedrive_id TEXT NOT NULL,
    archivo_nombre TEXT NOT NULL,
    archivo_url TEXT,
    tiene_qr BOOLEAN DEFAULT 0,      -- TRUE si tiene QR
    fecha_registro TIMESTAMP,
    observaciones TEXT
);
```

#### Tabla: `documento_campos`
```sql
CREATE TABLE documento_campos (
    id INTEGER PRIMARY KEY,
    documento_id INTEGER,
    campo_nombre TEXT NOT NULL,      -- Ej: "cedula", "nombre_completo"
    campo_valor TEXT,                -- Valor del campo
    FOREIGN KEY (documento_id) REFERENCES documentos(id)
);
```

#### Tabla: `tipos_documento`
```sql
CREATE TABLE tipos_documento (
    codigo TEXT PRIMARY KEY,         -- Ej: "GCO-REG-009"
    nombre TEXT NOT NULL,
    definicion_json TEXT NOT NULL,   -- Definición completa del tipo
    activo BOOLEAN DEFAULT 1
);
```

### Estructura de Archivos en OneDrive

```
OneDrive/
└── Documentos_SGD/
    ├── GCO-REG-009_123456789_20250109_143021.pdf
    ├── GCO-REG-009_987654321_20250109_143045.pdf
    └── OTRO-DOC-001_555555555_20250109_150000.jpg
```

**Nomenclatura**: `{tipo_documento}_{identificador}_{timestamp}.{extension}`

### Metadatos en OneDrive

Los archivos en OneDrive llevarán metadatos embebidos:
```json
{
  "tipo_documento": "GCO-REG-009",
  "cedula": "123456789",
  "nombre_completo": "Juan Pérez",
  "fecha_documento": "2025-01-05",
  "tiene_qr": true,
  "qr_code": "uuid-xxxx-xxxx"
}
```

---

## 📝 CONFIGURACIÓN DE TIPOS DE DOCUMENTO

### Archivo: `document_types.json`

Este archivo define todos los tipos de documentos y sus campos.

#### Estructura General:
```json
{
  "tipos_documentos": {
    "CODIGO-DOC": {
      "nombre": "Nombre Descriptivo",
      "descripcion": "Descripción del documento",
      "activo": true,
      "requiere_qr": false,
      "campos": [
        {
          "id": "nombre_campo",
          "label": "Etiqueta en UI",
          "tipo": "text|number|date|select|textarea|checkbox",
          "requerido": true|false,
          "validacion": "regex_pattern",
          "mensaje_error": "Mensaje si falla validación",
          "placeholder": "Texto de ayuda",
          "orden": 1,
          "ancho": "full|half|third",
          "opciones": ["Op1", "Op2"],  // Solo para tipo 'select'
          "filas": 3,                  // Solo para tipo 'textarea'
          "min": 0,                    // Solo para tipo 'number'
          "max": 999999                // Solo para tipo 'number'
        }
      ]
    }
  }
}
```

#### Tipos de Campo Soportados:

| Tipo | Descripción | Widget UI |
|------|-------------|-----------|
| `text` | Texto simple | Entry |
| `number` | Números | Spinbox |
| `date` | Fechas | DateEntry |
| `select` | Lista opciones | Combobox |
| `textarea` | Texto largo | Text (multilinea) |
| `checkbox` | Sí/No | Checkbutton |

#### Ejemplo Real: GCO-REG-009

```json
{
  "tipos_documentos": {
    "GCO-REG-009": {
      "nombre": "Acta de Registro General",
      "activo": true,
      "requiere_qr": false,
      "campos": [
        {
          "id": "cedula",
          "label": "Número de Cédula",
          "tipo": "text",
          "requerido": true,
          "validacion": "^[0-9]{6,12}$",
          "orden": 1,
          "ancho": "full"
        },
        {
          "id": "nombre_completo",
          "label": "Nombre Completo",
          "tipo": "text",
          "requerido": true,
          "orden": 2,
          "ancho": "full"
        },
        {
          "id": "fecha_documento",
          "label": "Fecha del Documento",
          "tipo": "date",
          "requerido": true,
          "orden": 3,
          "ancho": "half"
        },
        {
          "id": "tipo_tramite",
          "label": "Tipo de Trámite",
          "tipo": "select",
          "requerido": true,
          "opciones": [
            "Registro inicial",
            "Actualización",
            "Renovación",
            "Cancelación"
          ],
          "orden": 4,
          "ancho": "half"
        },
        {
          "id": "observaciones",
          "label": "Observaciones",
          "tipo": "textarea",
          "requerido": false,
          "orden": 5,
          "ancho": "full",
          "filas": 3
        }
      ]
    }
  }
}
```

**IMPORTANTE**: Estos campos son provisionales para el prototipo. Más adelante se proporcionarán los campos reales que necesita el GCO-REG-009.

---

## 🔄 FLUJO DE TRABAJO MODIFICADO

### 1. Inicio de la Aplicación

```python
# main.py
1. Cargar config.json (credenciales Azure)
2. Inicializar OneDriveManager
   - Autenticar con Microsoft
   - Verificar/crear carpeta "Documentos_SGD"
3. Inicializar DatabaseManager
   - Conectar a sgd_database.db
   - Crear tablas si no existen
4. Cargar tipos de documento desde document_types.json
5. Mostrar menú principal
```

### 2. Registro de Documentos (Modificado)

```
Usuario → Selecciona archivos/carpeta
    ↓
Sistema → Para cada archivo:
    ├─ Intentar leer QR (NO falla si no hay)
    │  ├─ QR encontrado → Guardar código, tiene_qr = True
    │  └─ QR no encontrado → tiene_qr = False, continuar
    ↓
Sistema → Mostrar vista previa del documento
    ├─ Indicador QR: ✓ "QR: uuid-xxxx" o ✗ "Sin QR"
    ↓
Usuario → Seleccionar tipo de documento (Dropdown)
    ↓
Sistema → Cargar campos desde document_types.json
    └─ Generar formulario dinámicamente según configuración
    ↓
Usuario → Llenar campos manualmente (leyendo el documento)
    ↓
Usuario → Click en "Relacionar/Guardar"
    ↓
Sistema → Validar campos según reglas en JSON
    ├─ Validación falla → Mostrar errores
    └─ Validación OK → Continuar
    ↓
Sistema → Generar nombre de archivo: {tipo}_{cedula}_{timestamp}.ext
    ↓
Sistema → Subir archivo a OneDrive
    └─ Agregar metadatos al archivo (campos como JSON)
    ↓
Sistema → Guardar en base de datos:
    ├─ Registro en tabla 'documentos'
    └─ Campos en tabla 'documento_campos'
    ↓
Sistema → Pasar al siguiente documento o finalizar
```

### 3. Búsqueda de Documentos (Modificado)

```
Usuario → Ingresa término de búsqueda
    ├─ Opción 1: Buscar por campo específico (ej: cédula)
    └─ Opción 2: Búsqueda general (todos los campos)
    ↓
Sistema → Consultar base de datos SQLite
    └─ Buscar en tabla 'documentos' y 'documento_campos'
    ↓
Sistema → Mostrar resultados en tabla
    ├─ Fecha de registro
    ├─ Tipo de documento
    ├─ Nombre de archivo
    ├─ Campos principales (cédula, nombre, etc.)
    ├─ Indicador QR (✓/✗)
    └─ Botón vista previa
    ↓
Usuario → Seleccionar documentos
    ↓
Usuario → Descargar
    ↓
Sistema → Descargar desde OneDrive a carpeta local
```

---

## 🔧 COMPONENTES YA IMPLEMENTADOS

Los siguientes componentes **YA ESTÁN CREADOS Y LISTOS** (revisar archivos en el directorio):

### ✅ `onedrive_manager.py`
**Funcionalidades:**
- Autenticación con Microsoft Graph API usando MSAL
- Manejo de tokens (cache en `token.json`)
- Crear/verificar carpeta en OneDrive
- Subir archivos (pequeños y grandes con chunking)
- Descargar archivos
- Agregar metadatos personalizados
- Listar archivos
- Eliminar archivos

**Métodos principales:**
```python
OneDriveManager(config_path='config.json')
setup_folder() -> str
upload_file(file_path, remote_filename, metadata=None) -> dict
download_file(file_id, destination_path) -> bool
get_file_metadata(file_id) -> dict
list_files(folder_id=None) -> list
```

### ✅ `database_manager.py`
**Funcionalidades:**
- Conexión a SQLite
- Creación automática de tablas
- CRUD completo para documentos
- Sistema de campos dinámicos
- Búsquedas avanzadas (por campo, tipo, fecha, QR)
- Historial de cambios (auditoría)
- Estadísticas

**Métodos principales:**
```python
DatabaseManager(db_path='sgd_database.db')
add_document(tipo_documento, archivo_onedrive_id, archivo_nombre,
             archivo_url, qr_code=None, campos=None) -> int
search_documents(search_term=None, search_field=None,
                tipo_documento=None, tiene_qr=None) -> list
get_document_by_id(documento_id) -> dict
get_document_by_qr(qr_code) -> dict
update_document(documento_id, campos=None) -> bool
```

### ✅ `document_types.json`
**Estado:**
- Estructura completa definida
- Incluye ejemplo de GCO-REG-009 con 5 campos
- Incluye documento de ejemplo con todos los tipos de campo
- Validaciones predefinidas comunes

### ✅ Documentación
- `AZURE_SETUP_GUIDE.md` - Guía paso a paso de configuración de Azure AD
- `MIGRACION_ONEDRIVE.md` - Guía de migración desde Google Drive
- `config.example.json` - Plantilla de configuración

### ✅ Configuración
- `.gitignore` actualizado (protege config.json, token.json, *.db)
- `requirements_new.txt` con dependencias actualizadas

---

## 🔨 TRABAJO PENDIENTE

### 1. Modificar `document_register.py`

#### Cambios necesarios:

**a) QR Opcional (Método `process_files`):**
```python
# ACTUAL (línea 446-454):
qr_content = self.read_qr_code(file_path)
if qr_content is None:
    messagebox.showerror("Error", f"No se pudo leer el código QR...")
    continue

# MODIFICAR A:
qr_content = self.read_qr_code(file_path)
tiene_qr = qr_content is not None

# Guardar estado del QR para mostrar después
if not hasattr(self, 'qr_contents'):
    self.qr_contents = {}
self.qr_contents[file_path] = {
    'code': qr_content,
    'tiene_qr': tiene_qr
}

# CONTINUAR sin error (no usar continue)
```

**b) Indicador Visual de QR (Método `setup_register_window`):**

Agregar después de la línea 278 (después del label de instrucciones):

```python
# Indicador de estado del QR
self.qr_status_frame = ttk.Frame(input_frame)
self.qr_status_frame.pack(pady=(0, 10))

self.qr_status_label = ttk.Label(
    self.qr_status_frame,
    text="",
    font=("Segoe UI", 10)
)
self.qr_status_label.pack()
```

**c) Actualizar indicador en `load_document_preview`:**

Agregar al final del método (después de línea 599):

```python
# Actualizar indicador de QR
current_file = self.uploaded_files[self.current_doc_index]
qr_info = self.qr_contents.get(current_file, {})

if qr_info.get('tiene_qr'):
    qr_code = qr_info.get('code')
    self.qr_status_label.config(
        text=f"✓ QR detectado: {qr_code[:20]}...",
        foreground="green"
    )
else:
    self.qr_status_label.config(
        text="✗ Sin código QR",
        foreground="orange"
    )
```

**d) Reemplazar GoogleDriveManager por OneDriveManager:**

```python
# En los imports (línea 22-25):
# ELIMINAR:
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# AGREGAR:
from onedrive_manager import OneDriveManager
from database_manager import DatabaseManager

# En __init__ (línea 38-39):
# CAMBIAR de:
self.drive_manager = drive_manager

# A:
self.onedrive_manager = onedrive_manager
self.database_manager = database_manager
```

**e) Modificar método `store_document` (línea 1179-1231):**

```python
def store_document(self, file_path, qr_content, formato, campos):
    """
    Almacena documento en OneDrive y registra en base de datos.

    Args:
        file_path: Ruta del archivo local
        qr_content: Código QR (puede ser None)
        formato: Tipo de documento (ej: "GCO-REG-009")
        campos: Dict con campos adicionales {campo_nombre: valor}
    """
    try:
        # Obtener identificador principal (cédula u otro)
        identificador = campos.get('cedula', 'sin_id')

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_ext = os.path.splitext(file_path)[1]
        remote_filename = f"{formato}_{identificador}_{timestamp}{file_ext}"

        # Preparar metadatos para OneDrive
        metadata = {
            'tipo_documento': formato,
            'qr_code': qr_content,
            'tiene_qr': qr_content is not None,
            **campos  # Incluir todos los campos
        }

        # Subir a OneDrive
        file_info = self.onedrive_manager.upload_file(
            file_path=file_path,
            remote_filename=remote_filename,
            metadata=metadata
        )

        if not file_info:
            raise Exception("Error al subir archivo a OneDrive")

        # Registrar en base de datos
        documento_id = self.database_manager.add_document(
            tipo_documento=formato,
            archivo_onedrive_id=file_info['id'],
            archivo_nombre=file_info['name'],
            archivo_url=file_info['webUrl'],
            qr_code=qr_content,
            campos=campos
        )

        print(f"✓ Documento registrado con ID: {documento_id}")
        return documento_id

    except Exception as e:
        print(f"Error al almacenar documento: {str(e)}")
        raise
```

**f) Implementar Campos Dinámicos:**

Agregar método para cargar configuración de tipo de documento:

```python
def load_document_type_fields(self, tipo_documento):
    """Carga los campos definidos para un tipo de documento"""
    try:
        with open('document_types.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        tipo_config = config['tipos_documentos'].get(tipo_documento)

        if not tipo_config:
            raise Exception(f"Tipo de documento no encontrado: {tipo_documento}")

        return tipo_config

    except Exception as e:
        print(f"Error al cargar configuración de tipo: {e}")
        return None
```

Modificar `setup_register_window` para generar campos dinámicamente:

```python
# Después del ComboBox de formato (línea 310):

# Vincular cambio de tipo de documento
self.format_combo.bind('<<ComboboxSelected>>', self.on_document_type_change)

# Frame para campos dinámicos
self.dynamic_fields_frame = ttk.Frame(input_frame)
self.dynamic_fields_frame.pack(pady=(10, 0), fill=X)

self.field_widgets = {}  # Diccionario para almacenar widgets de campos

# Método para generar campos dinámicamente:
def on_document_type_change(self, event=None):
    """Genera campos dinámicos según el tipo de documento seleccionado"""

    # Limpiar campos anteriores
    for widget in self.dynamic_fields_frame.winfo_children():
        widget.destroy()
    self.field_widgets.clear()

    # Obtener tipo seleccionado
    tipo_documento = self.format_var.get()

    if tipo_documento == "Otro":
        # Mostrar entry para tipo manual
        return

    # Cargar configuración del tipo
    tipo_config = self.load_document_type_fields(tipo_documento)

    if not tipo_config:
        return

    # Generar campos según configuración
    campos = sorted(tipo_config['campos'], key=lambda x: x.get('orden', 999))

    for campo in campos:
        campo_id = campo['id']
        campo_label = campo['label']
        campo_tipo = campo['tipo']
        requerido = campo.get('requerido', False)

        # Frame para el campo
        field_frame = ttk.Frame(self.dynamic_fields_frame)
        field_frame.pack(fill=X, pady=5)

        # Label
        label_text = f"{campo_label}{'*' if requerido else ''}:"
        ttk.Label(field_frame, text=label_text).pack(anchor=W)

        # Widget según tipo
        if campo_tipo == 'text':
            widget = ttk.Entry(field_frame)
            if 'placeholder' in campo:
                # Agregar placeholder como watermark
                pass

        elif campo_tipo == 'number':
            widget = ttk.Spinbox(
                field_frame,
                from_=campo.get('min', 0),
                to=campo.get('max', 999999)
            )

        elif campo_tipo == 'date':
            # Usar DateEntry de ttkbootstrap
            widget = ttk.DateEntry(field_frame)

        elif campo_tipo == 'select':
            widget = ttk.Combobox(
                field_frame,
                values=campo.get('opciones', []),
                state='readonly'
            )

        elif campo_tipo == 'textarea':
            widget = tk.Text(
                field_frame,
                height=campo.get('filas', 3),
                width=40
            )

        elif campo_tipo == 'checkbox':
            var = tk.BooleanVar()
            widget = ttk.Checkbutton(field_frame, variable=var)
            widget.var = var

        widget.pack(fill=X)

        # Guardar referencia
        self.field_widgets[campo_id] = {
            'widget': widget,
            'config': campo
        }
```

**g) Modificar `relacionar_documento` para capturar campos:**

```python
def relacionar_documento(self):
    """Procesar la relación del documento con sus campos"""

    if self.is_processing:
        return

    try:
        self.is_processing = True

        # Obtener tipo de documento
        formato = self.format_var.get()

        if formato == "Otro":
            formato = self.custom_format_var.get().strip()
            if not formato:
                messagebox.showwarning("Advertencia", "Ingrese un formato válido")
                return

        # Recolectar valores de campos dinámicos
        campos = {}
        errores = []

        for campo_id, field_info in self.field_widgets.items():
            widget = field_info['widget']
            config = field_info['config']

            # Obtener valor según tipo de widget
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Spinbox):
                valor = widget.get().strip()
            elif isinstance(widget, ttk.Combobox):
                valor = widget.get()
            elif isinstance(widget, tk.Text):
                valor = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, ttk.Checkbutton):
                valor = widget.var.get()
            elif hasattr(widget, 'entry'):  # DateEntry
                valor = widget.entry.get()
            else:
                valor = ""

            # Validar campo requerido
            if config.get('requerido') and not valor:
                errores.append(f"{config['label']} es obligatorio")
                continue

            # Validar con regex si existe
            if valor and 'validacion' in config:
                import re
                if not re.match(config['validacion'], str(valor)):
                    mensaje = config.get('mensaje_error', f"{config['label']} no es válido")
                    errores.append(mensaje)
                    continue

            campos[campo_id] = valor

        # Mostrar errores si existen
        if errores:
            messagebox.showerror("Errores de Validación", "\n".join(errores))
            return

        # Almacenar documento
        current_file = self.uploaded_files[self.current_doc_index]
        qr_info = self.qr_contents[current_file]
        qr_code = qr_info.get('code')

        documento_id = self.store_document(
            file_path=current_file,
            qr_content=qr_code,
            formato=formato,
            campos=campos
        )

        messagebox.showinfo("Éxito", f"Documento registrado exitosamente (ID: {documento_id})")

        # Limpiar y pasar al siguiente
        self.current_doc_index += 1

        if self.current_doc_index < len(self.uploaded_files):
            self.load_document_preview()
        else:
            messagebox.showinfo("Completado", "Todos los documentos han sido procesados")
            # Cerrar ventana de registro

    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar documento: {str(e)}")
    finally:
        self.is_processing = False
```

**h) Eliminar la clase `GoogleDriveManager`:**

Eliminar toda la clase desde la línea 1258 hasta el final (línea 1644).

### 2. Modificar `document_search.py`

#### Cambios necesarios:

**a) Reemplazar imports y managers:**

```python
# En imports (línea 5-6):
# ELIMINAR:
from document_register import GoogleDriveManager

# AGREGAR:
from onedrive_manager import OneDriveManager
from database_manager import DatabaseManager

# En __init__ (línea 24-25):
# CAMBIAR:
self.drive_manager = drive_manager

# A:
self.onedrive_manager = onedrive_manager
self.database_manager = database_manager
```

**b) Modificar método `search_documents` (línea 232-294):**

```python
def search_documents(self, search_term, search_type='cedula'):
    """
    Busca documentos en la base de datos SQLite.

    Args:
        search_term: Término a buscar
        search_type: Tipo de búsqueda ('cedula' o 'nombre')

    Returns:
        Lista de documentos encontrados
    """
    if not self.database_manager:
        messagebox.showerror("Error", "No hay conexión con la base de datos")
        return []

    try:
        # Buscar en base de datos
        if search_type == 'cedula':
            results = self.database_manager.search_documents(
                search_term=search_term,
                search_field='cedula'
            )
        else:
            # Búsqueda general en todos los campos
            results = self.database_manager.search_documents(
                search_term=search_term
            )

        return results

    except Exception as e:
        print(f"Error al buscar documentos: {str(e)}")
        messagebox.showerror("Error", f"Error al buscar documentos: {str(e)}")
        return []
```

**c) Modificar `display_results` (línea 296-337):**

```python
def display_results(self, results):
    """Muestra los resultados de la búsqueda"""
    # Limpiar resultados anteriores
    for item in self.results_tree.get_children():
        self.results_tree.delete(item)

    if not results:
        messagebox.showinfo("Búsqueda", "No se encontraron documentos")
        return

    for doc in results:
        try:
            # Obtener campos del documento
            campos = doc.get('campos', {})
            cedula = campos.get('cedula', 'N/A')
            nombre = campos.get('nombre_completo', 'N/A')

            # Indicador de QR
            qr_indicator = "✓" if doc.get('tiene_qr') else "✗"

            self.results_tree.insert(
                '',
                'end',
                values=(
                    "",  # Checkbox
                    doc['fecha_registro'],
                    doc['archivo_nombre'],
                    cedula,
                    qr_indicator
                ),
                tags=(doc['id'],)  # Guardar ID en tags
            )

        except Exception as e:
            print(f"Error al mostrar resultado: {str(e)}")
            continue

    self.last_search_results = results
```

**d) Modificar `download_selected_documents`:**

```python
def download_selected_documents(self):
    """Descarga documentos seleccionados desde OneDrive"""

    if not self.onedrive_manager:
        messagebox.showerror("Error", "No hay conexión con OneDrive")
        return

    selected_docs = []

    for item in self.results_tree.get_children():
        values = self.results_tree.item(item)['values']
        if values[0] == "✓":
            doc_id = int(self.results_tree.item(item)['tags'][0])

            # Buscar documento en resultados
            for doc in self.last_search_results:
                if doc['id'] == doc_id:
                    selected_docs.append(doc)
                    break

    if not selected_docs:
        messagebox.showwarning("Advertencia", "Seleccione documentos para descargar")
        return

    download_dir = filedialog.askdirectory(title="Seleccione carpeta de descarga")
    if not download_dir:
        return

    try:
        progress_window = ttk.Toplevel(self.window)
        progress_window.title("Descargando")
        progress_window.geometry("300x150")

        progress_frame = ttk.Frame(progress_window, padding=20)
        progress_frame.pack(fill=BOTH, expand=YES)

        progress_label = ttk.Label(
            progress_frame,
            text="Descargando documentos...",
            wraplength=250
        )
        progress_label.pack(pady=(0, 10))

        progress_bar = ttk.Progressbar(
            progress_frame,
            length=200,
            mode='determinate'
        )
        progress_bar.pack()

        total = len(selected_docs)
        successful = 0

        for i, doc in enumerate(selected_docs, 1):
            progress = (i / total) * 100
            progress_bar['value'] = progress
            progress_label.config(text=f"Descargando {i} de {total}")
            progress_window.update()

            try:
                if self.onedrive_manager.download_file(
                    doc['archivo_onedrive_id'],
                    download_dir
                ):
                    successful += 1
            except Exception as e:
                print(f"Error al descargar {doc['archivo_nombre']}: {e}")
                continue

        progress_window.destroy()

        messagebox.showinfo(
            "Éxito",
            f"Se descargaron {successful} de {total} documentos en {download_dir}"
        )

    except Exception as e:
        if 'progress_window' in locals():
            progress_window.destroy()
        messagebox.showerror("Error", f"Error al descargar documentos: {str(e)}")
```

**e) Modificar vista previa para usar OneDrive:**

```python
def load_preview(self, canvas, file_id):
    """Carga vista previa desde OneDrive"""
    try:
        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2,
            text="Cargando vista previa...",
            font=("Segoe UI", 12)
        )
        canvas.update()

        # Descargar temporalmente
        import tempfile
        temp_dir = tempfile.gettempdir()

        # Usar OneDriveManager para descargar
        success = self.onedrive_manager.download_file(file_id, temp_dir)

        if not success:
            raise Exception("No se pudo descargar el archivo")

        # Obtener metadata para saber el nombre del archivo
        file_info = self.onedrive_manager.get_file_metadata(file_id)
        temp_file = os.path.join(temp_dir, file_info['name'])

        if not os.path.exists(temp_file):
            raise Exception("No se encuentra el archivo descargado")

        # Cargar vista previa según tipo
        if temp_file.lower().endswith('.pdf'):
            doc = fitz.open(temp_file)
            page = doc[0]
            zoom_matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=zoom_matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
        else:
            img = Image.open(temp_file)

        # Guardar imagen original
        self.current_image = img
        self.original_image_size = img.size

        # Ajustar al canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        img_copy = img.copy()
        img_copy.thumbnail((canvas_width, canvas_height))

        # Mostrar
        photo = ImageTk.PhotoImage(img_copy)
        canvas.delete("all")
        canvas.create_image(
            canvas_width//2,
            canvas_height//2,
            image=photo,
            anchor="center"
        )
        canvas.image = photo

        # Limpiar archivo temporal
        try:
            os.remove(temp_file)
        except:
            pass

    except Exception as e:
        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2,
            text=f"Error: {str(e)}",
            font=("Segoe UI", 12),
            fill="red"
        )
```

### 3. Modificar `main.py`

#### Cambios necesarios:

```python
# En imports (línea 5-6):
# ELIMINAR:
from document_register import DocumentRegisterSystem, GoogleDriveManager

# AGREGAR:
from document_register import DocumentRegisterSystem
from onedrive_manager import OneDriveManager
from database_manager import DatabaseManager
import json

# Modificar __init__ (línea 12-81):
class SistemaGestionDocumental:
    def __init__(self):
        """Inicializa la ventana principal del sistema"""
        # Crear ventana principal
        self.root = ttk.Window(themename="flatly")
        self.root.withdraw()

        # Ventana de carga
        loading_window = ttk.Toplevel(self.root)
        loading_window.title("Conectando")
        loading_window.geometry("300x150")

        screen_width = loading_window.winfo_screenwidth()
        screen_height = loading_window.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        loading_window.geometry(f"+{x}+{y}")

        loading_frame = ttk.Frame(loading_window, padding=20)
        loading_frame.pack(fill=BOTH, expand=YES)

        ttk.Label(
            loading_frame,
            text="Iniciando sistema...",
            font=("Segoe UI", 11),
            wraplength=250
        ).pack(pady=(0, 15))

        progress = ttk.Progressbar(
            loading_frame,
            mode='indeterminate',
            length=200
        )
        progress.pack()
        progress.start(15)

        loading_window.update()

        try:
            # Cargar configuración
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            # Inicializar OneDrive
            loading_frame.winfo_children()[0].config(text="Conectando con OneDrive...")
            loading_window.update()

            self.onedrive_manager = OneDriveManager('config.json')
            self.onedrive_manager.setup_folder()

            # Inicializar Base de Datos
            loading_frame.winfo_children()[0].config(text="Inicializando base de datos...")
            loading_window.update()

            db_path = self.config['database']['path']
            self.database_manager = DatabaseManager(db_path)

            # Cargar tipos de documento
            loading_frame.winfo_children()[0].config(text="Cargando tipos de documento...")
            loading_window.update()

            self._load_document_types()

            # Configurar ventana principal
            self.root.title("Sistema de Gestión Documental")
            window_width = 800
            window_height = 600
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
            self.root.minsize(800, 600)

            loading_window.destroy()
            self.root.deiconify()

            self.setup_main_menu()

        except FileNotFoundError as e:
            loading_window.destroy()
            self.root.destroy()
            messagebox.showerror(
                "Error de Configuración",
                "No se encontró el archivo config.json\n\n"
                "Por favor, crea el archivo desde config.example.json\n"
                "y completa las credenciales de Azure."
            )
            sys.exit(1)

        except Exception as e:
            loading_window.destroy()
            self.root.destroy()
            messagebox.showerror(
                "Error de Conexión",
                f"Error al inicializar el sistema: {str(e)}"
            )
            sys.exit(1)

    def _load_document_types(self):
        """Carga tipos de documento desde JSON a la base de datos"""
        try:
            with open('document_types.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            tipos = config['tipos_documentos']

            for codigo, tipo_config in tipos.items():
                # Verificar si ya existe en DB
                existing = self.database_manager.get_document_type_definition(codigo)

                if not existing:
                    # Agregar a base de datos
                    self.database_manager.add_document_type(
                        codigo=codigo,
                        nombre=tipo_config['nombre'],
                        definicion=tipo_config,
                        descripcion=tipo_config.get('descripcion')
                    )
                    print(f"✓ Tipo de documento cargado: {codigo}")

        except Exception as e:
            print(f"Error al cargar tipos de documento: {e}")

# Modificar métodos open_* para pasar ambos managers:
def open_generator(self):
    print("generador accedido")
    generator = DocumentGenerator(
        parent=self.root,
        onedrive_manager=self.onedrive_manager,
        database_manager=self.database_manager
    )

def open_register(self):
    print("registrador accedido")
    register = DocumentRegisterSystem(
        parent=self.root,
        onedrive_manager=self.onedrive_manager,
        database_manager=self.database_manager
    )

def open_search(self):
    print("Buscador accedido")
    search = DocumentSearch(
        parent=self.root,
        onedrive_manager=self.onedrive_manager,
        database_manager=self.database_manager
    )
```

### 4. Actualizar `document_generator.py`

**Nota**: Este módulo puede mantener Google Drive por ahora o actualizarse después. Si se decide actualizar:

```python
# Cambiar para que también use OneDrive + Database
# Similar a los cambios en document_register.py
# El método add_qr_record cambiaría a:

self.database_manager.add_document(
    tipo_documento=formato,
    archivo_onedrive_id="generated",  # O el ID si se sube a OneDrive
    archivo_nombre=f"acta_{i}.docx",
    archivo_url="local",
    qr_code=uuid_texto,
    campos={'formato': formato}
)
```

---

## 🧪 TESTING Y VALIDACIÓN

### Pruebas Esenciales

1. **Autenticación**:
   - Primera ejecución debe abrir navegador
   - Autenticación exitosa debe guardar token
   - Siguientes ejecuciones deben usar token guardado

2. **QR Opcional**:
   - Documentos CON QR → Detectar y mostrar código
   - Documentos SIN QR → Mostrar "Sin QR" y permitir continuar
   - No deben haber errores/bloqueos por falta de QR

3. **Campos Dinámicos**:
   - Seleccionar tipo de documento → Mostrar campos correspondientes
   - Campos requeridos → No permitir guardar si están vacíos
   - Validaciones → Rechazar datos inválidos con mensaje claro
   - Guardar → Datos deben aparecer en búsqueda

4. **OneDrive**:
   - Subir archivo → Verificar que aparece en carpeta OneDrive
   - Descargar archivo → Debe descargarse correctamente
   - Metadatos → Verificar que se guardan con el archivo

5. **Base de Datos**:
   - Buscar por cédula → Encontrar documentos
   - Búsqueda general → Buscar en todos los campos
   - Estadísticas → Mostrar conteos correctos

---

## 📚 RECURSOS Y REFERENCIAS

### Documentación API
- **Microsoft Graph API**: https://docs.microsoft.com/en-us/graph/api/overview
- **MSAL Python**: https://github.com/AzureAD/microsoft-authentication-library-for-python
- **SQLite Python**: https://docs.python.org/3/library/sqlite3.html

### Dependencias Clave
```
msal==1.31.1              # Autenticación Microsoft
msal-extensions==1.2.0    # Extensiones para cache de tokens
requests==2.32.3          # HTTP client
ttkbootstrap==1.13.8      # UI moderna
PyMuPDF==1.26.0          # Procesamiento PDF
opencv-python==4.11.0.86  # Procesamiento imágenes
pyzbar==0.1.9            # Lectura QR
python-docx==1.1.2       # Generación documentos
Pillow==10.4.0           # Imágenes
```

### Estructura de Archivos del Proyecto

```
SGD_desktop/
├── main.py                          # Entrada principal
├── document_generator.py            # Generación documentos con QR
├── document_register.py             # Registro documentos (MODIFICAR)
├── document_search.py               # Búsqueda documentos (MODIFICAR)
│
├── onedrive_manager.py              # ✨ Gestor OneDrive (NUEVO - LISTO)
├── database_manager.py              # ✨ Gestor SQLite (NUEVO - LISTO)
│
├── config.json                      # Configuración (crear desde example)
├── config.example.json              # Plantilla (LISTO)
├── document_types.json              # Tipos de documentos (LISTO)
│
├── sgd_database.db                  # Base de datos (se crea automáticamente)
├── token.json                       # Token OneDrive (se crea automáticamente)
│
├── plantilla.docx                   # Plantilla para generar documentos
├── Logo.jpg                         # Logo de la aplicación
│
├── requirements.txt                 # Dependencias actuales
├── requirements_new.txt             # Dependencias actualizadas (LISTO)
│
├── .gitignore                       # Archivos ignorados (ACTUALIZADO)
│
├── README.md                        # Documentación original
├── AZURE_SETUP_GUIDE.md            # ✨ Guía configuración Azure (NUEVO - LISTO)
├── MIGRACION_ONEDRIVE.md           # ✨ Guía migración (NUEVO - LISTO)
└── PROJECT_BRIEF.md                # ✨ Este documento (NUEVO - LISTO)
```

---

## 🎯 PRIORIDADES Y ORDEN DE IMPLEMENTACIÓN

### Fase 1: Infraestructura (✅ COMPLETADA)
- [x] Crear OneDriveManager
- [x] Crear DatabaseManager
- [x] Crear document_types.json
- [x] Actualizar .gitignore
- [x] Crear documentación

### Fase 2: Migración Core (⏳ PENDIENTE)
- [ ] Modificar main.py (inicialización)
- [ ] Modificar document_register.py (QR opcional + campos dinámicos + OneDrive)
- [ ] Modificar document_search.py (búsqueda en SQLite)

### Fase 3: Campos Dinámicos (⏳ PENDIENTE)
- [ ] Implementar generación dinámica de formulario
- [ ] Implementar validaciones de campos
- [ ] Implementar recolección de datos
- [ ] Guardar en DB y metadatos

### Fase 4: Testing y Refinamiento (⏳ PENDIENTE)
- [ ] Pruebas de autenticación
- [ ] Pruebas de QR opcional
- [ ] Pruebas de campos dinámicos
- [ ] Pruebas de búsqueda
- [ ] Ajustes UX

---

## 💡 CONSIDERACIONES IMPORTANTES

### Sobre el Prototipo
Este es un **prototipo de transición**. Existe un plan para migrar todo a una aplicación web con arquitectura moderna. Por lo tanto:
- No es necesario sobre-optimizar
- Priorizar funcionalidad sobre perfección
- El código debe ser **legible y mantenible** para facilitar la migración futura

### Sobre los Campos del GCO-REG-009
Los campos en `document_types.json` son **provisionales**. El usuario proporcionará más adelante la estructura exacta del documento GCO-REG-009 con todos sus campos reales.

### Sobre la Migración a Web
Cuando se migre a web, esta arquitectura ayudará porque:
- SQLite → PostgreSQL es casi directo
- OneDriveManager puede reemplazarse con servicio de storage cloud
- La lógica de campos dinámicos se reutiliza
- El JSON de tipos de documento se mantiene igual

### Sobre la Escalabilidad
Por ahora, el sistema es monousuario (escritorio). En la versión web se agregará:
- Multi-usuario con autenticación
- Control de permisos por roles
- API REST
- Frontend moderno (React/Vue)
- Base de datos centralizada

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error: "No se encontró config.json"
**Causa**: No se creó el archivo de configuración.
**Solución**: Copiar `config.example.json` a `config.json` y completar credenciales.

### Error de autenticación Microsoft
**Causa**: Permisos no configurados o credenciales incorrectas.
**Solución**: Revisar `AZURE_SETUP_GUIDE.md` y verificar:
- Client ID, Secret y Tenant ID correctos
- Permisos de API configurados
- "Grant admin consent" habilitado

### Error: "Database is locked"
**Causa**: Otra conexión tiene la BD abierta.
**Solución**: Cerrar todas las instancias de la aplicación y reiniciar.

### Documentos no aparecen en búsqueda
**Causa**: No se guardaron correctamente en la base de datos.
**Solución**: Verificar que `database_manager.add_document()` se ejecuta sin errores.

### QR no se detecta en documentos válidos
**Causa**: Calidad del escaneo o configuración de pyzbar.
**Solución**: Aumentar el factor de zoom en la conversión PDF a imagen (línea 1063 en document_register.py).

---

## 📞 SIGUIENTE PASO

Para continuar con la implementación:

1. **Configurar Azure AD** siguiendo `AZURE_SETUP_GUIDE.md`
2. **Crear config.json** desde `config.example.json`
3. **Instalar dependencias**: `pip install -r requirements_new.txt`
4. **Probar managers**:
   ```bash
   python onedrive_manager.py
   python database_manager.py
   ```
5. **Comenzar migraciones** siguiendo la sección "TRABAJO PENDIENTE"

---

## 📝 NOTAS FINALES

Este documento debe servir como **especificación completa** del proyecto para cualquier desarrollador (humano o IA) que continúe el trabajo.

Si alguna sección no es clara o falta información, consultar:
- El código existente en los archivos `.py`
- La documentación en los archivos `.md`
- Los comentarios en el código
- El historial de Git

**Última actualización**: 2025-01-09
**Versión del documento**: 1.0
**Estado del proyecto**: Infraestructura completa, pendiente migración de módulos principales
