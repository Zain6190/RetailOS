from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.models import (
    Role, User, Employee, Customer, Category, Product, Inventory,
    Sale, SaleItem, Order, Supplier, PurchaseOrder, PurchaseOrderItem,
    Forecast, PricingHistory, Notification, Document
)

def seed_db(db: Session):
    # 1. Seed Roles
    admin_role = db.query(Role).filter_by(name="Administrator").first()
    if not admin_role:
        admin_role = Role(name="Administrator", description="Full administrator system rights")
        employee_role = Role(name="Employee", description="Limited access rights for store activities")
        db.add_all([admin_role, employee_role])
        db.commit()
        db.refresh(admin_role)
        db.refresh(employee_role)
    else:
        employee_role = db.query(Role).filter_by(name="Employee").first()

    # 2. Seed Users
    admin_user = db.query(User).filter_by(email="admin@smartstore.ai").first()
    if not admin_user:
        admin_user = User(
            email="admin@smartstore.ai",
            hashed_password=get_password_hash("Admin123!"),
            full_name="Haris Admin",
            is_active=True,
            role_id=admin_role.id
        )
        staff_user = User(
            email="staff@smartstore.ai",
            hashed_password=get_password_hash("Staff123!"),
            full_name="John Staff",
            is_active=True,
            role_id=employee_role.id
        )
        db.add_all([admin_user, staff_user])
        db.commit()
        db.refresh(admin_user)
        db.refresh(staff_user)

        # Seed Employees
        admin_emp = Employee(user_id=admin_user.id, department="Management", position="General Manager", salary=6000.0)
        staff_emp = Employee(user_id=staff_user.id, department="Retail Store", position="Store Lead", salary=3200.0)
        db.add_all([admin_emp, staff_emp])
        db.commit()

    # 3. Seed Customers
    if db.query(Customer).count() == 0:
        c1 = Customer(name="Sarah Connor", email="sarah@skynet.com", phone="555-0199", address="123 Cyberdyne Way", loyalty_points=240)
        c2 = Customer(name="Bruce Wayne", email="bruce@waynecorp.com", phone="555-1939", address="Wayne Manor, Gotham", loyalty_points=1200)
        c3 = Customer(name="Clark Kent", email="clark@dailyplanet.com", phone="555-1938", address="345 Clinton St, Metropolis", loyalty_points=50)
        db.add_all([c1, c2, c3])
        db.commit()

    # 4. Seed Suppliers
    if db.query(Supplier).count() == 0:
        s1 = Supplier(name="Apex Distributors", contact_person="Peter Parker", email="peter@apex.com", phone="555-9080", address="Queens, NY", rating=4.8)
        s2 = Supplier(name="Global Goods Inc.", contact_person="Tony Stark", email="tony@globalgoods.com", phone="555-3000", address="Malibu, CA", rating=4.5)
        s3 = Supplier(name="Prime Foods Group", contact_person="Barry Allen", email="barry@primefoods.com", phone="555-4422", address="Central City", rating=4.2)
        db.add_all([s1, s2, s3])
        db.commit()

    # 5. Seed Categories & Products
    if db.query(Category).count() == 0:
        cat1 = Category(name="Electronics", description="Gadgets and power accessories")
        cat2 = Category(name="Beverages", description="Soft drinks, milk, and juices")
        cat3 = Category(name="Snacks", description="Chips, chocolates, and bars")
        cat4 = Category(name="Household", description="Soaps, detergents, and cleaning goods")
        db.add_all([cat1, cat2, cat3, cat4])
        db.commit()
        db.refresh(cat1)
        db.refresh(cat2)
        db.refresh(cat3)
        db.refresh(cat4)

        # Seed Products
        products = [
            Product(name="Wireless Earbuds", description="Noise cancelling wireless ear buds", sku="ELEC-001", category_id=cat1.id, barcode="4006381333931", price=89.99, cost=45.00),
            Product(name="USB-C Charging Cable", description="1.5 meter fast charging nylon braided cable", sku="ELEC-002", category_id=cat1.id, barcode="4006381333948", price=14.99, cost=4.50),
            Product(name="Power Bank 20k", description="20,000mAh portable charger with power delivery", sku="ELEC-003", category_id=cat1.id, barcode="4006381333955", price=39.99, cost=18.00),
            
            Product(name="Organic Almond Milk", description="Unsweetened organic almond milk 1L", sku="BEV-001", category_id=cat2.id, barcode="4006381333962", price=3.99, cost=1.80),
            Product(name="Sparkling Water 6-Pack", description="Lime flavored unsweetened sparkling water", sku="BEV-002", category_id=cat2.id, barcode="4006381333979", price=5.49, cost=2.50),
            Product(name="Energy Drink", description="Sugar-free taurine and caffeine booster", sku="BEV-003", category_id=cat2.id, barcode="4006381333986", price=2.99, cost=1.10),
            
            Product(name="Gourmet Potato Chips", description="Sea salt and vinegar hand-cooked chips", sku="SNA-001", category_id=cat3.id, barcode="4006381333993", price=3.49, cost=1.40),
            Product(name="Dark Chocolate Bar 70%", description="Single-origin organic dark chocolate", sku="SNA-002", category_id=cat3.id, barcode="4006381334006", price=4.29, cost=1.90),
            Product(name="Protein Bar Cookie Dough", description="20g protein low sugar snack bar", sku="SNA-003", category_id=cat3.id, barcode="4006381334013", price=2.79, cost=1.20),
            
            Product(name="Eco Dish Soap", description="Biodegradable plant-based dish washing liquid", sku="HOU-001", category_id=cat4.id, barcode="4006381334020", price=4.99, cost=2.00),
            Product(name="Paper Towels 4-Pack", description="Ultra absorbent double roll paper towels", sku="HOU-002", category_id=cat4.id, barcode="4006381334037", price=6.49, cost=3.00),
            Product(name="All-Purpose Cleaner Spray", description="Citrus scent cleaning spray", sku="HOU-003", category_id=cat4.id, barcode="4006381334044", price=5.99, cost=2.40)
        ]
        db.add_all(products)
        db.commit()

        # Seed Inventory & Price History for these products
        for prod in products:
            qty = 25 if "Milk" in prod.name or "Chips" in prod.name else 80
            if "Soap" in prod.name:
                qty = 8  # Trigger Low stock
            
            status = "In Stock"
            if qty <= 10:
                status = "Low Stock"
            elif qty == 0:
                status = "Out of Stock"

            inv = Inventory(
                product_id=prod.id,
                quantity=qty,
                location="Aisle A" if prod.category_id == cat1.id else "Aisle B",
                reorder_level=15,
                status=status
            )
            db.add(inv)

            ph = PricingHistory(
                product_id=prod.id,
                old_price=prod.price * 0.9,
                new_price=prod.price,
                change_reason="Initial pricing adjustment based on cost markup"
            )
            db.add(ph)
        db.commit()

    # 6. Seed Historical Sales (for charts)
    if db.query(Sale).count() == 0:
        custs = db.query(Customer).all()
        prods = db.query(Product).all()
        emps = db.query(Employee).all()

        now = datetime.now()
        # Seed 30 days of sales data
        for i in range(30, 0, -1):
            sale_date = now - timedelta(days=i)
            # Create 1-3 sales per day
            for s_idx in range(1, 3):
                # Pick customer/employee/products
                cust = custs[s_idx % len(custs)]
                emp = emps[s_idx % len(emps)]
                
                # Make 1-3 sale items
                sale_items = []
                total = 0.0
                for item_idx in range(1, 3):
                    prod = prods[(i + s_idx + item_idx) % len(prods)]
                    qty = (item_idx % 2) + 1
                    subtotal = prod.price * qty
                    total += subtotal
                    sale_items.append(SaleItem(product_id=prod.id, quantity=qty, unit_price=prod.price))
                
                sale = Sale(
                    customer_id=cust.id,
                    employee_id=emp.id,
                    total_amount=round(total, 2),
                    tax=round(total * 0.08, 2),
                    discount=0.0,
                    payment_method="Card" if s_idx % 2 == 0 else "Cash",
                    date_created=sale_date
                )
                db.add(sale)
                db.commit()
                db.refresh(sale)

                for item in sale_items:
                    item.sale_id = sale.id
                    db.add(item)
                
                # Create Order status
                order_status = "Delivered" if i > 2 else "Pending"
                ordr = Order(
                    sale_id=sale.id,
                    status=order_status,
                    shipping_address=cust.address,
                    tracking_number=f"TRK{1000000 + sale.id}"
                )
                db.add(ordr)
        db.commit()

    # 7. Seed Notifications
    if db.query(Notification).count() == 0:
        notifs = [
            Notification(title="Low Stock Alert", message="Eco Dish Soap has fallen below reorder level (current: 8, threshold: 15).", type="Alert"),
            Notification(title="Supplier Registered", message="Apex Distributors has completed registration and is ready for purchase orders.", type="Info"),
            Notification(title="System Ready", message="SmartStore AI Autonomous Retail System is initialized and online.", type="Info")
        ]
        db.add_all(notifs)
        db.commit()

    # 8. Seed Store Knowledge Documents (for RAG Assistant)
    if db.query(Document).count() == 0:
        docs = [
            Document(
                title="Return and Exchange Policy",
                content="Our store return policy allows customers to return unopened items within 30 days of purchase for a full refund. Original proof of purchase (receipt or digital invoice) is required. Loyalty points earned during the purchase will be deducted from the customer's loyalty account. For electronics, a 10% restocking fee applies if the product packaging is opened.",
                type="Policy"
            ),
            Document(
                title="Inventory Reordering and Threshold Policy",
                content="Store policy requires that inventory reordering occurs automatically or via supervisor confirmation when stock falls below the 'reorder level'. The reorder level is set to 15 units for standard items and 30 units for fast-moving consumer goods like milk and snacks. Orders must be submitted to the preferred supplier with the highest rating. The typical target order quantity is 50 units.",
                type="Policy"
            ),
            Document(
                title="Employee Roles and Safety Manual",
                content="Employees are divided into Administrator and Employee roles. Employees can update inventory levels, run shelf scans using the AI Stock Assistant, process sales transactions, and track assigned reorder tasks. Administrators retain full platform access, including setting dynamic pricing rules, executing financial forecasting, viewing supplier delivery ratings, and managing notifications.",
                type="Manual"
            )
        ]
        db.add_all(docs)
        db.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
