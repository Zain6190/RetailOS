from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    employee = relationship("Employee", uselist=False, back_populates="user")
    chat_histories = relationship("ChatHistory", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    reports = relationship("Report", back_populates="creator")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    salary = Column(Float, nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="employee")
    sales = relationship("Sale", back_populates="employee")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    loyalty_points = Column(Integer, default=0)
    date_created = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="customer")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(250), nullable=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    barcode = Column(String(100), nullable=True, index=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    image_url = Column(String(300), nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", uselist=False, back_populates="product", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product")
    pricing_histories = relationship("PricingHistory", back_populates="product")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    location = Column(String(100), nullable=True)
    reorder_level = Column(Integer, default=10, nullable=False)
    status = Column(String(50), default="In Stock")  # In Stock, Low Stock, Out of Stock
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    total_amount = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    payment_method = Column(String(50), default="Card")  # Cash, Card, Mobile, Online
    date_created = Column(DateTime, default=datetime.utcnow, index=True)

    customer = relationship("Customer", back_populates="sales")
    employee = relationship("Employee", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    order = relationship("Order", uselist=False, back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    status = Column(String(50), default="Pending")  # Pending, Shipped, Delivered, Cancelled
    shipping_address = Column(String(300), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale = relationship("Sale", back_populates="order")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(250), nullable=True)
    rating = Column(Float, default=5.0)
    date_created = Column(DateTime, default=datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(String(50), default="Draft")  # Draft, Sent, Received, Cancelled
    total_amount = Column(Float, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    delivery_date = Column(DateTime, nullable=True)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False, index=True)
    forecasted_quantity = Column(Float, nullable=False)
    confidence_interval = Column(Float, default=0.95)
    date_created = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="forecasts")


class PricingHistory(Base):
    __tablename__ = "pricing_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    change_reason = Column(String(250), nullable=True)
    date_changed = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="pricing_histories")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null means system-wide broadcast
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    type = Column(String(50), default="Info")  # Info, Alert, Action
    date_created = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="notifications")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    type = Column(String(50), nullable=False)  # Sales, Inventory, Financial
    format = Column(String(10), nullable=False)  # PDF, Excel, CSV
    file_url = Column(String(300), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="reports")


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    latency = Column(Float, nullable=True)  # in seconds
    token_count = Column(Integer, nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    message = Column(Text, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_histories")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    content = Column(Text, nullable=False)
    type = Column(String(50), default="Policy")  # Policy, Manual, Catalog
    file_url = Column(String(300), nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)

    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_content = Column(Text, nullable=False)
    vector_id = Column(String(100), nullable=True)  # ID referencing the vector index in Qdrant

    document = relationship("Document", back_populates="embeddings")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Pending")  # Pending, Completed
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

    assigned_to = relationship("User", backref="tasks")
