from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv
from datetime import datetime
from typing import List

from backend.app.core.database import get_db
from backend.app.schemas.schemas import ForecastOut, ReportOut, ReportCreate
from backend.app.models.models import Forecast, Report, Product, Sale, Inventory, User
from backend.app.services.forecasting import ForecastingService
from backend.app.api.deps import get_current_employee_or_admin, get_current_user

router = APIRouter()

# --- Forecasting Results ---

@router.get("/forecast/demand/{product_id}", response_model=List[ForecastOut])
def get_product_demand_forecast(
    product_id: int,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    user = Depends(get_current_employee_or_admin)
):
    # Verify product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    forecasts = ForecastingService.calculate_demand_forecast(db, product_id, days)
    
    # Retrieve from DB to match schemas
    db_forecasts = db.query(Forecast).filter(
        Forecast.product_id == product_id
    ).order_by(Forecast.forecast_date.asc()).limit(days).all()

    return db_forecasts


@router.get("/forecast/financials")
def get_financials_forecast(
    db: Session = Depends(get_db),
    user = Depends(get_current_employee_or_admin)
):
    return ForecastingService.calculate_financial_forecast(db)


# --- Reports Export ---

@router.get("/export")
def export_report_file(
    report_type: str = Query(..., regex="^(sales|inventory|financials)$"),
    format: str = Query("csv", regex="^(csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    output = io.StringIO()
    writer = csv.writer(output)

    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if report_type == "sales":
        # Write headers
        writer.writerow(["Sale ID", "Date", "Customer Name", "Employee Name", "Total Amount", "Tax", "Discount", "Payment Method"])
        sales = db.query(Sale).order_by(Sale.date_created.desc()).all()
        for sale in sales:
            cust_name = sale.customer.name if sale.customer else "Guest"
            emp_name = sale.employee.user.full_name if sale.employee else "POS Terminal"
            writer.writerow([
                sale.id, 
                sale.date_created.isoformat(), 
                cust_name, 
                emp_name, 
                sale.total_amount, 
                sale.tax, 
                sale.discount, 
                sale.payment_method
            ])
            
    elif report_type == "inventory":
        writer.writerow(["Inventory ID", "SKU", "Product Name", "Category", "Quantity", "Reorder Level", "Status", "Last Updated"])
        inv_items = db.query(Inventory).all()
        for item in inv_items:
            writer.writerow([
                item.id,
                item.product.sku,
                item.product.name,
                item.product.category.name,
                item.quantity,
                item.reorder_level,
                item.status,
                item.last_updated.isoformat()
            ])
            
    elif report_type == "financials":
        writer.writerow(["Metric", "Projected 30d Value"])
        metrics = ForecastingService.calculate_financial_forecast(db)
        for key, val in metrics.items():
            writer.writerow([key.replace("_", " ").title(), val])

    # Log report creation in DB
    db_report = Report(
        title=f"{report_type.title()} Report ({format.upper()})",
        type=report_type.title(),
        format=format.upper(),
        file_url=f"/api/v1/reports/export?report_type={report_type}&format={format}",
        created_by=user.id
    )
    db.add(db_report)
    db.commit()

    output.seek(0)
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")), 
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.get("/history", response_model=List[ReportOut])
def get_reports_history(
    db: Session = Depends(get_db),
    user = Depends(get_current_employee_or_admin)
):
    return db.query(Report).order_by(Report.date_created.desc()).all()
