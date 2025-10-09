# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SGD Web (Sistema de Gestión Documental Web) is an enterprise document management system with Microsoft 365 integration, automatic QR code generation, OneDrive synchronization, and configurable workflows. Built with FastAPI (backend) and React (frontend), PostgreSQL database.

## Development Commands

### Backend (FastAPI)

```bash
# Development server with auto-reload
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "message"  # Create new migration
alembic downgrade -1                    # Rollback one migration

# Testing
pytest tests/ -v --cov=app              # Run tests with coverage
pytest tests/test_specific.py::test_name  # Run specific test

# Code quality
black app/                              # Format code
isort app/                              # Sort imports
flake8 app/                            # Lint code
```

### Frontend (React)

```bash
# Development server
cd frontend
npm start                               # Starts on port 3000

# Building
npm run build                           # Production build
npm run serve                           # Serve production build locally

# Code quality
npm run lint                            # Run ESLint
npm run format                          # Format with Prettier
npm test                               # Run tests
```

### Docker Development

```bash
# Full stack with Docker
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose logs -f backend          # View backend logs
docker-compose exec backend bash        # Shell into backend container
docker-compose exec postgres psql -U sgd_user -d sgd_db  # Database shell

# Development mode with hot reload
docker-compose -f docker-compose.dev.yml up -d
```

## Architecture

### Backend Structure

**Core modules:**
- `app/main.py` - FastAPI application entry point with lifespan management, middleware configuration, and error handling
- `app/config.py` - Centralized settings using Pydantic (environment-based configuration)
- `app/database.py` - SQLAlchemy configuration with connection pooling and health checks

**Models (SQLAlchemy ORM):**
- `models/user.py` - Users with Microsoft 365 integration and role-based access
- `models/document.py` - Documents with metadata, versioning, and OneDrive sync info
- `models/document_type.py` - Configurable document types with validation rules and QR settings
- `models/qr_code.py` - QR code lifecycle management (generation → use → expiration)

**API Endpoints:**
- `api/endpoints/auth.py` - Microsoft SSO, JWT tokens, local auth (demo mode)
- `api/endpoints/documents.py` - CRUD operations, file uploads, metadata management
- `api/endpoints/document_types.py` - Admin configuration of document types
- `api/endpoints/generator.py` - Document generation from templates with QR insertion
- `api/endpoints/search.py` - Advanced search with filters (full-text, date, type, status)

**Utilities:**
- `utils/qr_processor.py` - QR code generation and extraction from PDFs/images
- `utils/file_handler.py` - File upload, validation, storage management
- `utils/onedrive_sync.py` - OneDrive integration for automatic cloud backup

### Frontend Structure

**Pages:**
- `pages/Login.jsx` - Microsoft SSO and local authentication
- `pages/Dashboard.jsx` - User dashboard with statistics and recent activity
- `pages/Generator.jsx` - Document generation interface
- `pages/Search.jsx` - Advanced search with filters and export
- `pages/Admin.jsx` - Admin panel for types and users

**Core Services:**
- `services/api.js` - Axios client with JWT interceptors and error handling
- `services/auth.js` - Authentication state management
- `services/microsoft.js` - Microsoft Graph API integration
- `services/documents.js` - Document operations
- `services/documentTypes.js` - Document type configuration

**State Management:**
- `context/AuthContext.js` - Authentication state and user session
- `context/ThemeContext.js` - Dark/light theme management
- `hooks/useAuth.js` - Authentication hooks with token refresh

### Database Schema

**Core tables:**
- `users` - User accounts with Microsoft Azure AD integration and refresh tokens
- `document_types` - Configurable types with validation rules, QR settings, workflow config
- `documents` - Document records with file_path (local), onedrive_url, onedrive_sync_info (JSON)
- `qr_codes` - QR lifecycle tracking with generation, usage, and expiration

**Important fields:**
- Documents store both local file paths AND OneDrive metadata (URL and ID in onedrive_sync_info JSON)
- Document types define QR position in Word templates (table_number, row, column)
- Users have microsoft_access_token and microsoft_refresh_token for Graph API calls

## Key Workflows

### Document Generation Flow

1. User selects document type and fills required fields
2. Backend loads Word template from `templates/` directory
3. QR code generated with unique ID and inserted into template at configured position
4. Template fields replaced with user data (using python-docx)
5. Document saved locally to `storage/documents/`
6. **Automatic OneDrive upload** via `onedrive_sync.py` (stores URL and ID in database)
7. Database record created with file metadata and OneDrive info

### Document Upload/Registration Flow

1. User uploads existing document (PDF, Word, images)
2. System extracts QR code if present (using pyzbar + opencv)
3. Validates against existing QR codes in database
4. Saves to local storage and syncs to OneDrive
5. Metadata extracted and stored with OneDrive reference

### OneDrive Synchronization

- **OneDrive structure:** `SGD_Documents/{document_type_code}/{unique_filename}`
- **Sync happens:** During document generation, on manual upload, batch sync operations
- **Metadata stored:** `document.onedrive_sync_info` contains `{onedrive_id, onedrive_url, sync_date, file_hash}`
- **Important:** Always check if `document.onedrive_url` exists before re-uploading
- **Access tokens:** Users must have valid `microsoft_access_token` or `microsoft_refresh_token`

