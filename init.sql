-- SQL initialization script for SGD Web
-- Creates base tables for users, document types, qr codes and documents

-- =========================
-- ENUM TYPES
-- =========================
CREATE TYPE userrole AS ENUM ('admin', 'operator', 'viewer');
CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'pending', 'suspended');

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    azure_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    given_name VARCHAR(100),
    surname VARCHAR(100),
    display_name VARCHAR(200),
    department VARCHAR(100),
    job_title VARCHAR(100),
    office_location VARCHAR(100),
    company_name VARCHAR(100),
    role userrole NOT NULL DEFAULT 'viewer',
    status userstatus NOT NULL DEFAULT 'pending',
    preferred_language VARCHAR(10) DEFAULT 'es',
    timezone VARCHAR(50) DEFAULT 'America/Bogota',
    email_notifications BOOLEAN DEFAULT TRUE,
    theme_preference VARCHAR(20) DEFAULT 'light',
    first_login TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    last_token_issued TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    documents_uploaded INTEGER DEFAULT 0,
    documents_generated INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    admin_notes TEXT,
    phone VARCHAR(20),
    mobile_phone VARCHAR(20)
);

CREATE INDEX idx_users_azure_id ON users(azure_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_is_active ON users(is_active);

-- =========================
-- DOCUMENT TYPES TABLE
-- =========================
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    requires_qr BOOLEAN NOT NULL DEFAULT FALSE,
    requires_cedula BOOLEAN NOT NULL DEFAULT TRUE,
    requires_nombre BOOLEAN NOT NULL DEFAULT FALSE,
    requires_telefono BOOLEAN NOT NULL DEFAULT FALSE,
    requires_email BOOLEAN NOT NULL DEFAULT FALSE,
    requires_direccion BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_file_types TEXT,
    max_file_size_mb INTEGER DEFAULT 50,
    allow_multiple_files BOOLEAN DEFAULT FALSE,
    template_path VARCHAR(255),
    qr_table_number INTEGER DEFAULT 1,
    qr_row INTEGER DEFAULT 5,
    qr_column INTEGER DEFAULT 0,
    qr_width INTEGER DEFAULT 1,
    qr_height INTEGER DEFAULT 1,
    color VARCHAR(7) DEFAULT '#007bff',
    icon VARCHAR(50) DEFAULT 'file',
    sort_order INTEGER DEFAULT 0,
    requires_approval BOOLEAN DEFAULT FALSE,
    auto_notify_email BOOLEAN DEFAULT FALSE,
    notification_emails TEXT,
    retention_days INTEGER,
    auto_archive BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system_type BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    documents_count INTEGER DEFAULT 0,
    generated_count INTEGER DEFAULT 0
);

CREATE INDEX idx_document_types_code ON document_types(code);
CREATE INDEX idx_document_types_is_active ON document_types(is_active);

-- =========================
-- QR CODES TABLE
-- =========================
CREATE TABLE qr_codes (
    id SERIAL PRIMARY KEY,
    qr_id VARCHAR(255) NOT NULL UNIQUE,
    document_type_id INTEGER NOT NULL REFERENCES document_types(id),
    qr_data TEXT,
    qr_version INTEGER DEFAULT 1,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    is_expired BOOLEAN NOT NULL DEFAULT FALSE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    used_in_document_id INTEGER REFERENCES documents(id),
    generated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    used_at TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    generation_config JSONB,
    source_file_path VARCHAR(500),
    source_file_name VARCHAR(255),
    usage_attempts INTEGER DEFAULT 0,
    usage_log JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX idx_qr_codes_qr_id ON qr_codes(qr_id);
CREATE INDEX idx_qr_codes_document_type ON qr_codes(document_type_id);
CREATE INDEX idx_qr_codes_is_used ON qr_codes(is_used);
CREATE INDEX idx_qr_codes_is_expired ON qr_codes(is_expired);
CREATE INDEX idx_qr_codes_is_revoked ON qr_codes(is_revoked);
CREATE INDEX idx_qr_codes_used_in_document ON qr_codes(used_in_document_id);

-- =========================
-- DOCUMENTS TABLE
-- =========================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    qr_code_id VARCHAR(255) REFERENCES qr_codes(qr_id),
    document_type_id INTEGER NOT NULL REFERENCES document_types(id),
    cedula VARCHAR(20),
    nombre_completo VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    additional_data JSONB,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64),
    onedrive_url VARCHAR(500),
    onedrive_file_id VARCHAR(255),
    additional_files JSONB,
    qr_extraction_success BOOLEAN DEFAULT FALSE,
    qr_extraction_data JSONB,
    qr_extraction_error TEXT,
    ocr_processed BOOLEAN DEFAULT FALSE,
    ocr_text TEXT,
    ocr_confidence INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    approval_status VARCHAR(20) DEFAULT 'auto_approved',
    approval_notes TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    tags JSONB,
    category VARCHAR(100),
    priority INTEGER DEFAULT 0,
    group_id VARCHAR(50),
    sequence_number INTEGER DEFAULT 1,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    change_log JSONB,
    retention_date TIMESTAMP,
    archive_date TIMESTAMP,
    is_permanent BOOLEAN DEFAULT FALSE,
    is_confidential BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'normal',
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    last_viewed_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_documents_qr_code_id ON documents(qr_code_id);
CREATE INDEX idx_documents_document_type_id ON documents(document_type_id);
CREATE INDEX idx_documents_cedula ON documents(cedula);
CREATE INDEX idx_documents_status ON documents(status);

