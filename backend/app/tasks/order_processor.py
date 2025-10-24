"""
Order processing tasks for Celery
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from celery import current_task

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import Order, Customer, OrderItem, WhatsAppGroup, Product
from app.services.ai_service import enhance_order_data

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.process_order_confirmation"
)
def process_order_confirmation(self, order_id: int, confirmation_data: dict):
    """Process order confirmation and update status"""
    db = get_db_session()
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Finding order'}
        )

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Update order status
        order.status = confirmation_data.get("status", "confirmed")
        order.notes = confirmation_data.get("notes", order.notes)
        
        # Add confirmation timestamp
        if order.status == "confirmed":
            order.confirmed_at = datetime.utcnow()
        elif order.status == "delivered":
            order.delivered_at = datetime.utcnow()

        db.commit()

        logger.info(f"Order {order_id} status updated to {order.status}")
        return {
            "order_id": order_id,
            "status": order.status,
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing order confirmation {order_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.enhance_order_items"
)
def enhance_order_items(self, order_id: int):
    """Enhance order items with product matching and price suggestions"""
    db = get_db_session()
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Loading order'}
        )

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        enhanced_items = []
        for item in order.order_items:
            current_task.update_state(
                state='PROCESSING',
                meta={'step': f'Enhancing item: {item.product_name}'}
            )

            # Try to match with existing products
            product = db.query(Product).filter(
                Product.name.ilike(f"%{item.product_name}%")
            ).first()

            if product:
                item.product_id = product.id
                if not item.unit_price and product.price:
                    item.unit_price = product.price

            # Use AI to enhance item data
            enhancement = enhance_order_data({
                "product_name": item.product_name,
                "quantity": item.quantity,
                "current_price": item.unit_price,
                "notes": item.notes
            })

            if enhancement:
                if enhancement.get("suggested_price") and not item.unit_price:
                    item.unit_price = enhancement["suggested_price"]
                if enhancement.get("category"):
                    item.category = enhancement["category"]

            enhanced_items.append({
                "id": item.id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "product_id": item.product_id
            })

        db.commit()

        logger.info(f"Enhanced {len(enhanced_items)} items for order {order_id}")
        return {
            "order_id": order_id,
            "enhanced_items": enhanced_items,
            "total_items": len(enhanced_items)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error enhancing order items {order_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.calculate_order_totals"
)
def calculate_order_totals(self, order_id: int):
    """Calculate and update order totals"""
    db = get_db_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        total_items = 0
        total_amount = 0.0
        
        for item in order.order_items:
            total_items += item.quantity
            
            if item.unit_price:
                try:
                    # Clean price string and convert to float
                    price_str = item.unit_price.replace('₹', '').replace('$', '').replace(',', '').strip()
                    price = float(price_str)
                    total_amount += price * item.quantity
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse price for item {item.id}: {item.unit_price}")

        # Update order with calculated totals
        order.total_items = total_items
        order.total_amount = total_amount

        db.commit()

        return {
            "order_id": order_id,
            "total_items": total_items,
            "total_amount": total_amount
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating order totals {order_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.auto_complete_pending_orders"
)
def auto_complete_pending_orders(self):
    """Auto-complete orders that have been pending for too long"""
    db = get_db_session()
    try:
        # Find orders pending for more than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        pending_orders = db.query(Order).filter(
            Order.status == "pending",
            Order.created_at <= cutoff_time
        ).all()

        completed_orders = []
        for order in pending_orders:
            try:
                order.status = "auto_confirmed"
                order.notes = f"{order.notes or ''}\n[AUTO] Confirmed after 24h timeout".strip()
                completed_orders.append(order.id)
            except Exception as e:
                logger.error(f"Error auto-completing order {order.id}: {str(e)}")

        db.commit()

        logger.info(f"Auto-completed {len(completed_orders)} orders")
        return {
            "completed_orders": completed_orders,
            "total_completed": len(completed_orders)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error in auto-complete pending orders: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.merge_duplicate_orders"
)
def merge_duplicate_orders(self, customer_id: int, time_window_minutes: int = 5):
    """Merge duplicate orders from the same customer within a time window"""
    db = get_db_session()
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Finding duplicate orders'}
        )

        # Find recent orders from this customer
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        recent_orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.created_at >= cutoff_time,
            Order.status == "pending"
        ).order_by(Order.created_at).all()

        if len(recent_orders) <= 1:
            return {"message": "No duplicate orders found", "merged_count": 0}

        # Keep the first order, merge others into it
        primary_order = recent_orders[0]
        duplicate_orders = recent_orders[1:]

        merged_items = []
        for duplicate_order in duplicate_orders:
            # Move items to primary order
            for item in duplicate_order.order_items:
                item.order_id = primary_order.id
                merged_items.append({
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "from_order": duplicate_order.id
                })

            # Update primary order notes
            if duplicate_order.notes:
                primary_order.notes = f"{primary_order.notes or ''}\nMerged: {duplicate_order.notes}".strip()

            # Delete duplicate order
            db.delete(duplicate_order)

        db.commit()

        # Recalculate totals for primary order
        calculate_order_totals.delay(primary_order.id)

        logger.info(f"Merged {len(duplicate_orders)} duplicate orders into order {primary_order.id}")
        return {
            "primary_order_id": primary_order.id,
            "merged_orders": [o.id for o in duplicate_orders],
            "merged_items": merged_items,
            "merged_count": len(duplicate_orders)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error merging duplicate orders for customer {customer_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.order_processor.validate_order_data"
)
def validate_order_data(self, order_id: int):
    """Validate and clean order data"""
    db = get_db_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        validation_errors = []
        
        # Validate customer
        if not order.customer:
            validation_errors.append("Missing customer information")

        # Validate items
        if not order.order_items:
            validation_errors.append("Order has no items")
        else:
            for item in order.order_items:
                if not item.product_name or not item.product_name.strip():
                    validation_errors.append(f"Item {item.id} has no product name")
                if item.quantity <= 0:
                    validation_errors.append(f"Item {item.id} has invalid quantity")

        # Validate group
        if not order.group:
            validation_errors.append("Order not associated with a group")

        # Update order validation status
        order.is_validated = len(validation_errors) == 0
        order.validation_errors = validation_errors if validation_errors else None

        db.commit()

        return {
            "order_id": order_id,
            "is_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error validating order {order_id}: {str(e)}")
        raise
    finally:
        db.close()