### Microsoft 365 Authentication

- Uses MSAL (Microsoft Authentication Library) for OAuth flow
- Redirect URI configured in Azure AD app registration
- Scopes: `User.Read`, `User.ReadBasic.All`, `Files.ReadWrite`, `Sites.ReadWrite.All`
- Tokens stored in user table (access_token expires in 1 hour, use refresh_token)
- Demo mode available with local users (see `config.py` DEMO_* settings)

## Important Technical Details

### QR Code Processing

- **Generation:** Uses `qrcode` library with configurable error correction
- **Insertion:** Inserts into Word document tables using `python-docx` at specific cell position
- **Extraction:** Uses `pyzbar` + `opencv-python` to detect QR codes from PDFs (via PyMuPDF) and images
- **Configuration:** Each document type has `qr_config` with table/row/column position
- **Lifecycle:** QR codes track state (generated → used → expired) with timestamps

### File Storage

- **Local:** Files stored in `backend/storage/documents/` (Docker volume: `documents_storage`)
- **OneDrive:** Automatically synced to OneDrive Business using Microsoft Graph API
- **Validation:** File type checking (PDF, DOCX, images), size limits (50MB default)
- **Naming:** Local files use sanitized names; OneDrive uses `{doc_id}_{timestamp}_{name}`

### Database Migrations (Alembic)

- Migration files in `backend/alembic/versions/`
- Always use `alembic upgrade head` before starting backend
- Auto-generate migrations: `alembic revision --autogenerate -m "description"`
- Never edit migration files directly after they've been applied

### Environment Configuration

Critical environment variables (`.env` file):
- `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` - Azure AD app credentials
- `POSTGRES_*` - Database connection settings
- `SECRET_KEY` - JWT signing key (must be secure in production)
- `ADMIN_EMAILS` - Comma-separated list of admin emails for auto-role assignment
- `ALLOWED_DOMAINS` - Optional domain restriction for user logins
- `ENVIRONMENT` - `development|production` (affects CORS, debug logging, docs availability)

### Authentication System

- **Primary:** Microsoft SSO (Azure AD OAuth2 flow)
- **Fallback:** Local authentication (username/password) when `LOCAL_AUTH_ENABLED=true`
- **Demo users:** Three demo accounts (admin/operator/viewer) available in development
- **JWT tokens:** 24-hour expiration, include user role and Microsoft token status
- **Role hierarchy:** `admin` (full access) > `operator` (create/edit) > `viewer` (read-only)

### API Request Flow

1. Request hits middleware stack (CORS → GZIP → Security headers → Logging)
2. JWT validation via `api/deps.py` dependency injection
3. Route handler executes business logic
4. Database transaction managed by `get_db()` dependency
5. Response formatted and logged with process time

## Testing Approach

- Backend tests use `pytest` with `pytest-asyncio` for async endpoints
- Create test database with `ENVIRONMENT=testing`
- Mock Microsoft Graph API calls in tests (don't hit real endpoints)
- Frontend tests use React Testing Library + Jest
- Integration tests available via `docker-compose.test.yml`

## Common Development Tasks

### Adding a New Document Type

1. Admin creates type via frontend (`/admin`)
2. Upload Word template with table for QR insertion
3. Configure QR position (table number, row, column)
4. Set required fields (cedula, nombre, telefono, etc.)
5. OneDrive folder auto-created on first document generation

### Adding a New API Endpoint

1. Define Pydantic schema in `schemas/`
2. Create endpoint function in `api/endpoints/`
3. Add authentication dependency: `current_user: User = Depends(get_current_user)`
4. Add router to `main.py` with appropriate prefix/tags
5. Database operations use `db: Session = Depends(get_db)`

### Modifying Database Schema

1. Update SQLAlchemy model in `models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply: `alembic upgrade head`
5. Update Pydantic schemas to match

### Troubleshooting OneDrive Sync

- Check user has valid Microsoft token: `user.microsoft_access_token`
- Verify OneDrive is configured: `user.onedrive_configured`
- Review sync errors in `document.onedrive_sync_info`
- Test Graph API manually: `/health` endpoint checks database connectivity
- Force re-sync: `sync_document_to_onedrive(document, token, force_upload=True)`

## Production Deployment

- Use Gunicorn with Uvicorn workers for backend
- Frontend served via Nginx (config in `nginx/` directory)
- PostgreSQL 15+ required
- Set `ENVIRONMENT=production` and secure `SECRET_KEY`
- Configure SSL/TLS certificates in Nginx
- Enable trusted host middleware for security
- Database backups via `db_manager.backup_database()`

## Health Checks

- `GET /health` - Comprehensive health check (database, storage, uptime)
- `GET /info` - Application version and feature flags
- Docker health checks configured for all services
- Database health via active connection count query

## Security Considerations

- All passwords hashed (local auth only, primary is SSO)
- JWT tokens with 24-hour expiration
- CORS restricted to allowed origins
- File uploads validated (type, size, content)
- SQL injection prevented by SQLAlchemy ORM
- XSS protection headers configured
- Rate limiting on authentication endpoints (when enabled)
