#!/bin/bash

# WhatsApp Order Backend Deployment Script
# For Ubuntu 22.04+ with PostgreSQL, Redis, and Nginx

set -e

# Configuration
PROJECT_NAME="whatsapp-orders"
PROJECT_DIR="/opt/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_USER="www-data"
DB_NAME="whatsapp_orders"
DB_USER="whatsapp_user"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

log "Starting WhatsApp Order Backend deployment..."

# Update system
log "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
log "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    git \
    curl \
    build-essential \
    libpq-dev \
    pkg-config

# Install Chrome/Chromium for Selenium (WhatsApp Web automation)
log "Installing Chrome for WhatsApp Web automation..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Create project directory
log "Creating project directory..."
mkdir -p $PROJECT_DIR
mkdir -p $BACKEND_DIR
mkdir -p $BACKEND_DIR/logs
mkdir -p $BACKEND_DIR/exports
mkdir -p $BACKEND_DIR/static
mkdir -p $BACKEND_DIR/whatsapp_sessions

# Set ownership
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# Setup PostgreSQL
log "Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD 'secure_password_here';" || warn "User might already exist"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || warn "Database might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Configure Redis
log "Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

# Create Python virtual environment
log "Creating Python virtual environment..."
sudo -u $SERVICE_USER python3 -m venv $VENV_DIR

# Function to copy backend files (assumes this script is run from project root)
copy_backend_files() {
    log "Copying backend files..."
    if [ -d "./backend" ]; then
        cp -r ./backend/* $BACKEND_DIR/
        chown -R $SERVICE_USER:$SERVICE_USER $BACKEND_DIR
    else
        warn "Backend directory not found. Please copy your backend files manually to $BACKEND_DIR"
    fi
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip
    
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r $BACKEND_DIR/requirements.txt
    else
        error "requirements.txt not found in $BACKEND_DIR"
    fi
}

# Setup environment variables
setup_environment() {
    log "Setting up environment variables..."
    
    # Generate random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > $BACKEND_DIR/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://$DB_USER:secure_password_here@localhost:5432/$DB_NAME

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=$SECRET_KEY
WHATSAPP_WEBHOOK_SECRET=$WEBHOOK_SECRET

# API Configuration
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
DEBUG=false
ENVIRONMENT=production

# Celery Configuration
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# WhatsApp Configuration
WHATSAPP_SESSION_PATH=/opt/whatsapp-orders/backend/whatsapp_sessions
CHROME_EXECUTABLE_PATH=/usr/bin/google-chrome

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/whatsapp-orders/backend/logs/app.log
EOF
    
    chown $SERVICE_USER:$SERVICE_USER $BACKEND_DIR/.env
    chmod 600 $BACKEND_DIR/.env
    
    log "Environment variables configured. Please update the database password and domain in $BACKEND_DIR/.env"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    cd $BACKEND_DIR
    sudo -u $SERVICE_USER $VENV_DIR/bin/python -m alembic upgrade head
}

# Setup systemd services
setup_services() {
    log "Setting up systemd services..."
    
    # Copy service files
    if [ -f "$BACKEND_DIR/deployment/systemd/whatsapp-api.service" ]; then
        cp $BACKEND_DIR/deployment/systemd/*.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable whatsapp-api whatsapp-celery-worker whatsapp-celery-beat
    else
        warn "Service files not found. Please copy them manually from deployment/systemd/"
    fi
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    if [ -f "$BACKEND_DIR/deployment/nginx/whatsapp-orders.conf" ]; then
        cp $BACKEND_DIR/deployment/nginx/whatsapp-orders.conf /etc/nginx/sites-available/
        ln -sf /etc/nginx/sites-available/whatsapp-orders.conf /etc/nginx/sites-enabled/
        
        # Remove default site
        rm -f /etc/nginx/sites-enabled/default
        
        # Test nginx configuration
        nginx -t && systemctl reload nginx
    else
        warn "Nginx configuration not found. Please configure manually."
    fi
}

# Create admin user
create_admin_user() {
    log "Creating admin user..."
    cd $BACKEND_DIR
    
    cat > create_admin.py << 'EOF'
import os
import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Check if admin user exists
admin_user = db.query(User).filter(User.username == "admin").first()

if not admin_user:
    hashed_password = pwd_context.hash("admin123")  # Change this password!
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    print("Admin user created with username: admin, password: admin123")
    print("Please change the password after first login!")
else:
    print("Admin user already exists")

db.close()
EOF
    
    sudo -u $SERVICE_USER $VENV_DIR/bin/python create_admin.py
    rm create_admin.py
}

# Main deployment function
main() {
    copy_backend_files
    install_python_deps
    setup_environment
    run_migrations
    create_admin_user
    setup_services
    setup_nginx
    
    log "Starting services..."
    systemctl start whatsapp-api
    systemctl start whatsapp-celery-worker
    systemctl start whatsapp-celery-beat
    
    log "Deployment completed successfully!"
    log "Next steps:"
    log "1. Update the database password in $BACKEND_DIR/.env"
    log "2. Update the domain name in $BACKEND_DIR/.env and nginx config"
    log "3. Install SSL certificate"
    log "4. Test the API at http://your-domain/docs"
    log "5. Change the admin password (admin/admin123)"
    
    log "Service status:"
    systemctl status whatsapp-api --no-pager -l
    systemctl status whatsapp-celery-worker --no-pager -l
    systemctl status nginx --no-pager -l
}

# Run main function
main
