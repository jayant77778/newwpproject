from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routers import orders, whatsapp, export, auth, summaries
from app.database import engine, SessionLocal, test_connection
from app.models import Base
from app.whatsapp.bot import WhatsAppBot
from app.celery_config import celery_app

# Test database connection
if not test_connection():
    print("❌ Database connection failed!")
    exit(1)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="WhatsApp Order Automation API",
    description="Backend API for WhatsApp Group Order Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["Summaries"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return HTTPException(status_code=500, detail=str(exc))

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "WhatsApp Order Automation API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "whatsapp": "ready"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 WhatsApp Order API starting up...")
    
    # Initialize WhatsApp bot
    try:
        whatsapp_bot = WhatsAppBot()
        app.state.whatsapp_bot = whatsapp_bot
        print("✅ WhatsApp bot initialized")
    except Exception as e:
        print(f"❌ WhatsApp bot initialization failed: {e}")
    
    print("✅ API server started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Shutting down API server...")
    
    # Clean up WhatsApp bot
    if hasattr(app.state, 'whatsapp_bot'):
        try:
            await app.state.whatsapp_bot.close()
            print("✅ WhatsApp bot closed")
        except Exception as e:
            print(f"❌ Error closing WhatsApp bot: {e}")
    
    print("✅ API server shutdown complete!")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
