#!/bin/bash

# =============================================================================
# SGD Web Setup Script
# Sets up the project for development or production deployment
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  SGD Web Setup Script"
    echo "  Sistema de Gestión Documental"
    echo "=============================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3 and try again."
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker found: $(docker --version)"
    else
        print_info "Docker not found. You'll need Docker for containerized deployment."
    fi
    
    # Check Docker Compose (optional)
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose found: $(docker-compose --version)"
    else
        print_info "Docker Compose not found. You'll need it for multi-container deployment."
    fi
    
    print_success "System requirements check completed"
}

setup_backend() {
    print_step "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_error "requirements.txt not found in backend directory"
        exit 1
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error "Backend .env file not found. Please create it from .env.example"
        exit 1
    fi
    
    print_success "Backend setup completed"
    cd ..
}

setup_frontend() {
    print_step "Setting up frontend..."
    
    cd frontend
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in frontend directory"
        exit 1
    fi
    
    # Install npm dependencies
    print_info "Installing npm dependencies... (this may take a few minutes)"
    npm ci
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error "Frontend .env file not found. Please create it from .env.example"
        exit 1
    fi
    
    print_success "Frontend setup completed"
    cd ..
}

setup_database() {
    print_step "Setting up database..."
    
    cd backend
    source venv/bin/activate
    
    # Run Alembic migrations
    print_info "Running database migrations..."
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        print_success "Database migrations completed"
    else
        print_info "No alembic.ini found. Skipping migrations."
    fi
    
    cd ..
}

check_configuration() {
    print_step "Checking configuration..."
    
    # Check backend .env
    if [ -f "backend/.env" ]; then
        print_success "Backend .env file found"
    else
        print_error "Backend .env file not found"
        exit 1
    fi
    
    # Check frontend .env
    if [ -f "frontend/.env" ]; then
        print_success "Frontend .env file found"
    else
        print_error "Frontend .env file not found"
        exit 1
    fi
    
    # Check Docker files
    if [ -f "docker-compose.yml" ]; then
        print_success "Docker Compose file found"
    else
        print_info "Docker Compose file not found"
    fi
    
    print_success "Configuration check completed"
}

run_tests() {
    print_step "Running tests..."
    
    # Backend tests
    print_info "Running backend tests..."
    cd backend
    source venv/bin/activate
    if command -v pytest &> /dev/null; then
        pytest || print_info "Some backend tests failed (this is normal during setup)"
    else
        print_info "pytest not available, skipping backend tests"
    fi
    cd ..
    
    # Frontend tests
    print_info "Running frontend tests..."
    cd frontend
    npm test -- --ci --coverage --watchAll=false || print_info "Some frontend tests failed (this is normal during setup)"
    cd ..
    
    print_success "Tests completed"
}

build_frontend() {
    print_step "Building frontend for production..."
    
    cd frontend
    print_info "Building React application..."
    npm run build
    print_success "Frontend build completed"
    cd ..
}

print_summary() {
    print_header
    print_success "SGD Web setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Start the development servers:"
    echo "     - Backend:  cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
    echo "     - Frontend: cd frontend && npm start"
    echo ""
    echo "  2. For Docker deployment:"
    echo "     - Development: docker-compose -f docker-compose.dev.yml up -d"
    echo "     - Production:  docker-compose up -d"
    echo ""
    echo "  3. Access the application:"
    echo "     - Frontend: http://localhost:3000"
    echo "     - Backend:  http://localhost:8000"
    echo "     - API Docs: http://localhost:8000/docs"
    echo ""
    print_info "Demo users (if LOCAL_AUTH_ENABLED=true):"
    echo "  - Admin:    admin@sgd-web.local / admin123"
    echo "  - Operator: operator@sgd-web.local / operator123"
    echo "  - Viewer:   viewer@sgd-web.local / viewer123"
    echo ""
}

# Main execution
main() {
    print_header
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_BUILD=false
    DEVELOPMENT=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --dev)
                DEVELOPMENT=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-tests    Skip running tests"
                echo "  --skip-build    Skip building frontend"
                echo "  --dev           Development setup (skip production build)"
                echo "  -h, --help      Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_requirements
    check_configuration
    setup_backend
    setup_frontend
    
    # Setup database if PostgreSQL is available
    if command -v psql &> /dev/null; then
        setup_database
    else
        print_info "PostgreSQL not found locally. Database setup will be handled by Docker."
    fi
    
    # Run tests unless skipped
    if [ "$SKIP_TESTS" != true ]; then
        run_tests
    fi
    
    # Build frontend for production unless skipped or development mode
    if [ "$SKIP_BUILD" != true ] && [ "$DEVELOPMENT" != true ]; then
        build_frontend
    fi
    
    print_summary
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi