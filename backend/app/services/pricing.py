from sqlalchemy.orm import Session
from backend.app.models.models import Product, Inventory, PricingHistory, Forecast
from typing import Dict, Any

class PricingService:
    @staticmethod
    def evaluate_dynamic_pricing(db: Session, product_id: int) -> Dict[str, Any]:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": "Product not found"}

        inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        if not inventory:
            return {"product_id": product_id, "current_price": product.price, "recommended_price": product.price, "reason": "No inventory record"}

        # Base parameters
        current_price = product.price
        cost = product.cost
        qty = inventory.quantity
        reorder = inventory.reorder_level

        # Calculate markup margin (Price over Cost)
        min_price = cost * 1.20  # Minimum 20% margin
        recommended_price = current_price
        reason = "Price optimized based on stable supply and demand."

        # 1. Supply-based Adjustments (Scarcity vs Excess)
        if qty <= reorder:
            # Low stock -> increase price (scarcity markup)
            recommended_price = current_price * 1.10
            reason = f"Scarcity adjustment: Low stock ({qty} items remaining)."
        elif qty >= 100:
            # Overstocked -> discount price to increase velocity
            recommended_price = current_price * 0.90
            reason = f"Inventory velocity optimization: High stock level ({qty} items)."

        # 2. Demand-based Adjustments
        # Check if we have positive future forecasts
        latest_forecasts = db.query(Forecast).filter(Forecast.product_id == product_id).all()
        if latest_forecasts:
            avg_forecast = sum(f.forecasted_quantity for f in latest_forecasts) / len(latest_forecasts)
            if avg_forecast > 15.0:  # High projected demand threshold
                recommended_price *= 1.05
                reason += " Supplemented by high projected customer demand."

        # Ensure we never sell below our minimum safe margin
        if recommended_price < min_price:
            recommended_price = min_price
            reason = "Safety threshold: Price locked to maintain a minimum 20% profit margin over cost."

        recommended_price = round(recommended_price, 2)

        # 3. Apply changes and save history if price changes
        if recommended_price != current_price:
            product.price = recommended_price
            
            pricing_log = PricingHistory(
                product_id=product_id,
                old_price=current_price,
                new_price=recommended_price,
                change_reason=reason
            )
            db.add(pricing_log)
            db.commit()

        return {
            "product_id": product_id,
            "product_name": product.name,
            "current_price": current_price,
            "recommended_price": recommended_price,
            "difference": round(recommended_price - current_price, 2),
            "reason": reason
        }
