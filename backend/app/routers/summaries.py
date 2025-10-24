from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import defaultdict

from app.database import get_db
from app.models import Order, Customer, OrderItem, WhatsAppGroup
from app.schemas import OrderSummaryResponse, OrderSummaryItem, ApiResponse

router = APIRouter()

@router.get("/generate", response_model=ApiResponse)
async def generate_summary(
    group_id: int = None,
    db: Session = Depends(get_db)
):
    """Generate order summary grouped by customer"""
    try:
        # Build query
        query = db.query(Order).join(Customer).join(OrderItem)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        # Get all orders with items
        orders = query.all()
        
        if not orders:
            return ApiResponse(
                success=True,
                message="No orders found",
                data={
                    "summary_date": None,
                    "total_orders": 0,
                    "total_customers": 0,
                    "total_items": 0,
                    "customers": []
                }
            )
        
        # Group by customer
        customer_summary = defaultdict(lambda: {
            "customer_name": "",
            "customer_phone": "",
            "items": defaultdict(int),
            "total_quantity": 0,
            "total_orders": 0,
            "order_ids": set()
        })
        
        for order in orders:
            customer_key = f"{order.customer.name}_{order.customer.phone_number}"
            summary = customer_summary[customer_key]
            
            # Set customer info
            summary["customer_name"] = order.customer.name
            summary["customer_phone"] = order.customer.phone_number or "N/A"
            
            # Add order if not already counted
            if order.id not in summary["order_ids"]:
                summary["total_orders"] += 1
                summary["order_ids"].add(order.id)
            
            # Add items
            for item in order.order_items:
                summary["items"][item.product_name] += item.quantity
                summary["total_quantity"] += item.quantity
        
        # Convert to response format
        customers_data = []
        for customer_data in customer_summary.values():
            items_list = [
                {"item": item_name, "qty": qty}
                for item_name, qty in customer_data["items"].items()
            ]
            
            customers_data.append(OrderSummaryItem(
                customer_name=customer_data["customer_name"],
                customer_phone=customer_data["customer_phone"],
                items=items_list,
                total_quantity=customer_data["total_quantity"],
                total_orders=customer_data["total_orders"]
            ))
        
        # Sort by total quantity (descending)
        customers_data.sort(key=lambda x: x.total_quantity, reverse=True)
        
        # Calculate totals
        total_orders = len(orders)
        total_customers = len(customers_data)
        total_items = sum(item.total_quantity for item in customers_data)
        
        summary_response = OrderSummaryResponse(
            summary_date=orders[0].order_date if orders else None,
            total_orders=total_orders,
            total_customers=total_customers,
            total_items=total_items,
            customers=customers_data
        )
        
        return ApiResponse(
            success=True,
            message=f"Summary generated for {total_customers} customers",
            data=summary_response.dict()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-breakdown")
async def get_customer_breakdown(
    customer_id: int = None,
    group_id: int = None,
    db: Session = Depends(get_db)
):
    """Get detailed breakdown for specific customer or all customers"""
    try:
        query = db.query(Order).join(Customer).join(OrderItem)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        orders = query.all()
        
        # Group by customer
        breakdown = {}
        
        for order in orders:
            customer_key = order.customer.id
            
            if customer_key not in breakdown:
                breakdown[customer_key] = {
                    "customer_id": order.customer.id,
                    "customer_name": order.customer.name,
                    "customer_phone": order.customer.phone_number or "N/A",
                    "orders": [],
                    "total_orders": 0,
                    "total_items": 0,
                    "item_summary": defaultdict(int)
                }
            
            customer_data = breakdown[customer_key]
            
            # Add order details
            order_items = []
            order_total_qty = 0
            
            for item in order.order_items:
                order_items.append({
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "notes": item.notes
                })
                order_total_qty += item.quantity
                customer_data["item_summary"][item.product_name] += item.quantity
            
            customer_data["orders"].append({
                "order_id": order.id,
                "order_date": order.order_date.isoformat(),
                "order_time": order.order_time,
                "status": order.status,
                "items": order_items,
                "total_quantity": order_total_qty,
                "notes": order.notes
            })
            
            customer_data["total_orders"] += 1
            customer_data["total_items"] += order_total_qty
        
        # Convert defaultdict to regular dict
        for customer_data in breakdown.values():
            customer_data["item_summary"] = dict(customer_data["item_summary"])
        
        result = list(breakdown.values())
        
        return ApiResponse(
            success=True,
            message=f"Breakdown for {len(result)} customers",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/item-analysis")
async def get_item_analysis(
    group_id: int = None,
    db: Session = Depends(get_db)
):
    """Get analysis of ordered items"""
    try:
        query = db.query(OrderItem).join(Order)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        items = query.all()
        
        # Analyze items
        item_stats = defaultdict(lambda: {
            "total_quantity": 0,
            "order_count": 0,
            "customers": set(),
            "avg_quantity_per_order": 0
        })
        
        for item in items:
            stats = item_stats[item.product_name]
            stats["total_quantity"] += item.quantity
            stats["order_count"] += 1
            stats["customers"].add(item.order.customer_id)
        
        # Calculate averages and convert sets to counts
        analysis_result = []
        for item_name, stats in item_stats.items():
            stats["unique_customers"] = len(stats["customers"])
            stats["avg_quantity_per_order"] = round(
                stats["total_quantity"] / stats["order_count"], 2
            ) if stats["order_count"] > 0 else 0
            
            # Remove the set (not JSON serializable)
            del stats["customers"]
            
            analysis_result.append({
                "item_name": item_name,
                **stats
            })
        
        # Sort by total quantity
        analysis_result.sort(key=lambda x: x["total_quantity"], reverse=True)
        
        return ApiResponse(
            success=True,
            message=f"Analysis for {len(analysis_result)} items",
            data=analysis_result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/group-summary")
async def get_group_summary(db: Session = Depends(get_db)):
    """Get summary by WhatsApp groups"""
    try:
        groups = db.query(WhatsAppGroup).all()
        
        group_summaries = []
        
        for group in groups:
            # Get orders for this group
            orders = db.query(Order).filter(Order.group_id == group.id).all()
            
            if not orders:
                continue
            
            # Calculate group statistics
            total_orders = len(orders)
            unique_customers = len(set(order.customer_id for order in orders))
            
            # Get total items
            total_items = db.query(OrderItem).join(Order).filter(
                Order.group_id == group.id
            ).count()
            
            total_quantity = db.query(db.func.sum(OrderItem.quantity)).join(Order).filter(
                Order.group_id == group.id
            ).scalar() or 0
            
            # Most recent order
            latest_order = db.query(Order).filter(
                Order.group_id == group.id
            ).order_by(Order.order_date.desc()).first()
            
            group_summaries.append({
                "group_id": group.id,
                "group_name": group.group_name,
                "total_orders": total_orders,
                "unique_customers": unique_customers,
                "total_items": total_items,
                "total_quantity": int(total_quantity),
                "latest_order_date": latest_order.order_date.isoformat() if latest_order else None,
                "is_active": group.is_active
            })
        
        return ApiResponse(
            success=True,
            message=f"Summary for {len(group_summaries)} groups",
            data=group_summaries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
