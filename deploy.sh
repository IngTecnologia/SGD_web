#!/bin/bash

# =============================================================================
# SGD Web Deployment Script
# Handles Docker-based deployment for development and production
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
REBUILD=false
LOGS=false
SERVICES=""
CLEAN=false

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  SGD Web Deployment Script"
    echo "  Docker-based deployment"
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

check_docker() {
    print_step "Checking Docker availability..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

check_environment_files() {
    print_step "Checking environment files..."
    
    # Check backend .env
    if [ ! -f "backend/.env" ]; then
        print_error "Backend .env file not found. Please create it first."
        exit 1
    fi
    
    # Check frontend .env
    if [ ! -f "frontend/.env" ]; then
        print_error "Frontend .env file not found. Please create it first."
        exit 1
    fi
    
    print_success "Environment files found"
}

get_compose_file() {
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "docker-compose.dev.yml"
    else
        echo "docker-compose.yml"
    fi
}

clean_docker() {
    print_step "Cleaning Docker resources..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    print_success "Docker cleanup completed"
}

build_images() {
    print_step "Building Docker images..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    if [ "$REBUILD" = true ]; then
        print_info "Rebuilding images from scratch..."
        docker-compose -f "$COMPOSE_FILE" build --no-cache $SERVICES
    else
        print_info "Building images..."
        docker-compose -f "$COMPOSE_FILE" build $SERVICES
    fi
    
    print_success "Docker images built successfully"
}

deploy_services() {
    print_step "Deploying services..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    # Create necessary directories
    mkdir -p backend/{uploads,temp,output,backups,templates,static}
    
    # Start services
    print_info "Starting services with $COMPOSE_FILE..."
    docker-compose -f "$COMPOSE_FILE" up -d $SERVICES
    
    # Wait for services to be healthy
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health
    
    print_success "Services deployed successfully"
}

check_service_health() {
    print_step "Checking service health..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    # Check backend health
    print_info "Checking backend health..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Backend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend health check failed"
        fi
        sleep 2
    done
    
    # Check frontend health
    print_info "Checking frontend health..."
    for i in {1..30}; do
        if curl -f http://localhost:3000 &> /dev/null; then
            print_success "Frontend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Frontend health check failed"
        fi
        sleep 2
    done
    
    # Check database health
    print_info "Checking database health..."
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U sgd_user &> /dev/null; then
        print_success "Database is healthy"
    else
        print_error "Database health check failed"
    fi
}

run_migrations() {
    print_step "Running database migrations..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    sleep 5
    
    # Run migrations
    docker-compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
    
    print_success "Database migrations completed"
}

show_logs() {
    COMPOSE_FILE=$(get_compose_file)
    
    if [ -n "$SERVICES" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f $SERVICES
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

show_status() {
    print_step "Checking deployment status..."
    
    COMPOSE_FILE=$(get_compose_file)
    
    echo ""
    print_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_info "Service URLs:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  PgAdmin:   http://localhost:5050 (admin@sgd.local / admin)"
    echo "  MailHog:   http://localhost:8025"
    
    echo ""
    print_info "Demo Users (if LOCAL_AUTH_ENABLED=true):"
    echo "  Admin:     admin@sgd-web.local / admin123"
    echo "  Operator:  operator@sgd-web.local / operator123"
    echo "  Viewer:    viewer@sgd-web.local / viewer123"
    
    echo ""
    print_info "To view logs: $0 --logs"
    print_info "To stop services: $0 --stop"
    echo ""
}

stop_services() {
    print_step "Stopping services..."
    
    COMPOSE_FILE=$(get_compose_file)
    docker-compose -f "$COMPOSE_FILE" down
    
    print_success "Services stopped"
}

print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV         Environment (development|production) [default: development]"
    echo "  -r, --rebuild         Rebuild Docker images from scratch"
    echo "  -c, --clean           Clean Docker resources before deployment"
    echo "  -s, --services LIST   Deploy specific services only (comma-separated)"
    echo "  -l, --logs            Show service logs after deployment"
    echo "  --stop               Stop all services"
    echo "  --status             Show deployment status"
    echo "  --migrations         Run database migrations only"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy in development mode"
    echo "  $0 --env production          # Deploy in production mode"
    echo "  $0 --rebuild --clean         # Clean rebuild"
    echo "  $0 --services backend,db     # Deploy only backend and database"
    echo "  $0 --logs                    # Deploy and show logs"
    echo "  $0 --stop                    # Stop all services"
}

# Main execution
main() {
    print_header
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--rebuild)
                REBUILD=true
                shift
                ;;
            -c|--clean)
                CLEAN=true
                shift
                ;;
            -s|--services)
                SERVICES="$2"
                shift 2
                ;;
            -l|--logs)
                LOGS=true
                shift
                ;;
            --stop)
                stop_services
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --migrations)
                check_docker
                run_migrations
                exit 0
                ;;
            -h|--help)
                print_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                print_help
                exit 1
                ;;
        esac
    done
    
    # Validate environment
    if [ "$ENVIRONMENT" != "development" ] && [ "$ENVIRONMENT" != "production" ]; then
        print_error "Invalid environment: $ENVIRONMENT. Must be 'development' or 'production'"
        exit 1
    fi
    
    print_info "Deploying in $ENVIRONMENT mode"
    
    # Run deployment steps
    check_docker
    check_environment_files
    
    if [ "$CLEAN" = true ]; then
        clean_docker
    fi
    
    build_images
    deploy_services
    
    # Run migrations if database is available
    if [ -z "$SERVICES" ] || [[ "$SERVICES" == *"postgres"* ]] || [[ "$SERVICES" == *"db"* ]]; then
        run_migrations
    fi
    
    show_status
    
    if [ "$LOGS" = true ]; then
        echo ""
        print_info "Showing logs (Ctrl+C to exit)..."
        show_logs
    fi
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi