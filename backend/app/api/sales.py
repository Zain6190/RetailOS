from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.models.models import (
    Customer, Supplier, PurchaseOrder, PurchaseOrderItem, Sale, SaleItem, Order, Inventory, Notification, Product
)
from backend.app.schemas.schemas import (
    CustomerCreate, CustomerOut, SupplierCreate, SupplierOut,
    PurchaseOrderCreate, PurchaseOrderOut, SaleCreate, SaleOut, OrderOut, OrderUpdate
)
from backend.app.api.deps import get_current_admin, get_current_employee_or_admin
from backend.app.core.websocket import manager

router = APIRouter()

# --- Customer Endpoints ---

@router.get("/customers", response_model=List[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()

@router.post("/customers", response_model=CustomerOut)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_employee_or_admin)
):
    existing = db.query(Customer).filter(Customer.email == customer_in.email).first() if customer_in.email else None
    if existing:
        raise HTTPException(status_code=400, detail="Customer email already registered")
    
    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
        phone=customer_in.phone,
        address=customer_in.address,
        loyalty_points=customer_in.loyalty_points
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


# --- Supplier Endpoints ---

@router.get("/suppliers", response_model=List[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()

@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    supplier = Supplier(
        name=supplier_in.name,
        contact_person=supplier_in.contact_person,
        email=supplier_in.email,
        phone=supplier_in.phone,
        address=supplier_in.address,
        rating=supplier_in.rating
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


# --- Purchase Order Endpoints ---

@router.get("/purchase-orders", response_model=List[PurchaseOrderOut])
def list_purchase_orders(db: Session = Depends(get_db)):
    return db.query(PurchaseOrder).order_by(PurchaseOrder.date_created.desc()).all()

@router.post("/purchase-orders", response_model=PurchaseOrderOut)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_employee_or_admin)
):
    # Verify supplier
    supplier = db.query(Supplier).filter(Supplier.id == po_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    total_amount = 0.0
    po_items = []
    
    for item in po_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        
        total_amount += item.unit_cost * item.quantity
        po_items.append(PurchaseOrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost
        ))

    po = PurchaseOrder(
        supplier_id=po_in.supplier_id,
        status="Draft",
        total_amount=round(total_amount, 2),
        items=po_items
    )
    
    db.add(po)
    db.commit()
    db.refresh(po)
    return po

@router.put("/purchase-orders/{id}/status", response_model=PurchaseOrderOut)
async def update_po_status(
    id: int,
    status: str,  # Draft, Sent, Received, Cancelled
    db: Session = Depends(get_db),
    user=Depends(get_current_employee_or_admin)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    old_status = po.status
    po.status = status
    
    # If PO is received, increase inventory stocks
    if status == "Received" and old_status != "Received":
        po.delivery_date = datetime.utcnow()
        for item in po.items:
            inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
            if inv:
                inv.quantity += item.quantity
                # Update stock status
                if inv.quantity > inv.reorder_level:
                    inv.status = "In Stock"
                elif inv.quantity > 0:
                    inv.status = "Low Stock"
                else:
                    inv.status = "Out of Stock"
        
        # Broadcast stock updates
        payload = {
            "type": "STOCK_REPLENISHMENT",
            "po_id": po.id,
            "message": f"Purchase Order #{po.id} received. Restocked items."
        }
        await manager.broadcast(payload)
        
        # Log notification
        notif = Notification(
            title="PO Received & Restocked",
            message=f"Purchase Order #{po.id} from {po.supplier.name} has been processed. Stock levels updated.",
            type="Info"
        )
        db.add(notif)

    db.commit()
    db.refresh(po)
    return po


# --- Sales Endpoints ---

@router.get("/sales", response_model=List[SaleOut])
def list_sales(db: Session = Depends(get_db)):
    return db.query(Sale).order_by(Sale.date_created.desc()).all()

@router.post("/sales", response_model=SaleOut)
async def process_sale(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_employee_or_admin)
):
    total_amount = 0.0
    sale_items = []

    # Validate stock availability and calculate totals
    for item in sale_in.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        
        inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
        if not inv or inv.quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient inventory for {prod.name}. Available: {inv.quantity if inv else 0}"
            )
        
        # Deduct quantity from inventory
        inv.quantity -= item.quantity
        if inv.quantity == 0:
            inv.status = "Out of Stock"
        elif inv.quantity <= inv.reorder_level:
            inv.status = "Low Stock"
        else:
            inv.status = "In Stock"

        subtotal = item.unit_price * item.quantity
        total_amount += subtotal
        sale_items.append(SaleItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        ))

    # Apply tax and discount
    net_total = total_amount + sale_in.tax - sale_in.discount
    
    # Process Loyalty points (1 point per dollar spent)
    if sale_in.customer_id:
        cust = db.query(Customer).filter(Customer.id == sale_in.customer_id).first()
        if cust:
            cust.loyalty_points += int(net_total)

    sale = Sale(
        customer_id=sale_in.customer_id,
        employee_id=sale_in.employee_id,
        total_amount=round(net_total, 2),
        tax=sale_in.tax,
        discount=sale_in.discount,
        payment_method=sale_in.payment_method,
        items=sale_items
    )
    
    db.add(sale)
    db.commit()
    db.refresh(sale)

    # Automatically create shipping / collection Order
    order = Order(
        sale_id=sale.id,
        status="Pending",
        shipping_address="Store Pickup"
    )
    db.add(order)
    db.commit()

    # Trigger real-time WebSocket broadcast of the sale
    payload = {
        "type": "NEW_SALE",
        "sale_id": sale.id,
        "amount": sale.total_amount,
        "payment_method": sale.payment_method,
        "date": sale.date_created.isoformat()
    }
    await manager.broadcast(payload)

    # Check for automatic reorder trigger or notifications if stock became low
    for item in sale_items:
        inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
        if inv and inv.status in ["Low Stock", "Out of Stock"]:
            ws_alert = {
                "type": "STOCK_ALERT",
                "level": "warning" if inv.status == "Low Stock" else "critical",
                "product_name": inv.product.name,
                "sku": inv.product.sku,
                "quantity": inv.quantity,
                "reorder_level": inv.reorder_level
            }
            await manager.broadcast(ws_alert)

    return sale


# --- Order Endpoints ---

@router.get("/orders", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.date_created.desc()).all()

@router.put("/orders/{id}", response_model=OrderOut)
def update_order(
    id: int,
    order_in: OrderUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_employee_or_admin)
):
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=44, detail="Order not found")
    
    for field, value in order_in.dict(exclude_unset=True).items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order
