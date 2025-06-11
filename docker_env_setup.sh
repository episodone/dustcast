#!/bin/bash

# =============================================================================
# Docker Environment Setup for Tashkent Dust Storm Predictor
# =============================================================================

echo "🐳 Setting up Docker environment for Tashkent Dust Storm Predictor..."

# Create Docker-specific requirements.txt
cat > requirements.txt << 'EOL'
# Core Earth Engine and Geospatial (Docker optimized)
earthengine-api>=0.1.380
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-cloud-storage>=2.10.0

# Data Processing
pandas>=2.1.0
numpy>=1.25.0
scipy>=1.11.0

# Geospatial libraries (using system GDAL)
rasterio>=1.3.0
shapely>=2.0.0
pyproj>=3.6.0
fiona>=1.9.0

# Machine Learning
scikit-learn>=1.3.0

# Web Framework
Flask>=3.0.0
Flask-CORS>=4.0.0
Werkzeug>=3.0.0
Jinja2>=3.1.0

# HTTP and API
requests>=2.31.0
urllib3>=2.0.0
aiohttp>=3.9.0

# Task Scheduling
schedule>=1.2.0
APScheduler>=3.10.0

# Environment and Configuration
python-dotenv>=1.0.0

# Data Visualization
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.17.0

# Performance Optimization
numba>=0.58.0
bottleneck>=1.3.0

# Date and Time
python-dateutil>=2.8.0
pytz>=2023.3

# Development and Testing
pytest>=7.4.0
pytest-flask>=1.3.0

# Monitoring and Logging
psutil>=5.9.0

# Excel support
openpyxl>=3.1.0
xlsxwriter>=3.1.0

# Additional for Docker
gunicorn>=21.2.0
EOL

# Create Docker-specific .env file
cat > .env.docker << 'EOL'
# Docker Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Google Earth Engine
GOOGLE_CLOUD_PROJECT=youtubecommentsapp

# Geospatial library paths (Docker)
GDAL_DATA=/usr/share/gdal
PROJ_LIB=/usr/share/proj

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/dust_predictor.log

# Update intervals (in minutes)
DATA_UPDATE_INTERVAL=30
FORECAST_UPDATE_INTERVAL=360

# Tashkent coordinates
TASHKENT_LAT=41.2995
TASHKENT_LON=69.2401

# Alert thresholds
DUST_RISK_HIGH_THRESHOLD=0.6
DUST_RISK_MODERATE_THRESHOLD=0.3
TEMPERATURE_HIGH_THRESHOLD=35
NDDI_ELEVATED_THRESHOLD=0.15

# Cache settings
ENABLE_CACHE=True
CACHE_TTL_MINUTES=30
CACHE_DIR=/app/cache

# Docker specific settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
EOL

# Create .dockerignore
cat > .dockerignore << 'EOL'
# Virtual environments
dust_predictor_env/
venv/
env/

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Git
.git/
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/_build/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# Environments
.env.local
.env.development
.env.test

# Logs
*.log
logs/*.log

# Temporary files
*.tmp
*.temp
temp/

# Backup files
backup_*/
*.tar.gz
*.zip

# Docker
docker-compose.override.yml
Dockerfile.dev
EOL

# Create production Dockerfile with multi-stage build
cat > Dockerfile.production << 'EOL'
# Multi-stage build for production
FROM python:3.13-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for building
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal32 \
    proj-bin \
    libproj25 \
    geos-bin \
    libgeos-c1v5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV GDAL_DATA=/usr/share/gdal
ENV PROJ_LIB=/usr/share/proj

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=appuser:appuser . .

# Create directories with proper permissions
RUN mkdir -p data logs cache && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "app:app"]
EOL

# Create development docker-compose override
cat > docker-compose.override.yml << 'EOL'
# Development overrides
version: '3.8'

services:
  dust-predictor:
    build:
      context: .
      dockerfile: Dockerfile  # Use development Dockerfile
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=True
    volumes:
      # Mount source code for development
      - .:/app
      - /app/dust_predictor_env  # Exclude virtual env
    command: ["python", "app.py"]  # Use development server
EOL

# Create production docker-compose
cat > docker-compose.prod.yml << 'EOL'
version: '3.8'

services:
  dust-predictor:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: tashkent-dust-predictor-prod
    restart: unless-stopped
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./cache:/app/cache
      - ~/.config/earthengine:/home/appuser/.config/earthengine:ro
      - ./.env.docker:/app/.env:ro
    environment:
      - FLASK_ENV=production
      - GOOGLE_CLOUD_PROJECT=youtubecommentsapp
    networks:
      - dust-predictor-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: dust-predictor-nginx-prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - dust-predictor
    networks:
      - dust-predictor-network

networks:
  dust-predictor-network:
    driver: bridge
EOL

# Create production nginx config
cat > nginx.prod.conf << 'EOL'
events {
    worker_connections 1024;
}

http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml+rss;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;
    
    upstream dust_predictor {
        server dust-predictor:5001;
        keepalive 32;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # Rate limiting for general requests
        limit_req zone=general burst=50 nodelay;
        
        # Main application
        location / {
            proxy_pass http://dust_predictor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # API endpoints with stricter rate limiting
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
        
        # Static files with caching
        location /static/ {
            proxy_pass http://dust_predictor;
            expires 1d;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOL

echo "✅ Docker environment files created!"
echo ""
echo "📁 Files created:"
echo "   - Dockerfile (development)"
echo "   - Dockerfile.production (optimized production)"
echo "   - docker-compose.yml (main configuration)"
echo "   - docker-compose.prod.yml (production)"
echo "   - requirements.txt (Docker optimized)"
echo "   - .env.docker (Docker environment)"
echo "   - .dockerignore (exclude files)"
echo "   - nginx.prod.conf (production nginx)"
echo ""
echo "🚀 Next steps:"
echo "   1. Make scripts executable: chmod +x docker_manager.sh"
echo "   2. Setup: ./docker_manager.sh setup"
echo "   3. Start: ./docker_manager.sh start"
echo ""