from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import os
from datetime import datetime
import json

from app.database import get_db
from app.models import Order, Customer, OrderItem, WhatsAppGroup
from app.schemas import ExportRequest, ExportResponse, ApiResponse

router = APIRouter()

# Create exports directory
EXPORT_DIR = "./exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@router.get("/excel")
async def export_to_excel(
    group_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    include_items: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Export orders to Excel file"""
    try:
        # Build query
        query = db.query(Order).join(Customer)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        
        orders = query.all()
        
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for export")
        
        # Prepare data
        export_data = []
        
        for order in orders:
            base_data = {
                "Order ID": order.id,
                "Customer Name": order.customer.name,
                "Customer Phone": order.customer.phone_number or "N/A",
                "Group": order.group.group_name if order.group else "N/A",
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Order Time": order.order_time,
                "Status": order.status,
                "Notes": order.notes or ""
            }
            
            if include_items and order.order_items:
                for item in order.order_items:
                    row_data = base_data.copy()
                    row_data.update({
                        "Item Name": item.product_name,
                        "Quantity": item.quantity,
                        "Unit Price": item.unit_price or "N/A",
                        "Item Notes": item.notes or ""
                    })
                    export_data.append(row_data)
            else:
                # Summary row without item details
                total_items = sum(item.quantity for item in order.order_items)
                base_data.update({
                    "Total Items": total_items,
                    "Item Summary": ", ".join([
                        f"{item.product_name} ({item.quantity})"
                        for item in order.order_items
                    ])
                })
                export_data.append(base_data)
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders_export_{timestamp}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main orders sheet
            df.to_excel(writer, sheet_name='Orders', index=False)
            
            # Summary sheet
            summary_data = {
                "Metric": [
                    "Total Orders",
                    "Total Customers", 
                    "Total Items",
                    "Export Date",
                    "Date Range"
                ],
                "Value": [
                    len(set(order.id for order in orders)),
                    len(set(order.customer_id for order in orders)),
                    sum(sum(item.quantity for item in order.order_items) for order in orders),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    f"{date_from or 'All'} to {date_to or 'All'}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv")
async def export_to_csv(
    group_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    include_items: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Export orders to CSV file"""
    try:
        # Build query (same as Excel)
        query = db.query(Order).join(Customer)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        
        orders = query.all()
        
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for export")
        
        # Prepare data (same logic as Excel)
        export_data = []
        
        for order in orders:
            base_data = {
                "Order ID": order.id,
                "Customer Name": order.customer.name,
                "Customer Phone": order.customer.phone_number or "N/A",
                "Group": order.group.group_name if order.group else "N/A",
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Order Time": order.order_time,
                "Status": order.status,
                "Notes": order.notes or ""
            }
            
            if include_items and order.order_items:
                for item in order.order_items:
                    row_data = base_data.copy()
                    row_data.update({
                        "Item Name": item.product_name,
                        "Quantity": item.quantity,
                        "Unit Price": item.unit_price or "N/A",
                        "Item Notes": item.notes or ""
                    })
                    export_data.append(row_data)
            else:
                total_items = sum(item.quantity for item in order.order_items)
                base_data.update({
                    "Total Items": total_items,
                    "Item Summary": ", ".join([
                        f"{item.product_name} ({item.quantity})"
                        for item in order.order_items
                    ])
                })
                export_data.append(base_data)
        
        # Create DataFrame and export to CSV
        df = pd.DataFrame(export_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders_export_{timestamp}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='text/csv'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary-excel")
async def export_summary_to_excel(
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Export customer summary to Excel file"""
    try:
        # Get summary data (reuse logic from summaries router)
        query = db.query(Order).join(Customer).join(OrderItem)
        
        if group_id:
            query = query.filter(Order.group_id == group_id)
        
        orders = query.all()
        
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for export")
        
        # Group by customer
        from collections import defaultdict
        
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
            
            summary["customer_name"] = order.customer.name
            summary["customer_phone"] = order.customer.phone_number or "N/A"
            
            if order.id not in summary["order_ids"]:
                summary["total_orders"] += 1
                summary["order_ids"].add(order.id)
            
            for item in order.order_items:
                summary["items"][item.product_name] += item.quantity
                summary["total_quantity"] += item.quantity
        
        # Convert to Excel format
        summary_rows = []
        detail_rows = []
        
        for customer_data in customer_summary.values():
            # Summary row per customer
            summary_rows.append({
                "Customer Name": customer_data["customer_name"],
                "Phone Number": customer_data["customer_phone"],
                "Total Orders": customer_data["total_orders"],
                "Total Quantity": customer_data["total_quantity"],
                "Items Summary": ", ".join([
                    f"{item}: {qty}" for item, qty in customer_data["items"].items()
                ])
            })
            
            # Detail rows per item
            for item_name, qty in customer_data["items"].items():
                detail_rows.append({
                    "Customer Name": customer_data["customer_name"],
                    "Phone Number": customer_data["customer_phone"],
                    "Item Name": item_name,
                    "Quantity": qty
                })
        
        # Create Excel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"customer_summary_{timestamp}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Customer summary sheet
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name='Customer Summary', index=False)
            
            # Item details sheet
            detail_df = pd.DataFrame(detail_rows)
            detail_df.to_excel(writer, sheet_name='Item Details', index=False)
            
            # Statistics sheet
            stats_data = {
                "Metric": [
                    "Total Customers",
                    "Total Orders",
                    "Total Items",
                    "Export Date"
                ],
                "Value": [
                    len(summary_rows),
                    sum(row["Total Orders"] for row in summary_rows),
                    sum(row["Total Quantity"] for row in summary_rows),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp-data")
async def export_whatsapp_data(
    group_id: int,
    format: str = Query("json", regex="^(json|excel)$"),
    db: Session = Depends(get_db)
):
    """Export raw WhatsApp data for a group"""
    try:
        from app.models import WhatsAppMessage
        
        # Get group
        group = db.query(WhatsAppGroup).filter(WhatsAppGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Get messages
        messages = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.group_id == group.group_id
        ).order_by(WhatsAppMessage.timestamp.desc()).all()
        
        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for this group")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            # JSON export
            export_data = {
                "group_name": group.group_name,
                "group_id": group.group_id,
                "export_date": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": [
                    {
                        "message_id": msg.message_id,
                        "sender_name": msg.sender_name,
                        "content": msg.message_content,
                        "timestamp": msg.timestamp.isoformat(),
                        "is_order": msg.is_order,
                        "extracted_data": msg.extracted_data
                    }
                    for msg in messages
                ]
            }
            
            filename = f"whatsapp_data_{group.group_name}_{timestamp}.json"
            filepath = os.path.join(EXPORT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return FileResponse(
                path=filepath,
                filename=filename,
                media_type='application/json'
            )
        
        else:  # Excel format
            message_data = []
            for msg in messages:
                message_data.append({
                    "Message ID": msg.message_id,
                    "Sender": msg.sender_name,
                    "Content": msg.message_content,
                    "Timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Is Order": "Yes" if msg.is_order else "No",
                    "Processed": "Yes" if msg.is_processed else "No",
                    "Extracted Data": str(msg.extracted_data) if msg.extracted_data else ""
                })
            
            df = pd.DataFrame(message_data)
            
            filename = f"whatsapp_data_{group.group_name}_{timestamp}.xlsx"
            filepath = os.path.join(EXPORT_DIR, filename)
            
            df.to_excel(filepath, index=False)
            
            return FileResponse(
                path=filepath,
                filename=filename,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_export_files():
    """List all available export files"""
    try:
        files = []
        
        if os.path.exists(EXPORT_DIR):
            for filename in os.listdir(EXPORT_DIR):
                filepath = os.path.join(EXPORT_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return ApiResponse(
            success=True,
            message=f"Found {len(files)} export files",
            data=files
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{filename}")
async def download_export_file(filename: str):
    """Download a specific export file"""
    try:
        filepath = os.path.join(EXPORT_DIR, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine media type based on extension
        if filename.endswith('.xlsx'):
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            media_type = 'text/csv'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
