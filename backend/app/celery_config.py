"""
Celery configuration for WhatsApp Order Backend
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
celery_app = Celery(
    "whatsapp_orders",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "app.tasks.message_processor",
        "app.tasks.order_processor", 
        "app.tasks.summary_generator",
        "app.tasks.export_generator"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer=os.getenv("CELERY_TASK_SERIALIZER", "json"),
    accept_content=[os.getenv("CELERY_ACCEPT_CONTENT", "json")],
    result_serializer=os.getenv("CELERY_RESULT_SERIALIZER", "json"),
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=os.getenv("CELERY_ENABLE_UTC", "true").lower() == "true",
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
    # Task routing
    task_routes={
        "app.tasks.message_processor.*": {"queue": "messages"},
        "app.tasks.order_processor.*": {"queue": "orders"},
        "app.tasks.summary_generator.*": {"queue": "summaries"},
        "app.tasks.export_generator.*": {"queue": "exports"},
    },
    # Rate limiting
    task_annotations={
        "app.tasks.message_processor.process_whatsapp_message": {"rate_limit": "10/m"},
        "app.tasks.export_generator.generate_export": {"rate_limit": "5/m"},
    }
)
