"""
Export generation tasks for Celery
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from celery import current_task

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import Order, Customer, OrderItem, WhatsAppGroup

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="app.tasks.export_generator.generate_export"
)
def generate_export(self, export_config: dict):
    """Generate export file based on configuration"""
    db = get_db_session()
    try:
        export_format = export_config.get("format", "excel")
        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Generating {export_format} export'}
        )

        # Build query based on filters
        query = db.query(Order).join(Customer).join(WhatsAppGroup)
        
        # Apply filters
        if export_config.get("date_from"):
            query = query.filter(Order.order_date >= export_config["date_from"])
        
        if export_config.get("date_to"):
            query = query.filter(Order.order_date <= export_config["date_to"])
        
        if export_config.get("customer_id"):
            query = query.filter(Order.customer_id == export_config["customer_id"])
        
        if export_config.get("group_id"):
            query = query.filter(Order.group_id == export_config["group_id"])
        
        if export_config.get("status"):
            query = query.filter(Order.status == export_config["status"])

        orders = query.order_by(Order.order_date.desc(), Order.created_at.desc()).all()

        if not orders:
            return {
                "success": False,
                "message": "No orders found matching the criteria"
            }

        current_task.update_state(
            state='PROCESSING',
            meta={'step': 'Preparing data for export'}
        )

        # Prepare data for export
        export_data = []
        
        for order in orders:
            base_row = {
                "Order ID": order.id,
                "Customer Name": order.customer.name,
                "Customer Phone": order.customer.phone_number,
                "Group Name": order.group.group_name,
                "Order Date": order.order_date.strftime("%Y-%m-%d"),
                "Order Time": order.order_time,
                "Status": order.status,
                "Notes": order.notes or ""
            }

            if export_config.get("include_items", True):
                # Include detailed items
                for item in order.order_items:
                    row = base_row.copy()
                    row.update({
                        "Product Name": item.product_name,
                        "Quantity": item.quantity,
                        "Unit Price": item.unit_price or "",
                        "Item Notes": item.notes or ""
                    })
                    export_data.append(row)
            else:
                # Summary only
                total_items = sum(item.quantity for item in order.order_items)
                items_list = ", ".join([f"{item.product_name} ({item.quantity})" for item in order.order_items])
                
                base_row.update({
                    "Total Items": total_items,
                    "Items Summary": items_list
                })
                export_data.append(base_row)

        # Create DataFrame
        df = pd.DataFrame(export_data)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)

        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Saving {export_format} file'}
        )

        if export_format.lower() == "excel":
            filename = f"orders_export_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Orders', index=False)
                
                # Add summary sheet
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
                        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        f"{export_config.get('date_from', 'All')} to {export_config.get('date_to', 'All')}"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

        elif export_format.lower() == "csv":
            filename = f"orders_export_{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            df.to_csv(filepath, index=False)

        elif export_format.lower() == "pdf":
            filename = f"orders_export_{timestamp}.pdf"
            filepath = os.path.join(export_dir, filename)
            
            # For PDF, we'll create a simplified format
            _generate_pdf_export(df, filepath, export_config)

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        file_size = os.path.getsize(filepath)
        
        logger.info(f"Generated {export_format} export: {filename} ({file_size} bytes)")
        
        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "file_size": file_size,
            "record_count": len(export_data),
            "format": export_format,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating export: {str(e)}")
        raise
    finally:
        db.close()


def _generate_pdf_export(df: pd.DataFrame, filepath: str, config: dict):
    """Generate PDF export using reportlab"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("WhatsApp Orders Export", title_style))
        story.append(Spacer(1, 12))

        # Export info
        info_style = styles['Normal']
        story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"Total Records: {len(df)}", info_style))
        story.append(Spacer(1, 20))

        # Prepare table data
        table_data = [df.columns.tolist()]  # Header
        
        # Limit rows for PDF (to avoid huge files)
        max_rows = 100
        if len(df) > max_rows:
            table_data.extend(df.head(max_rows).values.tolist())
            story.append(Paragraph(f"Note: Showing first {max_rows} records only", styles['Italic']))
        else:
            table_data.extend(df.values.tolist())

        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        doc.build(story)

    except ImportError:
        # Fallback: save as text file if reportlab not available
        with open(filepath.replace('.pdf', '.txt'), 'w') as f:
            f.write("WhatsApp Orders Export\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Records: {len(df)}\n\n")
            f.write(df.to_string(index=False))


@celery_app.task(
    bind=True,
    name="app.tasks.export_generator.generate_summary_export"
)
def generate_summary_export(self, summary_data: dict, export_format: str = "excel"):
    """Generate export from summary data"""
    try:
        current_task.update_state(
            state='PROCESSING',
            meta={'step': f'Generating summary {export_format} export'}
        )

        # Create DataFrame from summary data
        customers_data = []
        for customer in summary_data.get("customers", []):
            base_row = {
                "Customer Name": customer["customer_name"],
                "Customer Phone": customer["customer_phone"],
                "Total Orders": customer["total_orders"],
                "Total Quantity": customer["total_quantity"]
            }

            # Add items breakdown
            for item in customer["items"]:
                row = base_row.copy()
                row.update({
                    "Product Name": item["name"],
                    "Quantity": item["quantity"]
                })
                customers_data.append(row)

        df = pd.DataFrame(customers_data)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)

        if export_format.lower() == "excel":
            filename = f"summary_export_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Customer Summary', index=False)
                
                # Add overview sheet
                overview_data = {
                    "Metric": ["Date", "Total Orders", "Total Customers", "Total Items"],
                    "Value": [
                        summary_data.get("date", "N/A"),
                        summary_data.get("total_orders", 0),
                        summary_data.get("total_customers", 0),
                        summary_data.get("total_items", 0)
                    ]
                }
                overview_df = pd.DataFrame(overview_data)
                overview_df.to_excel(writer, sheet_name='Overview', index=False)

        elif export_format.lower() == "csv":
            filename = f"summary_export_{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            df.to_csv(filepath, index=False)

        file_size = os.path.getsize(filepath)
        
        logger.info(f"Generated summary {export_format} export: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "file_size": file_size,
            "record_count": len(customers_data),
            "format": export_format,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating summary export: {str(e)}")
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.export_generator.cleanup_old_exports"
)
def cleanup_old_exports(self, days_to_keep: int = 7):
    """Clean up old export files"""
    try:
        export_dir = "exports"
        if not os.path.exists(export_dir):
            return {"message": "Export directory does not exist"}

        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_files = []
        
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        deleted_files.append(filename)
                    except Exception as e:
                        logger.error(f"Error deleting file {filename}: {str(e)}")

        logger.info(f"Cleaned up {len(deleted_files)} old export files")
        return {
            "deleted_files": deleted_files,
            "total_deleted": len(deleted_files)
        }

    except Exception as e:
        logger.error(f"Error cleaning up exports: {str(e)}")
        raise