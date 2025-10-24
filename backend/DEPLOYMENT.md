# WhatsApp Order Backend - Production Deployment Guide

This guide provides step-by-step instructions for deploying the WhatsApp Order Backend to production on Ubuntu 22.04+ VPS.

## 🚀 Quick Deployment

For automated deployment, run:
```bash
sudo bash deployment/deploy.sh
```

For manual deployment, follow the detailed steps below.

## 📋 Prerequisites

### System Requirements
- Ubuntu 22.04+ VPS with root access
- Minimum 2GB RAM, 20GB storage
- Domain name (recommended)
- SSL certificate (Let's Encrypt recommended)

### Services Required
- PostgreSQL 14+
- Redis 6+
- Nginx
- Python 3.8+
- Node.js 16+ (for WhatsApp bot integration)

## 🛠️ Manual Production Setup

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    build-essential \
    libpq-dev \
    supervisor

# Install Chrome for WhatsApp Web automation
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable
```

### Step 2: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE USER whatsapp_user WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE whatsapp_orders OWNER whatsapp_user;
GRANT ALL PRIVILEGES ON DATABASE whatsapp_orders TO whatsapp_user;
\q

# Test connection
psql -h localhost -U whatsapp_user -d whatsapp_orders -c "SELECT version();"
```

### Step 3: Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/whatsapp-orders
sudo chown -R www-data:www-data /opt/whatsapp-orders

# Clone your repository (replace with your actual repo)
cd /opt/whatsapp-orders
sudo -u www-data git clone https://github.com/your-username/whatsapp-orders.git .

# Create Python virtual environment
sudo -u www-data python3 -m venv venv

# Install Python dependencies
sudo -u www-data /opt/whatsapp-orders/venv/bin/pip install --upgrade pip
sudo -u www-data /opt/whatsapp-orders/venv/bin/pip install -r backend/requirements.txt
```

### Step 4: Environment Configuration

```bash
# Create production environment file
sudo -u www-data cp backend/.env.example backend/.env

# Edit environment variables
sudo -u www-data nano backend/.env
```

**Important environment variables to set:**
```bash
# Database
DATABASE_URL=postgresql://whatsapp_user:your_secure_password_here@localhost:5432/whatsapp_orders

# Security (generate secure random keys)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
WHATSAPP_WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Production settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Redis
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# WhatsApp
WHATSAPP_SESSION_PATH=/opt/whatsapp-orders/backend/whatsapp_sessions
CHROME_EXECUTABLE_PATH=/usr/bin/google-chrome
CHROME_HEADLESS=true
```

### Step 5: Database Migration

```bash
# Navigate to backend directory
cd /opt/whatsapp-orders/backend

# Run migrations
sudo -u www-data /opt/whatsapp-orders/venv/bin/python -m alembic upgrade head

# Create admin user
sudo -u www-data /opt/whatsapp-orders/venv/bin/python startup.py --check-only
```

### Step 6: SystemD Services

```bash
# Copy service files
sudo cp /opt/whatsapp-orders/backend/deployment/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable whatsapp-api
sudo systemctl enable whatsapp-celery-worker
sudo systemctl enable whatsapp-celery-beat

sudo systemctl start whatsapp-api
sudo systemctl start whatsapp-celery-worker
sudo systemctl start whatsapp-celery-beat

# Check status
sudo systemctl status whatsapp-api
sudo systemctl status whatsapp-celery-worker
```

### Step 7: Nginx Configuration

```bash
# Copy Nginx configuration
sudo cp /opt/whatsapp-orders/backend/deployment/nginx/whatsapp-orders.conf /etc/nginx/sites-available/

# Update the configuration with your domain
sudo nano /etc/nginx/sites-available/whatsapp-orders.conf

# Enable site
sudo ln -sf /etc/nginx/sites-available/whatsapp-orders.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 8: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 9: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Check status
sudo ufw status
```

## 🧪 Testing Production Deployment

### 1. Health Check
```bash
curl https://your-domain.com/
curl https://your-domain.com/api/health
```

### 2. API Documentation
Visit: `https://your-domain.com/docs`

### 3. Test API Endpoints
```bash
# Test user registration
curl -X POST "https://your-domain.com/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Test login
curl -X POST "https://your-domain.com/api/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
```

### 4. Run Comprehensive Tests
```bash
cd /opt/whatsapp-orders/backend
sudo -u www-data /opt/whatsapp-orders/venv/bin/python test_comprehensive.py https://your-domain.com
```

## 📊 Monitoring & Maintenance

### Service Management
```bash
# Check service status
sudo systemctl status whatsapp-api
sudo systemctl status whatsapp-celery-worker
sudo systemctl status whatsapp-celery-beat

# View logs
sudo journalctl -u whatsapp-api -f
sudo journalctl -u whatsapp-celery-worker -f

# Restart services
sudo systemctl restart whatsapp-api
sudo systemctl restart whatsapp-celery-worker
```

### Log Files
```bash
# Application logs
tail -f /opt/whatsapp-orders/backend/logs/app.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -f
```

### Database Backup
```bash
# Create backup script
cat > /opt/whatsapp-orders/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/whatsapp-orders/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U whatsapp_user -d whatsapp_orders > "$BACKUP_DIR/db_backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/whatsapp-orders/backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /opt/whatsapp-orders/backup.sh" | sudo crontab -
```

## 🔧 Performance Optimization

### 1. PostgreSQL Tuning
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf

# Recommended settings for 2GB RAM VPS:
# shared_buffers = 512MB
# effective_cache_size = 1536MB
# work_mem = 4MB
# maintenance_work_mem = 128MB

sudo systemctl restart postgresql
```

### 2. Redis Configuration
```bash
sudo nano /etc/redis/redis.conf

# Set appropriate maxmemory
# maxmemory 256mb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis
```

### 3. Nginx Optimization
```bash
# Add to nginx.conf
sudo nano /etc/nginx/nginx.conf

# worker_processes auto;
# worker_connections 1024;
# keepalive_timeout 65;
# client_max_body_size 50M;

sudo systemctl restart nginx
```

## 🛡️ Security Checklist

- [ ] Change default admin password
- [ ] Set strong database passwords
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/HTTPS
- [ ] Regular security updates
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Log rotation configured

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
cd /opt/whatsapp-orders
sudo -u www-data git pull origin main

# Install new dependencies
sudo -u www-data /opt/whatsapp-orders/venv/bin/pip install -r backend/requirements.txt

# Run migrations
cd backend
sudo -u www-data /opt/whatsapp-orders/venv/bin/python -m alembic upgrade head

# Restart services
sudo systemctl restart whatsapp-api
sudo systemctl restart whatsapp-celery-worker
```

### System Updates
```bash
# Regular system updates
sudo apt update && sudo apt upgrade -y

# Reboot if kernel updated
sudo reboot
```

## 🆘 Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check service logs
sudo journalctl -u whatsapp-api -n 50

# Check configuration
sudo -u www-data /opt/whatsapp-orders/venv/bin/python /opt/whatsapp-orders/backend/startup.py --check-only
```

**Database connection issues:**
```bash
# Test database connection
psql -h localhost -U whatsapp_user -d whatsapp_orders -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql
```

**Celery tasks not processing:**
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker status
sudo systemctl status whatsapp-celery-worker

# Inspect active tasks
sudo -u www-data /opt/whatsapp-orders/venv/bin/celery -A app.celery_config.celery_app inspect active
```

**High memory usage:**
```bash
# Monitor memory usage
htop

# Check processes
ps aux --sort=-%mem | head

# Restart services if needed
sudo systemctl restart whatsapp-api
```

## 📞 Support

For production deployment issues:
1. Check service logs first
2. Verify configuration files
3. Test individual components
4. Create GitHub issue with detailed logs
5. Consider professional support options

---

**Your WhatsApp Order Backend is now ready for production! 🚀**
