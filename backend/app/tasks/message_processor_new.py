"""
Message processing tasks for Celery
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from celery import current_task

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import (
    WhatsAppMessage, Order, Customer, OrderItem, WhatsAppGroup
)
from app.services.ai_service import extract_order_info

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="app.tasks.message_processor.process_whatsapp_message"
)
def process_whatsapp_message(self, message_data: dict):
    """Process incoming WhatsApp message and extract order information"""
    db = get_db_session()
    try:
        msg_id = message_data.get('message_id')
        logger.info(f"Processing WhatsApp message: {msg_id}")

        # Update task status
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Validating message'}
        )

        # Check if message already exists
        existing_message = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.message_id == message_data["message_id"]
        ).first()

        if existing_message:
            logger.info(f"Message already processed: {msg_id}")
            return {"status": "skipped", "reason": "already_processed"}

        # Create WhatsApp message record
        timestamp = message_data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

        whatsapp_message = WhatsAppMessage(
            message_id=message_data["message_id"],
            group_id=message_data["group_id"],
            sender_id=message_data["sender_id"],
            sender_name=message_data.get("sender_name", ""),
            message_content=message_data["message_content"],
            message_type=message_data.get("message_type", "text"),
            timestamp=timestamp
        )

        db.add(whatsapp_message)
        db.commit()

        # Update task status
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Analyzing message content'}
        )

        # Extract order information using AI
        extracted_data = extract_order_info(message_data["message_content"])
        
        # Update message with extracted data
        whatsapp_message.extracted_data = extracted_data
        whatsapp_message.is_order = extracted_data.get("is_order", False)
        
        if whatsapp_message.is_order:
            current_task.update_state(
                state='PROCESSING',
                meta={'step': 'Processing order information'}
            )
            
            # Process the order
            order_result = _process_order_from_message(db, whatsapp_message, extracted_data)
            whatsapp_message.is_processed = True
            
            db.commit()
            
            logger.info(f"Order processed successfully: {order_result}")
            return {
                "status": "success",
                "message_id": msg_id,
                "order_created": order_result is not None,
                "order_id": order_result.get("order_id") if order_result else None
            }
        else:
            whatsapp_message.is_processed = True
            db.commit()
            
            logger.info(f"Message processed but no order found: {msg_id}")
            return {
                "status": "success",
                "message_id": msg_id,
                "order_created": False
            }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing message {msg_id}: {str(e)}")
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'step': 'Error occurred'}
        )
        raise
    finally:
        db.close()


def _process_order_from_message(db, whatsapp_message: WhatsAppMessage, extracted_data: dict) -> Optional[dict]:
    """Process order from extracted message data"""
    try:
        # Get or create customer
        customer = _get_or_create_customer(
            db, 
            extracted_data.get("customer_name"),
            extracted_data.get("customer_phone"),
            whatsapp_message.sender_id
        )
        
        # Get WhatsApp group
        group = db.query(WhatsAppGroup).filter(
            WhatsAppGroup.group_id == whatsapp_message.group_id
        ).first()
        
        if not group:
            # Create group if not exists
            group = WhatsAppGroup(
                group_id=whatsapp_message.group_id,
                group_name=f"Group {whatsapp_message.group_id}",
                is_active=True
            )
            db.add(group)
            db.commit()
            db.refresh(group)

        # Create order
        order = Order(
            customer_id=customer.id,
            group_id=group.id,
            message_id=whatsapp_message.message_id,
            order_date=whatsapp_message.timestamp.date(),
            order_time=whatsapp_message.timestamp.strftime("%I:%M %p"),
            status="pending",
            notes=extracted_data.get("notes"),
            raw_message=whatsapp_message.message_content,
            is_processed=True
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)

        # Create order items
        items = extracted_data.get("items", [])
        for item_data in items:
            order_item = OrderItem(
                order_id=order.id,
                product_name=item_data.get("name"),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("price"),
                notes=item_data.get("notes")
            )
            db.add(order_item)

        # Update customer order count
        customer.total_orders = db.query(Order).filter(Order.customer_id == customer.id).count()
        
        db.commit()

        return {
            "order_id": order.id,
            "customer_id": customer.id,
            "items_count": len(items)
        }

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.rollback()
        return None


def _get_or_create_customer(db, name: str, phone: str, whatsapp_id: str) -> Customer:
    """Get existing customer or create new one"""
    # Try to find by WhatsApp ID first
    customer = None
    if whatsapp_id:
        customer = db.query(Customer).filter(Customer.whatsapp_id == whatsapp_id).first()
    
    # Try to find by phone number
    if not customer and phone:
        customer = db.query(Customer).filter(Customer.phone_number == phone).first()
    
    # Create new customer if not found
    if not customer:
        customer = Customer(
            name=name or f"Customer {whatsapp_id}",
            phone_number=phone or f"+{whatsapp_id}",
            whatsapp_id=whatsapp_id,
            is_active=True,
            total_orders=0
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    
    return customer


@celery_app.task(
    bind=True,
    name="app.tasks.message_processor.bulk_process_messages"
)
def bulk_process_messages(self, messages_data: List[dict]):
    """Process multiple WhatsApp messages in bulk"""
    results = []
    total_messages = len(messages_data)
    
    for i, message_data in enumerate(messages_data):
        try:
            current_task.update_state(
                state='PROCESSING',
                meta={
                    'step': f'Processing message {i+1} of {total_messages}',
                    'progress': ((i+1) / total_messages) * 100
                }
            )
            
            result = process_whatsapp_message.apply_async(args=[message_data])
            results.append({
                "message_id": message_data.get("message_id"),
                "task_id": result.id,
                "status": "queued"
            })
            
        except Exception as e:
            logger.error(f"Error queuing message processing: {str(e)}")
            results.append({
                "message_id": message_data.get("message_id"),
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_messages": total_messages,
        "queued_successfully": len([r for r in results if r["status"] == "queued"]),
        "results": results
    }


@celery_app.task(
    bind=True,
    name="app.tasks.message_processor.reprocess_failed_messages"
)
def reprocess_failed_messages(self):
    """Reprocess failed messages from the last 24 hours"""
    db = get_db_session()
    try:
        # Find unprocessed messages from last 24 hours
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        failed_messages = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.is_processed == False,
            WhatsAppMessage.created_at >= yesterday,
            WhatsAppMessage.is_order == True
        ).all()
        
        if not failed_messages:
            return {"status": "success", "message": "No failed messages to reprocess"}
        
        # Queue messages for reprocessing
        results = []
        for message in failed_messages:
            try:
                message_data = {
                    "message_id": message.message_id,
                    "group_id": message.group_id,
                    "sender_id": message.sender_id,
                    "sender_name": message.sender_name,
                    "message_content": message.message_content,
                    "message_type": message.message_type,
                    "timestamp": message.timestamp.isoformat()
                }
                
                result = process_whatsapp_message.apply_async(args=[message_data])
                results.append({
                    "message_id": message.message_id,
                    "task_id": result.id,
                    "status": "requeued"
                })
                
            except Exception as e:
                logger.error(f"Error requeuing message {message.message_id}: {str(e)}")
                results.append({
                    "message_id": message.message_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "total_failed": len(failed_messages),
            "requeued": len([r for r in results if r["status"] == "requeued"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing failed messages: {str(e)}")
        raise
    finally:
        db.close()
