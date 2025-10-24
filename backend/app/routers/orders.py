from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Order, Customer, OrderItem, WhatsAppGroup
from app.schemas import (
    Order as OrderSchema,
    OrderCreate,
    OrderUpdate,
    OrderFilter,
    PaginatedResponse,
    ApiResponse
)

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get orders with pagination and filtering"""
    try:
        query = db.query(Order).join(Customer).join(WhatsAppGroup)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.phone_number.ilike(f"%{search}%"),
                    Order.notes.ilike(f"%{search}%")
                )
            )
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        orders = query.order_by(desc(Order.created_at)).offset(offset).limit(size).all()
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return PaginatedResponse(
            items=[OrderSchema.from_orm(order) for order in orders],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderSchema.from_orm(order)

@router.post("/", response_model=OrderSchema)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify group exists
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == order.group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Create order
        db_order = Order(
            customer_id=order.customer_id,
            group_id=order.group_id,
            message_id=order.message_id,
            order_time=order.order_time,
            status=order.status,
            notes=order.notes,
            raw_message=order.raw_message
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        # Create order items
        for item in order.order_items:
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                notes=item.notes
            )
            db.add(db_item)
        
        # Update customer total orders
        customer.total_orders += 1
        
        db.commit()
        db.refresh(db_order)
        
        return OrderSchema.from_orm(db_order)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: int, 
    order_update: OrderUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing order"""
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order fields
        update_data = order_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field != "order_items":
                setattr(db_order, field, value)
        
        # Update order items if provided
        if order_update.order_items is not None:
            # Delete existing items
            db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
            
            # Add new items
            for item in order_update.order_items:
                db_item = OrderItem(
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    notes=item.notes
                )
                db.add(db_item)
        
        db.commit()
        db.refresh(db_order)
        
        return OrderSchema.from_orm(db_order)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete an order"""
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update customer total orders
        customer = db.query(Customer).filter(Customer.id == db_order.customer_id).first()
        if customer:
            customer.total_orders = max(0, customer.total_orders - 1)
        
        db.delete(db_order)
        db.commit()
        
        return ApiResponse(
            success=True,
            message=f"Order {order_id} deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/dashboard")
async def get_dashboard_statistics(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Total orders
        total_orders = db.query(Order).count()
        
        # Total customers
        total_customers = db.query(Customer).count()
        
        # Total quantity
        total_quantity = db.query(OrderItem).with_entities(
            db.func.sum(OrderItem.quantity)
        ).scalar() or 0
        
        # Most ordered item
        most_ordered = db.query(
            OrderItem.product_name,
            db.func.sum(OrderItem.quantity).label('total_qty')
        ).group_by(OrderItem.product_name).order_by(
            desc('total_qty')
        ).first()
        
        most_ordered_item = most_ordered[0] if most_ordered else "N/A"
        
        # Recent orders (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_orders = db.query(Order).filter(
            Order.order_date >= week_ago
        ).count()
        
        # Orders by status
        status_counts = db.query(
            Order.status,
            db.func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        status_distribution = {status: count for status, count in status_counts}
        
        return ApiResponse(
            success=True,
            message="Dashboard statistics retrieved",
            data={
                "total_orders": total_orders,
                "total_customers": total_customers,
                "total_quantity": int(total_quantity),
                "most_ordered_item": most_ordered_item,
                "recent_orders": recent_orders,
                "status_distribution": status_distribution
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/top-items")
async def get_top_items(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Get top ordered items"""
    try:
        top_items = db.query(
            OrderItem.product_name,
            db.func.sum(OrderItem.quantity).label('total_quantity'),
            db.func.count(OrderItem.id).label('order_count')
        ).group_by(OrderItem.product_name).order_by(
            desc('total_quantity')
        ).limit(limit).all()
        
        items_data = [
            {
                "item": item.product_name,
                "total_quantity": int(item.total_quantity),
                "order_count": item.order_count
            }
            for item in top_items
        ]
        
        return ApiResponse(
            success=True,
            message=f"Top {len(items_data)} items retrieved",
            data=items_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/orders-over-time")
async def get_orders_over_time(days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db)):
    """Get orders over time"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        orders_by_date = db.query(
            db.func.date(Order.order_date).label('order_date'),
            db.func.count(Order.id).label('order_count')
        ).filter(
            Order.order_date >= start_date
        ).group_by(
            db.func.date(Order.order_date)
        ).order_by('order_date').all()
        
        date_data = [
            {
                "date": str(order.order_date),
                "orders": order.order_count
            }
            for order in orders_by_date
        ]
        
        return ApiResponse(
            success=True,
            message=f"Orders over last {days} days retrieved",
            data=date_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
