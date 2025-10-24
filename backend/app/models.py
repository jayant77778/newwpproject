from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(100), unique=True, index=True, nullable=False)
    group_name = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    last_message_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="group")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    whatsapp_id = Column(String(100), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(String(50))  # Keeping as string for flexibility
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("whatsapp_groups.id"), nullable=False)
    message_id = Column(String(100), unique=True, index=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    order_time = Column(String(20))  # Format: "10:05 AM"
    status = Column(String(50), default="pending")  # pending, confirmed, delivered, cancelled
    notes = Column(Text)
    raw_message = Column(Text)  # Original WhatsApp message
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    group = relationship("WhatsAppGroup", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String(200), nullable=False)  # Store name even if product not in DB
    quantity = Column(Integer, nullable=False)
    unit_price = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), unique=True, index=True, nullable=False)
    group_id = Column(String(100), nullable=False)
    sender_id = Column(String(100), nullable=False)
    sender_name = Column(String(100))
    message_content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, image, document, etc.
    timestamp = Column(DateTime, nullable=False)
    is_order = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    extracted_data = Column(JSON)  # Store parsed order data
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderSummary(Base):
    __tablename__ = "order_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_date = Column(DateTime, default=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("whatsapp_groups.id"))
    total_orders = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    summary_data = Column(JSON)  # Store detailed summary
    file_path = Column(String(500))  # Path to exported file
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
