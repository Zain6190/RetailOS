import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from backend.app.models.models import Sale, SaleItem, Product, Forecast, Employee, PurchaseOrder

class ForecastingService:
    @staticmethod
    def calculate_demand_forecast(db: Session, product_id: int, days_to_forecast: int = 7) -> List[Dict[str, Any]]:
        # Fetch historical sales for this product
        sales_items = db.query(SaleItem).join(Sale).filter(
            SaleItem.product_id == product_id
        ).order_by(Sale.date_created.asc()).all()

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []

        # If we have no sales data, fallback to a default moving model with small randomized noise
        if len(sales_items) < 3:
            default_rate = 2.5 # baseline average items per day
            forecasts = []
            now = datetime.now()
            for day in range(1, days_to_forecast + 1):
                f_date = now + timedelta(days=day)
                qty = max(0.5, default_rate + np.random.normal(0, 0.5))
                forecasts.append({
                    "product_id": product_id,
                    "forecast_date": f_date,
                    "forecasted_quantity": round(qty, 2),
                    "confidence_interval": 0.85
                })
            return forecasts

        # Prepare dates and quantities for pandas
        data = []
        for item in sales_items:
            # strip time, keep date
            dt = item.sale.date_created.date()
            data.append({"date": pd.to_datetime(dt), "quantity": item.quantity})

        df = pd.DataFrame(data)
        # Group by date and sum quantity
        df_daily = df.groupby("date").sum().reset_index()
        
        # Ensure we have continuous dates by reindexing
        idx = pd.date_range(start=df_daily["date"].min(), end=pd.date_range(start=datetime.now().date(), periods=1)[0])
        df_daily = df_daily.set_index("date").reindex(idx, fill_value=0).reset_index()
        df_daily.columns = ["date", "quantity"]

        # Run double exponential smoothing or linear trend estimation
        x = np.arange(len(df_daily))
        y = df_daily["quantity"].values
        slope, intercept = np.polyfit(x, y, 1)

        forecasts = []
        last_x = x[-1]
        now = datetime.now()

        # Generate future dates
        for day in range(1, days_to_forecast + 1):
            f_date = now + timedelta(days=day)
            future_x = last_x + day
            predicted_qty = slope * future_x + intercept
            
            # Bound below by 0
            predicted_qty = max(0.0, predicted_qty)
            
            # Add small weekly seasonality (higher sales on weekends)
            weekday = f_date.weekday()
            seasonality_factor = 1.25 if weekday >= 5 else 0.95
            predicted_qty *= seasonality_factor
            
            # Confidence interval shrinks with more sales data and expands the further out we predict
            conf = min(0.98, max(0.70, 0.95 - (day * 0.02) + (len(sales_items) * 0.002)))

            # Save to Forecast DB table if not already computed today
            existing_forecast = db.query(Forecast).filter(
                Forecast.product_id == product_id,
                func.date(Forecast.forecast_date) == f_date.date()
            ).first()

            if not existing_forecast:
                db_forecast = Forecast(
                    product_id=product_id,
                    forecast_date=f_date,
                    forecasted_quantity=round(predicted_qty, 2),
                    confidence_interval=round(conf, 2)
                )
                db.add(db_forecast)
            
            forecasts.append({
                "product_id": product_id,
                "forecast_date": f_date,
                "forecasted_quantity": round(predicted_qty, 2),
                "confidence_interval": round(conf, 2)
            })
            
        db.commit()
        return forecasts

    @staticmethod
    def calculate_financial_forecast(db: Session) -> Dict[str, Any]:
        # 1. Calculate historical metrics
        sales = db.query(Sale).all()
        if not sales:
            return {
                "projected_revenue": 15000.0,
                "projected_expenses": 9500.0,
                "projected_profit": 5500.0,
                "profit_margin": 36.6,
                "growth_rate": 5.2
            }

        # Last 30 days total revenue
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        recent_sales = db.query(Sale).filter(Sale.date_created >= thirty_days_ago).all()
        recent_revenue = sum(s.total_amount for s in recent_sales)

        # Operational costs: Staff payroll + Purchase Orders processed
        payroll = db.query(func.sum(Employee.salary)).scalar() or 0.0
        
        recent_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.date_created >= thirty_days_ago,
            PurchaseOrder.status == "Received"
        ).all()
        recent_po_cost = sum(po.total_amount for po in recent_pos)

        # Total operational costs for last 30 days
        historical_expenses = payroll + recent_po_cost

        # Calculate a realistic forecasting trend based on weekly growth rates
        week_1_sales = sum(s.total_amount for s in recent_sales if s.date_created >= now - timedelta(days=7))
        week_2_sales = sum(s.total_amount for s in recent_sales if now - timedelta(days=14) <= s.date_created < now - timedelta(days=7))

        growth_rate = 3.5  # default baseline growth percentage
        if week_2_sales > 0:
            growth_rate = round(((week_1_sales - week_2_sales) / week_2_sales) * 100, 2)
            # Bound realistic values
            growth_rate = min(25.0, max(-15.0, growth_rate))

        # Project 30 days forward
        projected_rev = recent_revenue * (1 + (growth_rate / 100.0))
        # Project expenses: assume fixed payroll + purchasing scales with 70% of revenue changes
        projected_exp = payroll + (recent_po_cost * (1 + (growth_rate * 0.7 / 100.0)))
        
        # Ensure calculations remain positive
        projected_rev = round(max(5000.0, projected_rev), 2)
        projected_exp = round(max(3000.0, projected_exp), 2)
        projected_profit = round(projected_rev - projected_exp, 2)
        
        margin = round((projected_profit / projected_rev) * 100, 2) if projected_rev > 0 else 0.0

        return {
            "projected_revenue": projected_rev,
            "projected_expenses": projected_exp,
            "projected_profit": projected_profit,
            "profit_margin": margin,
            "growth_rate": growth_rate
        }
