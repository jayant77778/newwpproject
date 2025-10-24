#!/usr/bin/env python3
"""
Production startup script for WhatsApp Order Backend
Handles pre-flight checks, database initialization, and service startup
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, test_connection, SessionLocal
from app.models import Base, User
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'CELERY_BROKER_URL',
        'CELERY_RESULT_BACKEND'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True


def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'logs',
        'exports',
        'static',
        'whatsapp_sessions',
        'uploads',
        'backups'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"✅ Directory created/verified: {directory}")


def test_database():
    """Test database connection and create tables"""
    logger.info("Testing database connection...")
    
    if not test_connection():
        logger.error("❌ Database connection failed!")
        return False
    
    logger.info("✅ Database connection successful")
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
        return True
    except Exception as e:
        logger.error(f"❌ Database table creation failed: {e}")
        return False


def create_default_admin():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create admin user
            hashed_password = pwd_context.hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@whatsapp-orders.local",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("✅ Default admin user created (admin/admin123)")
            logger.warning("⚠️  Please change the admin password after first login!")
        else:
            logger.info("✅ Admin user already exists")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_redis():
    """Test Redis connection"""
    try:
        import redis
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
        r = redis.from_url(redis_url)
        r.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


def check_celery():
    """Check if Celery can import and start"""
    try:
        from app.celery_config import celery_app
        logger.info("✅ Celery configuration loaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Celery configuration failed: {e}")
        return False


def run_pre_flight_checks():
    """Run all pre-flight checks"""
    logger.info("🚀 Starting WhatsApp Order Backend pre-flight checks...")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Directory Creation", create_directories),
        ("Database Connection", test_database),
        ("Redis Connection", test_redis),
        ("Celery Configuration", check_celery),
        ("Default Admin User", create_default_admin),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        logger.info(f"Running check: {check_name}")
        try:
            if callable(check_func):
                result = check_func()
            else:
                result = check_func
            
            if not result:
                failed_checks.append(check_name)
                logger.error(f"❌ Check failed: {check_name}")
            else:
                logger.info(f"✅ Check passed: {check_name}")
        except Exception as e:
            failed_checks.append(check_name)
            logger.error(f"❌ Check crashed: {check_name} - {e}")
    
    if failed_checks:
        logger.error(f"❌ Pre-flight checks failed: {', '.join(failed_checks)}")
        return False
    
    logger.info("🎉 All pre-flight checks passed!")
    return True


def start_production_server():
    """Start the production server with uvicorn"""
    import uvicorn
    from main import app
    
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    workers = int(os.getenv('API_WORKERS', 4))
    
    logger.info(f"🚀 Starting production server on {host}:{port} with {workers} workers")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=False
    )


def main():
    """Main startup function"""
    logger.info("=" * 80)
    logger.info("🚀 WhatsApp Order Backend Startup")
    logger.info(f"🕐 Time: {datetime.utcnow().isoformat()}")
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info("=" * 80)
    
    # Run pre-flight checks
    if not run_pre_flight_checks():
        logger.error("❌ Startup failed due to pre-flight check failures")
        sys.exit(1)
    
    # Check if we should only run checks (useful for CI/CD)
    if '--check-only' in sys.argv:
        logger.info("✅ Pre-flight checks completed successfully (check-only mode)")
        sys.exit(0)
    
    # Start the server
    try:
        start_production_server()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
