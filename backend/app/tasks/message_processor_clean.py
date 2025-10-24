"""
Message processing tasks for Celery
"""
import logging
from datetime import datetime, timedelta
from celery import current_task

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import (
    WhatsAppMessage, Order, Customer, OrderItem, WhatsAppGroup
)
from app.services.ai_service import ai_extractor

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
            timestamp = datetime.fromisoformat(timestamp)

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

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Extracting order information'}
        )

        # Extract order information using AI service
        extracted_data = ai_extractor.extract_order_from_message(
            message_data["message_content"],
            message_data.get("sender_name", "")
        )

        # Validate extracted data
        validated_data = ai_extractor.validate_order_data(extracted_data)

        # Update message with extracted data
        whatsapp_message.extracted_data = validated_data
        whatsapp_message.is_order = validated_data.get("is_order", False)

        if validated_data.get("is_order"):
            current_task.update_state(
                state='PROCESSING',
                meta={'step': 'Creating order record'}
            )

            # Process as order
            order_result = create_order_from_extracted_data.delay(
                whatsapp_message.id,
                validated_data
            )

            whatsapp_message.is_processed = True
            db.commit()

            msg = f"Order extraction initiated for message: {msg_id}"
            logger.info(msg)
            return {
                "status": "success",
                "is_order": True,
                "order_task_id": order_result.id,
                "extracted_data": validated_data
            }
        else:
            whatsapp_message.is_processed = True
            db.commit()

            msg = f"Message processed but no order found: {msg_id}"
            logger.info(msg)
            return {
                "status": "success",
                "is_order": False,
                "extracted_data": validated_data
            }

    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        db.rollback()

        # Update task with error status
        current_task.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'message_id': message_data.get('message_id')
            }
        )

        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.message_processor.create_order_from_extracted_data"
)
def create_order_from_extracted_data(self, message_id: int, data: dict):
    """Create order record from extracted data"""
    db = get_db_session()
    try:
        logger.info(f"Creating order from message ID: {message_id}")

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Finding or creating customer'}
        )

        # Get the WhatsApp message
        message = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.id == message_id
        ).first()
        if not message:
            raise ValueError(f"WhatsApp message not found: {message_id}")

        # Find or create customer
        customer = db.query(Customer).filter(
            Customer.whatsapp_id == message.sender_id
        ).first()

        if not customer:
            # Create new customer
            customer_name = data.get(
                "customer_name",
                message.sender_name or f"Customer_{message.sender_id}"
            )
            customer = Customer(
                name=customer_name,
                phone_number=message.sender_id,
                whatsapp_id=message.sender_id
            )
            db.add(customer)
            db.flush()  # Get customer ID

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Finding WhatsApp group'}
        )

        # Find or create WhatsApp group
        group = db.query(WhatsAppGroup).filter(
            WhatsAppGroup.group_id == message.group_id
        ).first()

        if not group:
            # Create new group
            group = WhatsAppGroup(
                group_id=message.group_id,
                group_name=f"Group_{message.group_id}",
                description="Auto-created from message processing"
            )
            db.add(group)
            db.flush()  # Get group ID

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Creating order'}
        )

        # Create order
        order_time = data.get(
            "order_time",
            datetime.now().strftime("%I:%M %p")
        )
        order = Order(
            customer_id=customer.id,
            group_id=group.id,
            message_id=message.message_id,
            order_time=order_time,
            notes=data.get("special_instructions", ""),
            raw_message=message.message_content,
            status="pending"
        )

        db.add(order)
        db.flush()  # Get order ID

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Creating order items'}
        )

        # Create order items
        for item_data in data.get("items", []):
            order_item = OrderItem(
                order_id=order.id,
                product_name=item_data["name"],
                quantity=item_data["quantity"],
                unit_price=None,  # Will be set later
                notes=item_data.get("notes", "")
            )
            db.add(order_item)

        # Update customer order count
        customer.total_orders += 1

        # Update group last message time
        group.last_message_time = message.timestamp

        db.commit()

        logger.info(f"Order created successfully: Order ID {order.id}")

        return {
            "status": "success",
            "order_id": order.id,
            "customer_id": customer.id,
            "group_id": group.id,
            "items_count": len(data.get("items", []))
        }

    except Exception as e:
        logger.error(f"Error creating order from extracted data: {e}")
        db.rollback()

        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'message_id': message_id}
        )

        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.message_processor.cleanup_old_messages")
def cleanup_old_messages(days_old: int = 30):
    """Clean up old processed messages to free up space"""
    db = get_db_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Delete old messages that are processed and not orders
        deleted_count = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.created_at < cutoff_date,
            WhatsAppMessage.is_processed.is_(True),
            WhatsAppMessage.is_order.is_(False)
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {deleted_count} old messages")

        return {
            "status": "success",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up old messages: {e}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()
