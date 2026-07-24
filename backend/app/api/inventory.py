import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models.models import Category, Product, Inventory, AILog, Notification, User
from backend.app.schemas.schemas import (
    CategoryCreate, CategoryOut, ProductCreate, ProductOut, ProductUpdate,
    InventoryOut, InventoryUpdate, ShelfDetectionRequest, ShelfDetectionResponse, DetectedItem
)
from backend.app.api.deps import get_current_admin, get_current_employee_or_admin
from backend.app.core.websocket import manager

router = APIRouter()

# --- Categories Endpoints ---

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/categories", response_model=CategoryOut)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    category = Category(name=category_in.name, description=category_in.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

# --- Products Endpoints ---

@router.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.post("/products", response_model=ProductOut)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    product = Product(
        name=product_in.name,
        description=product_in.description,
        sku=product_in.sku,
        category_id=product_in.category_id,
        barcode=product_in.barcode,
        price=product_in.price,
        cost=product_in.cost,
        image_url=product_in.image_url
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Initialize inventory record for the new product
    inventory = Inventory(
        product_id=product.id,
        quantity=0,
        reorder_level=15,
        status="Out of Stock"
    )
    db.add(inventory)
    db.commit()

    return product

@router.put("/products/{id}", response_model=ProductOut)
def update_product(
    id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=44, detail="Product not found")
    
    for field, value in product_in.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{id}")
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=44, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# --- Inventory Endpoints ---

@router.get("/inventory", response_model=List[InventoryOut])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(Inventory).all()

@router.get("/inventory/low-stock", response_model=List[InventoryOut])
def list_low_stock(db: Session = Depends(get_db)):
    return db.query(Inventory).filter(Inventory.status == "Low Stock").all()

@router.put("/inventory/{id}", response_model=InventoryOut)
async def update_inventory_item(
    id: int,
    inventory_in: InventoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin)
):
    inv = db.query(Inventory).filter(Inventory.id == id).first()
    if not inv:
        raise HTTPException(status_code=44, detail="Inventory item not found")
    
    for field, value in inventory_in.dict(exclude_unset=True).items():
        setattr(inv, field, value)
    
    # Recalculate status
    if inv.quantity == 0:
        inv.status = "Out of Stock"
    elif inv.quantity <= inv.reorder_level:
        inv.status = "Low Stock"
    else:
        inv.status = "In Stock"

    db.commit()
    db.refresh(inv)

    # Broadcast real-time websocket alert if stock is low or out of stock
    if inv.status in ["Low Stock", "Out of Stock"]:
        payload = {
            "type": "STOCK_ALERT",
            "level": "warning" if inv.status == "Low Stock" else "critical",
            "product_name": inv.product.name,
            "sku": inv.product.sku,
            "quantity": inv.quantity,
            "reorder_level": inv.reorder_level
        }
        await manager.broadcast(payload)
        
        # Log notification
        notif = Notification(
            title=f"{inv.status} Alert",
            message=f"{inv.product.name} is now {inv.status.lower()} ({inv.quantity} units left).",
            type="Alert"
        )
        db.add(notif)
        db.commit()

    return inv

# --- AI Shelf Scan Detection ---

@router.post("/inventory/detect", response_model=ShelfDetectionResponse)
async def ai_shelf_detection(
    request: ShelfDetectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin)
):
    # Simulated YOLO Shelf Object Detection
    # In a real environment, you pass the base64 image data to an OCR / YOLO API.
    # Here, we simulate identifying items on the shelf and updating inventory.
    try:
        # Check that request image data is a valid base64 string
        base64.b64decode(request.image_data.split(",")[-1])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image encoding")

    # Pick 2 products in the database to update
    products = db.query(Product).limit(3).all()
    if not products:
        raise HTTPException(status_code=400, detail="No products seeded to run detection against")

    detected_items = []
    
    # We will simulate detecting products on a shelf
    # Product 1: Detected count 18 (Restocked)
    # Product 2: Detected count 6 (Low Stock warning triggered)
    mock_detections = [
        {"prod": products[0], "count": 18, "bbox": [0.1, 0.1, 0.4, 0.5], "conf": 0.94},
        {"prod": products[1] if len(products) > 1 else products[0], "count": 6, "bbox": [0.5, 0.1, 0.85, 0.6], "conf": 0.89}
    ]

    for item in mock_detections:
        prod = item["prod"]
        count = item["count"]
        
        # Find inventory for product and update quantity
        inv = db.query(Inventory).filter(Inventory.product_id == prod.id).first()
        if inv:
            inv.quantity = count
            if inv.quantity == 0:
                inv.status = "Out of Stock"
            elif inv.quantity <= inv.reorder_level:
                inv.status = "Low Stock"
            else:
                inv.status = "In Stock"
            db.commit()

            detected_items.append(DetectedItem(
                product_id=prod.id,
                product_name=prod.name,
                confidence=item["conf"],
                detected_count=count,
                bbox=item["bbox"]
            ))

            # Trigger WS Notification for updates
            payload = {
                "type": "SHELF_DETECTION",
                "product_name": prod.name,
                "sku": prod.sku,
                "detected_count": count,
                "status": inv.status
            }
            await manager.broadcast(payload)

    # Log the AI Activity
    ai_log = AILog(
        tool_name="YOLOv8 Shelf Stock Detector",
        prompt=f"Uploaded shelf scan snapshot (size: {len(request.image_data)} chars)",
        response=f"Detected: {[d.product_name for d in detected_items]}. Updated inventory records.",
        latency=0.74,
        token_count=0
    )
    db.add(ai_log)
    db.commit()

    return ShelfDetectionResponse(
        detected_items=detected_items,
        annotated_image=request.image_data,  # Echo back image (in real use, YOLO draws bounding boxes on canvas)
        message="AI shelf scan complete. Inventory updated successfully."
    )
