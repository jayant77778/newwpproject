from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    delivered = "delivered"
    cancelled = "cancelled"

class MessageType(str, Enum):
    text = "text"
    image = "image"
    document = "document"
    audio = "audio"
    video = "video"

# Base schemas
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]{10,15}$')
    whatsapp_id: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

class Customer(CustomerBase):
    id: int
    is_active: bool
    total_orders: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Order Item schemas
class OrderItemBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., ge=1)
    unit_price: Optional[str] = None
    notes: Optional[str] = None

class OrderItemCreate(OrderItemBase):
    product_id: Optional[int] = None

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order schemas
class OrderBase(BaseModel):
    order_time: str = Field(..., pattern=r'^\d{1,2}:\d{2}\s?(AM|PM)$')
    status: OrderStatus = OrderStatus.pending
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    customer_id: int
    group_id: int
    message_id: Optional[str] = None
    raw_message: Optional[str] = None
    order_items: List[OrderItemCreate] = Field(..., min_items=1)

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    order_items: Optional[List[OrderItemCreate]] = None

class Order(OrderBase):
    id: int
    customer_id: int
    group_id: int
    message_id: Optional[str] = None
    order_date: datetime
    is_processed: bool
    created_at: datetime
    updated_at: datetime
    
    # Related objects
    customer: Customer
    order_items: List[OrderItem]
    
    class Config:
        from_attributes = True

# WhatsApp Group schemas
class WhatsAppGroupBase(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

class WhatsAppGroupCreate(WhatsAppGroupBase):
    group_id: str = Field(..., min_length=1, max_length=100)

class WhatsAppGroupUpdate(BaseModel):
    group_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class WhatsAppGroup(WhatsAppGroupBase):
    id: int
    group_id: str
    is_active: bool
    last_message_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# WhatsApp Message schemas
class WhatsAppMessageBase(BaseModel):
    message_content: str = Field(..., min_length=1)
    message_type: MessageType = MessageType.text
    sender_name: Optional[str] = None

class WhatsAppMessageCreate(WhatsAppMessageBase):
    message_id: str
    group_id: str
    sender_id: str
    timestamp: datetime
    extracted_data: Optional[Dict[str, Any]] = None

class WhatsAppMessage(WhatsAppMessageBase):
    id: int
    message_id: str
    group_id: str
    sender_id: str
    timestamp: datetime
    is_order: bool
    is_processed: bool
    extracted_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Summary schemas
class OrderSummaryItem(BaseModel):
    customer_name: str
    customer_phone: str
    items: List[Dict[str, Any]]
    total_quantity: int
    total_orders: int

class OrderSummaryResponse(BaseModel):
    summary_date: datetime
    total_orders: int
    total_customers: int
    total_items: int
    customers: List[OrderSummaryItem]
    
    class Config:
        from_attributes = True

# Export schemas
class ExportRequest(BaseModel):
    format: str = Field(..., pattern=r'^(excel|csv|pdf)$')
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    group_id: Optional[int] = None
    customer_id: Optional[int] = None
    include_items: bool = True

class ExportResponse(BaseModel):
    file_url: str
    file_name: str
    record_count: int
    created_at: datetime

# Filter schemas
class OrderFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    customer_id: Optional[int] = None
    group_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

# Response schemas
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
