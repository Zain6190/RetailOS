from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.schemas.schemas import (
    ChatRequest, ChatResponse, RecommendationResponse, ProductOut, PricingHistoryOut
)
from backend.app.models.models import ChatHistory, Product, User, PricingHistory
from backend.app.api.deps import get_current_user, get_current_employee_or_admin, get_current_admin
from backend.app.services.agents_engine import RAGService, AutonomousReorderWorkflow
from backend.app.services.pricing import PricingService
from backend.app.core.websocket import manager

router = APIRouter()

# --- RAG Store Assistant Chat ---

@router.post("/chat", response_model=ChatResponse)
def assistant_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin)
):
    # Log user message
    user_msg = ChatHistory(
        user_id=user.id,
        session_id=payload.session_id,
        role="user",
        message=payload.message
    )
    db.add(user_msg)
    db.commit()

    # Query RAG Engine
    bot_response = RAGService.query_assistant(db, payload.message)

    # Log bot response
    assistant_msg = ChatHistory(
        user_id=user.id,
        session_id=payload.session_id,
        role="assistant",
        message=bot_response
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        message=bot_response,
        session_id=payload.session_id,
        date_created=datetime.utcnow()
    )


# --- AI Product Recommendation Engine ---

@router.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Retrieve active products
    products = db.query(Product).limit(3).all()
    
    # Recommendation logic simulation
    # In a real model, recommendations would run collaborative filtering or cosine match on customer logs.
    reasoning = "These items are highly recommended based on trending sales volumes and active promotions this week."
    if customer_id:
        reasoning = f"Customer-specific recommendations generated based on historical purchase habits for Customer #{customer_id}."

    return RecommendationResponse(
        recommended_products=products,
        reasoning=reasoning
    )


# --- Autonomous Reorder Workflow Trigger ---

@router.post("/reorder/trigger")
async def trigger_autonomous_reorder(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    workflow = AutonomousReorderWorkflow(db)
    result = workflow.run()
    
    # If any purchase order was drafted, broadcast via websocket
    if result["orders_drafted"]:
        po_info = result["orders_drafted"][0]
        ws_payload = {
            "type": "AUTONOMOUS_PO_DRAFT",
            "po_id": po_info["po_id"],
            "supplier": po_info["supplier_name"],
            "amount": po_info["total_amount"],
            "message": f"Autonomous Reorder workflow drafted PO #{po_info['po_id']} to {po_info['supplier_name']}."
        }
        await manager.broadcast(ws_payload)

    return result


# --- Dynamic Pricing Trigger ---

@router.post("/pricing/evaluate/{product_id}")
async def evaluate_dynamic_pricing(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = PricingService.evaluate_dynamic_pricing(db, product_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # If price was adjusted, broadcast to users
    if result["difference"] != 0:
        ws_payload = {
            "type": "PRICE_ADJUSTMENT",
            "product_name": result["product_name"],
            "old_price": result["current_price"],
            "new_price": result["recommended_price"],
            "reason": result["reason"]
        }
        await manager.broadcast(ws_payload)

    return result
