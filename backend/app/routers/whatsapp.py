from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
from app.tasks.message_processor import process_whatsapp_message, bulk_process_messages
from datetime import datetime
import hmac
import hashlib

from app.database import get_db
from app.models import WhatsAppGroup, WhatsAppMessage, Order, Customer, OrderItem
from app.schemas import (
    WhatsAppGroup as WhatsAppGroupSchema,
    WhatsAppGroupCreate,
    WhatsAppMessage as WhatsAppMessageSchema,
    ApiResponse
)
from app.whatsapp.bot import WhatsAppBot

router = APIRouter()

# Global bot instance
whatsapp_bot = None

def get_whatsapp_bot():
    global whatsapp_bot
    if whatsapp_bot is None:
        whatsapp_bot = WhatsAppBot()
    return whatsapp_bot

@router.post("/connect")
async def connect_whatsapp():
    """Connect to WhatsApp Web"""
    try:
        bot = get_whatsapp_bot()
        success = await bot.connect()
        
        if success:
            return ApiResponse(
                success=True,
                message="Successfully connected to WhatsApp Web",
                data={"status": "connected"}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to connect to WhatsApp Web. Please scan QR code."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_whatsapp_status():
    """Get WhatsApp connection status"""
    try:
        bot = get_whatsapp_bot()
        return ApiResponse(
            success=True,
            message="WhatsApp status retrieved",
            data={
                "connected": bot.is_connected,
                "current_group": bot.current_group
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups")
async def get_groups(db: Session = Depends(get_db)):
    """Get available WhatsApp groups"""
    try:
        bot = get_whatsapp_bot()
        
        if not bot.is_connected:
            success = await bot.connect()
            if not success:
                raise HTTPException(
                    status_code=400, 
                    detail="Not connected to WhatsApp Web"
                )
        
        # Get groups from WhatsApp
        whatsapp_groups = await bot.get_groups()
        
        # Store/update groups in database
        db_groups = []
        for group in whatsapp_groups:
            # Check if group exists in database
            existing_group = db.query(WhatsAppGroup).filter(
                WhatsAppGroup.group_id == group["id"]
            ).first()
            
            if existing_group:
                existing_group.group_name = group["name"]
                existing_group.is_active = True
                db.commit()
                db_groups.append(existing_group)
            else:
                # Create new group
                new_group = WhatsAppGroup(
                    group_id=group["id"],
                    group_name=group["name"],
                    is_active=True
                )
                db.add(new_group)
                db.commit()
                db.refresh(new_group)
                db_groups.append(new_group)
        
        return ApiResponse(
            success=True,
            message=f"Found {len(db_groups)} groups",
            data=[WhatsAppGroupSchema.from_orm(group) for group in db_groups]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/select")
async def select_group(group_id: int, db: Session = Depends(get_db)):
    """Select a WhatsApp group for monitoring"""
    try:
        # Get group from database
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        bot = get_whatsapp_bot()
        success = await bot.select_group(group.group_name)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"Selected group: {group.group_name}",
                data={"group_id": group_id, "group_name": group.group_name}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to select group: {group.group_name}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/messages")
async def get_group_messages(
    group_id: int, 
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent messages from a WhatsApp group"""
    try:
        # Get group from database
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        bot = get_whatsapp_bot()
        
        # Select group if not already selected
        if bot.current_group != group.group_name:
            await bot.select_group(group.group_name)
        
        # Get messages from WhatsApp
        messages = await bot.get_messages(limit=limit)
        
        # Store messages in database
        db_messages = []
        for msg in messages:
            # Check if message already exists
            existing_msg = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.message_id == msg["id"]
            ).first()
            
            if not existing_msg:
                new_message = WhatsAppMessage(
                    message_id=msg["id"],
                    group_id=group.group_id,
                    sender_id=msg["sender"],
                    sender_name=msg["sender"],
                    message_content=msg["content"],
                    timestamp=msg["datetime"],
                    is_order=msg["is_order"],
                    extracted_data=msg.get("order_data")
                )
                db.add(new_message)
                db_messages.append(new_message)
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(messages)} messages",
            data={
                "messages": messages,
                "group_name": group.group_name,
                "total_messages": len(messages),
                "order_messages": len([msg for msg in messages if msg["is_order"]])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/export")
async def export_group_chat(
    group_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Export chat data from a WhatsApp group"""
    try:
        # Get group from database
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        bot = get_whatsapp_bot()
        export_path = await bot.export_chat(group.group_name, days=days)
        
        if export_path:
            return ApiResponse(
                success=True,
                message="Chat exported successfully",
                data={
                    "export_path": export_path,
                    "group_name": group.group_name,
                    "days": days
                }
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to export chat"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/start-monitoring")
async def start_monitoring_group(
    group_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start monitoring a WhatsApp group for new orders"""
    try:
        # Get group from database
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        bot = get_whatsapp_bot()
        
        # Define callback for new order messages
        async def order_callback(message):
            try:
                # Process new order message
                await process_order_message(message, group, db)
            except Exception as e:
                print(f"Error processing order message: {e}")
        
        # Start monitoring in background
        background_tasks.add_task(
            bot.start_monitoring, 
            group.group_name, 
            order_callback
        )
        
        return ApiResponse(
            success=True,
            message=f"Started monitoring group: {group.group_name}",
            data={"group_id": group_id, "group_name": group.group_name}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_order_message(message: dict, group: WhatsAppGroup, db: Session):
    """Process a new order message and create order in database"""
    try:
        if not message.get("is_order") or not message.get("order_data"):
            return
        
        order_data = message["order_data"]
        
        # Get or create customer
        customer = db.query(Customer).filter(
            Customer.name == order_data["customer_name"]
        ).first()
        
        if not customer:
            customer = Customer(
                name=order_data["customer_name"],
                phone_number="",  # Will be updated when available
                whatsapp_id=message["sender"]
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        # Create order
        new_order = Order(
            customer_id=customer.id,
            group_id=group.id,
            message_id=message["id"],
            order_time=message["timestamp"],
            raw_message=message["content"],
            status="pending"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Create order items
        for item_data in order_data.get("items", []):
            order_item = OrderItem(
                order_id=new_order.id,
                product_name=item_data["item"],
                quantity=item_data["quantity"]
            )
            db.add(order_item)
        
        # Update customer total orders
        customer.total_orders += 1
        
        db.commit()
        
        print(f"✅ Processed order from {customer.name}: {len(order_data.get('items', []))} items")
        
    except Exception as e:
        print(f"❌ Error processing order message: {e}")
        db.rollback()

@router.post("/disconnect")
async def disconnect_whatsapp():
    """Disconnect from WhatsApp Web"""
    try:
        bot = get_whatsapp_bot()
        await bot.close()
        
        return ApiResponse(
            success=True,
            message="Disconnected from WhatsApp Web",
            data={"status": "disconnected"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def whatsapp_webhook(
    request_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for receiving WhatsApp messages from external services
    like Node Baileys or whatsapp-web.js
    """
    try:
        # Validate webhook secret if configured
        webhook_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
        if webhook_secret:
            provided_signature = request_data.get("signature")
            if not provided_signature:
                raise HTTPException(
                    status_code=401, 
                    detail="Missing webhook signature"
                )
            
            # Validate signature (implement your signature validation logic)
            request_body = json.dumps(request_data.get("data", {}))
            expected_signature = hmac.new(
                webhook_secret.encode(),
                request_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(provided_signature, expected_signature):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )

        # Extract message data
        message_data = request_data.get("data", {})
        if not message_data:
            raise HTTPException(
                status_code=400,
                detail="No message data provided"
            )

        # Validate required fields
        required_fields = ["message_id", "group_id", "sender_id", "message_content", "timestamp"]
        missing_fields = [field for field in required_fields if not message_data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Check if it's a bulk message or single message
        if isinstance(message_data, list):
            # Bulk processing
            background_tasks.add_task(
                bulk_process_messages.delay,
                message_data
            )
            
            return ApiResponse(
                success=True,
                message=f"Queued {len(message_data)} messages for processing",
                data={
                    "queued_messages": len(message_data),
                    "processing": "async"
                }
            )
        else:
            # Single message processing
            task_result = process_whatsapp_message.delay(message_data)
            
            return ApiResponse(
                success=True,
                message="Message queued for processing",
                data={
                    "task_id": task_result.id,
                    "message_id": message_data["message_id"],
                    "processing": "async"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook functionality"""
    test_message = {
        "message_id": f"test_{datetime.utcnow().timestamp()}",
        "group_id": "test_group_123",
        "sender_id": "test_sender_123",
        "sender_name": "Test User",
        "message_content": "Test order: 2x Pizza, 1x Coke",
        "message_type": "text",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    task_result = process_whatsapp_message.delay(test_message)
    
    return ApiResponse(
        success=True,
        message="Test message queued for processing",
        data={
            "task_id": task_result.id,
            "test_message": test_message
        }
    )


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get the status of a background task"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        return ApiResponse(
            success=True,
            message="Task status retrieved",
            data={
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "info": result.info
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
