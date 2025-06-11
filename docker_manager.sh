#!/bin/bash

# =============================================================================
# Docker Management Scripts for Tashkent Dust Storm Predictor
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_status "Docker is running ✅"
}

# Check if Earth Engine credentials exist
check_credentials() {
    if [ ! -d "$HOME/.config/earthengine" ]; then
        print_error "Earth Engine credentials not found!"
        print_warning "Please authenticate first:"
        echo "  python -c \"import ee; ee.Authenticate()\""
        exit 1
    fi
    print_status "Earth Engine credentials found ✅"
}

# Create necessary directories
create_directories() {
    print_status "Creating directories..."
    mkdir -p data logs cache ssl
    touch data/.gitkeep logs/.gitkeep cache/.gitkeep
}

# Build the Docker image
build_image() {
    print_header "Building Docker Image"
    print_status "Building tashkent-dust-predictor image..."
    
    docker build -t tashkent-dust-predictor . || {
        print_error "Failed to build Docker image"
        exit 1
    }
    
    print_status "Docker image built successfully ✅"
}

# Start the application
start_app() {
    print_header "Starting Dust Storm Predictor"
    
    # Stop existing containers
    docker-compose down
    
    # Start the application
    docker-compose up -d dust-predictor
    
    # Wait for the application to start
    print_status "Waiting for application to start..."
    sleep 10
    
    # Check if the application is healthy
    if docker-compose ps dust-predictor | grep -q "Up"; then
        print_status "Application started successfully ✅"
        print_status "Dashboard available at: http://localhost:5001"
        print_status "Health check: http://localhost:5001/health"
    else
        print_error "Application failed to start"
        print_warning "Check logs with: docker-compose logs dust-predictor"
        exit 1
    fi
}

# Start with reverse proxy
start_with_proxy() {
    print_header "Starting with Nginx Reverse Proxy"
    
    # Create nginx config if it doesn't exist
    if [ ! -f "nginx.conf" ]; then
        print_status "Creating nginx configuration..."
        create_nginx_config
    fi
    
    docker-compose up -d
    
    print_status "Full stack started ✅"
    print_status "Dashboard available at:"
    print_status "  - Direct: http://localhost:5001"
    print_status "  - Proxy: http://localhost:80"
}

# Create nginx configuration
create_nginx_config() {
    cat > nginx.conf << 'EOL'
events {
    worker_connections 1024;
}

http {
    upstream dust_predictor {
        server dust-predictor:5001;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Main application
        location / {
            proxy_pass http://dust_predictor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://dust_predictor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check (no rate limiting)
        location /health {
            proxy_pass http://dust_predictor;
            access_log off;
        }
        
        # Static files caching
        location /static/ {
            proxy_pass http://dust_predictor;
            expires 1d;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOL
}

# Stop the application
stop_app() {
    print_header "Stopping Application"
    docker-compose down
    print_status "Application stopped ✅"
}

# Show logs
show_logs() {
    print_header "Application Logs"
    docker-compose logs -f dust-predictor
}

# Show status
show_status() {
    print_header "Application Status"
    
    # Container status
    echo "Container Status:"
    docker-compose ps
    
    echo ""
    
    # Health check
    if curl -s http://localhost:5001/health >/dev/null 2>&1; then
        print_status "Application is healthy ✅"
        
        # Get current conditions
        echo ""
        echo "Current Conditions:"
        curl -s http://localhost:5001/api/current | python -m json.tool 2>/dev/null || echo "Could not fetch current conditions"
    else
        print_error "Application is not responding ❌"
    fi
    
    echo ""
    
    # Resource usage
    echo "Resource Usage:"
    docker stats --no-stream tashkent-dust-predictor 2>/dev/null || echo "Container not running"
}

# Clean up everything
cleanup() {
    print_header "Cleaning Up"
    
    # Stop containers
    docker-compose down
    
    # Remove volumes (optional)
    read -p "Remove data volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        print_status "Volumes removed"
    fi
    
    # Remove images (optional)
    read -p "Remove Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rmi tashkent-dust-predictor 2>/dev/null || true
        print_status "Images removed"
    fi
    
    print_status "Cleanup complete ✅"
}

# Update the application
update_app() {
    print_header "Updating Application"
    
    # Rebuild image
    build_image
    
    # Restart with new image
    docker-compose up -d dust-predictor
    
    print_status "Application updated ✅"
}

# Backup data
backup_data() {
    print_header "Backing Up Data"
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Copy data directories
    cp -r data logs cache "$BACKUP_DIR/" 2>/dev/null || true
    
    # Export container logs
    docker-compose logs dust-predictor > "$BACKUP_DIR/container_logs.txt" 2>/dev/null || true
    
    # Create archive
    tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    
    print_status "Backup created: ${BACKUP_DIR}.tar.gz ✅"
}

# Main script logic
case "$1" in
    "setup")
        print_header "Setting Up Docker Environment"
        check_docker
        check_credentials
        create_directories
        build_image
        print_status "Setup complete! Run './docker_manager.sh start' to begin."
        ;;
    "build")
        check_docker
        build_image
        ;;
    "start")
        check_docker
        check_credentials
        start_app
        ;;
    "start-full")
        check_docker
        check_credentials
        start_with_proxy
        ;;
    "stop")
        stop_app
        ;;
    "restart")
        stop_app
        sleep 2
        start_app
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "update")
        check_docker
        update_app
        ;;
    "backup")
        backup_data
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "🌪️ Tashkent Dust Storm Predictor - Docker Manager"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  setup      - Initial setup (build image, create directories)"
        echo "  build      - Build Docker image"
        echo "  start      - Start the application"
        echo "  start-full - Start with nginx reverse proxy"
        echo "  stop       - Stop the application"
        echo "  restart    - Restart the application"
        echo "  logs       - Show application logs"
        echo "  status     - Show application status and health"
        echo "  update     - Update and restart the application"
        echo "  backup     - Create backup of data"
        echo "  cleanup    - Clean up containers and images"
        echo ""
        echo "Examples:"
        echo "  $0 setup     # First time setup"
        echo "  $0 start     # Start the app"
        echo "  $0 status    # Check if it's working"
        echo "  $0 logs      # View logs"
        echo ""
        ;;
esac