"""
Summary generation tasks for Celery
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from celery import current_task

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import (
    Order, Customer, OrderItem, WhatsAppGroup, OrderSummary
)

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="app.tasks.summary_generator.generate_daily_summary"
)
def generate_daily_summary(self, date_str: str = None, group_id: int = None):
    """Generate daily order summary"""
    db = get_db_session()
    try:
        # Parse date or use today
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()
        else:
            target_date = datetime.utcnow().date()

        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Generating summary for {target_date}'}
        )

        # Query orders for the target date
        query = db.query(Order).filter(
            Order.order_date == target_date
        )
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        orders = query.all()

        if not orders:
            return {
                "date": target_date.isoformat(),
                "message": "No orders found for this date",
                "summary": None
            }

        # Generate summary data
        customer_summaries = {}
        total_items = 0
        
        for order in orders:
            customer_id = order.customer_id
            if customer_id not in customer_summaries:
                customer_summaries[customer_id] = {
                    "customer_name": order.customer.name,
                    "customer_phone": order.customer.phone_number,
                    "orders": [],
                    "total_quantity": 0,
                    "items": {}
                }
            
            order_items = []
            for item in order.order_items:
                product_name = item.product_name
                quantity = item.quantity
                
                # Add to order items
                order_items.append({
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": item.unit_price,
                    "notes": item.notes
                })
                
                # Aggregate by product
                if product_name not in customer_summaries[customer_id]["items"]:
                    customer_summaries[customer_id]["items"][product_name] = 0
                customer_summaries[customer_id]["items"][product_name] += quantity
                customer_summaries[customer_id]["total_quantity"] += quantity
                total_items += quantity
            
            customer_summaries[customer_id]["orders"].append({
                "order_id": order.id,
                "order_time": order.order_time,
                "status": order.status,
                "items": order_items
            })

        # Convert to list format
        customers_list = []
        for customer_data in customer_summaries.values():
            items_list = [
                {"name": name, "quantity": qty} 
                for name, qty in customer_data["items"].items()
            ]
            
            customers_list.append({
                "customer_name": customer_data["customer_name"],
                "customer_phone": customer_data["customer_phone"],
                "items": items_list,
                "total_quantity": customer_data["total_quantity"],
                "total_orders": len(customer_data["orders"]),
                "orders": customer_data["orders"]
            })

        summary_data = {
            "date": target_date.isoformat(),
            "total_orders": len(orders),
            "total_customers": len(customer_summaries),
            "total_items": total_items,
            "customers": customers_list,
            "generated_at": datetime.utcnow().isoformat()
        }

        # Save summary to database
        order_summary = OrderSummary(
            summary_date=target_date,
            group_id=group_id,
            total_orders=len(orders),
            total_customers=len(customer_summaries),
            total_items=total_items,
            summary_data=summary_data
        )
        
        db.add(order_summary)
        db.commit()
        db.refresh(order_summary)

        logger.info(f"Generated summary for {target_date}: {len(orders)} orders, {len(customer_summaries)} customers")
        
        return {
            "summary_id": order_summary.id,
            "date": target_date.isoformat(),
            "summary": summary_data
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error generating daily summary: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.summary_generator.generate_weekly_summary"
)
def generate_weekly_summary(self, week_start_date: str = None, group_id: int = None):
    """Generate weekly order summary"""
    db = get_db_session()
    try:
        # Parse week start date or use current week
        if week_start_date:
            start_date = datetime.fromisoformat(week_start_date).date()
        else:
            today = datetime.utcnow().date()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Generating weekly summary from {start_date} to {end_date}'}
        )

        # Query orders for the week
        query = db.query(Order).filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        orders = query.all()

        # Group orders by date
        daily_summaries = {}
        week_totals = {
            "total_orders": 0,
            "total_customers": set(),
            "total_items": 0,
            "product_totals": {}
        }

        for order in orders:
            order_date = order.order_date.isoformat()
            if order_date not in daily_summaries:
                daily_summaries[order_date] = {
                    "date": order_date,
                    "orders": 0,
                    "customers": set(),
                    "items": 0
                }

            daily_summaries[order_date]["orders"] += 1
            daily_summaries[order_date]["customers"].add(order.customer_id)
            
            week_totals["total_orders"] += 1
            week_totals["total_customers"].add(order.customer_id)

            for item in order.order_items:
                quantity = item.quantity
                daily_summaries[order_date]["items"] += quantity
                week_totals["total_items"] += quantity
                
                product_name = item.product_name
                if product_name not in week_totals["product_totals"]:
                    week_totals["product_totals"][product_name] = 0
                week_totals["product_totals"][product_name] += quantity

        # Convert daily summaries
        daily_list = []
        for date, data in daily_summaries.items():
            daily_list.append({
                "date": date,
                "orders": data["orders"],
                "customers": len(data["customers"]),
                "items": data["items"]
            })

        # Convert product totals to list
        product_list = [
            {"name": name, "quantity": qty}
            for name, qty in sorted(week_totals["product_totals"].items(), 
                                  key=lambda x: x[1], reverse=True)
        ]

        summary_data = {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "total_orders": week_totals["total_orders"],
            "total_customers": len(week_totals["total_customers"]),
            "total_items": week_totals["total_items"],
            "daily_breakdown": sorted(daily_list, key=lambda x: x["date"]),
            "top_products": product_list,
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Generated weekly summary: {week_totals['total_orders']} orders")
        return summary_data

    except Exception as e:
        logger.error(f"Error generating weekly summary: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.summary_generator.generate_customer_summary"
)
def generate_customer_summary(self, customer_id: int, days_back: int = 30):
    """Generate summary for a specific customer"""
    db = get_db_session()
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Generating customer summary for customer {customer_id}'}
        )

        # Get customer
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Get recent orders
        cutoff_date = datetime.utcnow().date() - timedelta(days=days_back)
        orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.order_date >= cutoff_date
        ).order_by(Order.order_date.desc()).all()

        # Analyze order patterns
        order_patterns = {
            "total_orders": len(orders),
            "total_items": 0,
            "favorite_products": {},
            "order_frequency": {},
            "average_order_size": 0,
            "recent_orders": []
        }

        for order in orders:
            # Count items
            order_items_count = sum(item.quantity for item in order.order_items)
            order_patterns["total_items"] += order_items_count

            # Track favorite products
            for item in order.order_items:
                product_name = item.product_name
                if product_name not in order_patterns["favorite_products"]:
                    order_patterns["favorite_products"][product_name] = 0
                order_patterns["favorite_products"][product_name] += item.quantity

            # Track order frequency by day of week
            day_of_week = order.order_date.strftime("%A")
            if day_of_week not in order_patterns["order_frequency"]:
                order_patterns["order_frequency"][day_of_week] = 0
            order_patterns["order_frequency"][day_of_week] += 1

            # Add to recent orders
            order_patterns["recent_orders"].append({
                "order_id": order.id,
                "date": order.order_date.isoformat(),
                "time": order.order_time,
                "items_count": order_items_count,
                "status": order.status
            })

        # Calculate averages
        if order_patterns["total_orders"] > 0:
            order_patterns["average_order_size"] = round(
                order_patterns["total_items"] / order_patterns["total_orders"], 2
            )

        # Convert favorite products to sorted list
        favorite_products_list = [
            {"name": name, "total_quantity": qty}
            for name, qty in sorted(order_patterns["favorite_products"].items(),
                                  key=lambda x: x[1], reverse=True)
        ]

        summary_data = {
            "customer_id": customer_id,
            "customer_name": customer.name,
            "customer_phone": customer.phone_number,
            "analysis_period_days": days_back,
            "total_orders": order_patterns["total_orders"],
            "total_items": order_patterns["total_items"],
            "average_order_size": order_patterns["average_order_size"],
            "favorite_products": favorite_products_list[:10],  # Top 10
            "order_frequency_by_day": order_patterns["order_frequency"],
            "recent_orders": order_patterns["recent_orders"][:20],  # Last 20
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Generated customer summary for {customer.name}: {order_patterns['total_orders']} orders")
        return summary_data

    except Exception as e:
        logger.error(f"Error generating customer summary: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.summary_generator.generate_product_summary"
)
def generate_product_summary(self, days_back: int = 30):
    """Generate product popularity summary"""
    db = get_db_session()
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Analyzing product popularity'}
        )

        # Get recent orders
        cutoff_date = datetime.utcnow().date() - timedelta(days=days_back)
        order_items = db.query(OrderItem).join(Order).filter(
            Order.order_date >= cutoff_date
        ).all()

        product_stats = {}
        
        for item in order_items:
            product_name = item.product_name
            if product_name not in product_stats:
                product_stats[product_name] = {
                    "name": product_name,
                    "total_quantity": 0,
                    "total_orders": 0,
                    "customers": set(),
                    "average_quantity_per_order": 0
                }

            product_stats[product_name]["total_quantity"] += item.quantity
            product_stats[product_name]["total_orders"] += 1
            product_stats[product_name]["customers"].add(item.order.customer_id)

        # Calculate averages and convert to list
        products_list = []
        for stats in product_stats.values():
            stats["unique_customers"] = len(stats["customers"])
            stats["average_quantity_per_order"] = round(
                stats["total_quantity"] / stats["total_orders"], 2
            )
            # Remove the set (not JSON serializable)
            del stats["customers"]
            products_list.append(stats)

        # Sort by popularity (total quantity)
        products_list.sort(key=lambda x: x["total_quantity"], reverse=True)

        summary_data = {
            "analysis_period_days": days_back,
            "total_products": len(products_list),
            "total_orders_analyzed": len(set(item.order_id for item in order_items)),
            "products": products_list,
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Generated product summary: {len(products_list)} products analyzed")
        return summary_data

    except Exception as e:
        logger.error(f"Error generating product summary: {str(e)}")
        raise
    finally:
        db.close()