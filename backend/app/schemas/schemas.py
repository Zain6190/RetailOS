from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# Token & Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_id: int

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    role_id: int
    role: Optional[RoleOut] = None
    date_created: datetime
    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    category_id: int
    barcode: Optional[str] = None
    price: float
    cost: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    image_url: Optional[str] = None

class ProductOut(ProductBase):
    id: int
    date_created: datetime
    category: Optional[CategoryOut] = None
    class Config:
        from_attributes = True

# Inventory Schemas
class InventoryBase(BaseModel):
    product_id: int
    quantity: int
    location: Optional[str] = None
    reorder_level: int = 10

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    reorder_level: Optional[int] = None
    status: Optional[str] = None

class InventoryOut(InventoryBase):
    id: int
    status: str
    last_updated: datetime
    product: Optional[ProductOut] = None
    class Config:
        from_attributes = True

class ShelfDetectionRequest(BaseModel):
    image_data: str  # Base64 string of the uploaded shelf snapshot

class DetectedItem(BaseModel):
    product_id: int
    product_name: str
    confidence: float
    detected_count: int
    bbox: List[float]  # [x1, y1, x2, y2] relative bounding box coords

class ShelfDetectionResponse(BaseModel):
    detected_items: List[DetectedItem]
    annotated_image: str  # Base64 string of shelf image with bounding boxes overlayed
    message: str

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    loyalty_points: int = 0

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int
    date_created: datetime
    class Config:
        from_attributes = True

# Supplier Schemas
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rating: float = 5.0

class SupplierCreate(SupplierBase):
    pass

class SupplierOut(SupplierBase):
    id: int
    date_created: datetime
    class Config:
        from_attributes = True

# Purchase Order Schemas
class PurchaseOrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_cost: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemOut(PurchaseOrderItemBase):
    id: int
    product: Optional[ProductOut] = None
    class Config:
        from_attributes = True

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderOut(BaseModel):
    id: int
    supplier_id: int
    status: str
    total_amount: float
    date_created: datetime
    delivery_date: Optional[datetime] = None
    supplier: Optional[SupplierOut] = None
    items: List[PurchaseOrderItemOut] = []
    class Config:
        from_attributes = True

# Sale Schemas
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemOut(SaleItemBase):
    id: int
    product: Optional[ProductOut] = None
    class Config:
        from_attributes = True

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    employee_id: Optional[int] = None
    items: List[SaleItemCreate]
    tax: float = 0.0
    discount: float = 0.0
    payment_method: str = "Card"

class SaleOut(BaseModel):
    id: int
    customer_id: Optional[int] = None
    employee_id: Optional[int] = None
    total_amount: float
    tax: float
    discount: float
    payment_method: str
    date_created: datetime
    customer: Optional[CustomerOut] = None
    items: List[SaleItemOut] = []
    class Config:
        from_attributes = True

# Order Schemas
class OrderOut(BaseModel):
    id: int
    sale_id: int
    status: str
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    date_created: datetime
    date_updated: datetime
    sale: Optional[SaleOut] = None
    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None

# Forecast Schemas
class ForecastBase(BaseModel):
    product_id: int
    forecast_date: datetime
    forecasted_quantity: float
    confidence_interval: float = 0.95

class ForecastOut(ForecastBase):
    id: int
    date_created: datetime
    product: Optional[ProductOut] = None
    class Config:
        from_attributes = True

# Pricing History Schemas
class PricingHistoryOut(BaseModel):
    id: int
    product_id: int
    old_price: float
    new_price: float
    change_reason: Optional[str] = None
    date_changed: datetime
    product: Optional[ProductOut] = None
    class Config:
        from_attributes = True

# Notification Schemas
class NotificationBase(BaseModel):
    user_id: Optional[int] = None
    title: str
    message: str
    type: str = "Info"

class NotificationCreate(NotificationBase):
    pass

class NotificationOut(NotificationBase):
    id: int
    is_read: bool
    date_created: datetime
    class Config:
        from_attributes = True

# Report Schemas
class ReportCreate(BaseModel):
    title: str
    type: str  # Sales, Inventory, Financial
    format: str  # PDF, Excel, CSV

class ReportOut(BaseModel):
    id: int
    title: str
    type: str
    format: str
    file_url: str
    created_by: Optional[int] = None
    date_created: datetime
    class Config:
        from_attributes = True

# AI Assistant & recommendation Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str
    session_id: str
    date_created: datetime

class RecommendationResponse(BaseModel):
    recommended_products: List[ProductOut]
    reasoning: str


# Task Schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_id: int
    due_date: Optional[datetime] = None

class TaskStatusUpdate(BaseModel):
    status: str

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to_id: int
    date_created: datetime
    due_date: Optional[datetime] = None
    class Config:
        from_attributes = True

# Staff Overview Schema
class StaffOverviewOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None
    sales_count: int
    total_sales_amount: float
    pending_tasks_count: int
    completed_tasks_count: int
    tasks: List[TaskOut] = []
    last_activity: Optional[datetime] = None
    class Config:
        from_attributes = True
