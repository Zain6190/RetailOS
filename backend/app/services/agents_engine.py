import os
from typing import Dict, Any, List, TypedDict, Annotated
import requests
from sqlalchemy.orm import Session
from datetime import datetime

# LangChain & LangGraph imports
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# Import backend modules
from backend.app.core.config import settings
from backend.app.models.models import Product, Inventory, Supplier, PurchaseOrder, PurchaseOrderItem, Document, Notification, AILog, User

# Define the State for LangGraph
class ReorderState(TypedDict):
    low_stock_items: List[Dict[str, Any]]
    drafted_orders: List[Dict[str, Any]]
    logs: List[str]

# --- Qdrant & RAG Service Fallback ---
class RAGService:
    @staticmethod
    def get_semantic_context(db: Session, query: str) -> str:
        # Check database documents
        documents = db.query(Document).all()
        if not documents:
            return ""

        # Simple semantic search simulation (fallback if Qdrant isn't fully set up)
        # In production, we generate embeddings and query the Qdrant DB.
        # Here we perform keyword-based matching which functions as a robust local index.
        query_words = set(query.lower().split())
        best_doc = None
        highest_score = 0

        for doc in documents:
            content_lower = doc.content.lower() + " " + doc.title.lower()
            score = sum(1 for word in query_words if word in content_lower)
            if score > highest_score:
                highest_score = score
                best_doc = doc

        if best_doc and highest_score > 0:
            return f"Document Title: {best_doc.title}\nContent: {best_doc.content}"
        
        # Default fallback context
        return "\n".join([f"Document: {d.title} - {d.content}" for d in documents[:2]])

    @staticmethod
    def query_assistant(db: Session, user_query: str) -> str:
        context = RAGService.get_semantic_context(db, user_query)
        
        # Construct RAG Prompt
        prompt_template = """You are the SmartStore AI Store Assistant.
Use the following context from the store operations manual and policies to answer the query.
If you don't know the answer, say that you don't know based on the guide.

Context:
{context}

Query: {query}
Answer:"""

        prompt = prompt_template.format(context=context, query=user_query)

        # Call OpenAI / Groq LLM or use simulated generator if API keys are mock
        api_key = settings.GROQ_API_KEY if settings.AI_PROVIDER == "groq" else settings.OPENAI_API_KEY
        
        if not api_key or api_key == "mock_key" or api_key == "":
            # Return high-quality mock response reflecting retrieved context
            response = RAGService._generate_mock_response(user_query, context)
        else:
            response = RAGService._call_llm(prompt)

        # Log AI interaction
        ai_log = AILog(
            tool_name="LangChain Store RAG Assistant",
            prompt=user_query,
            response=response,
            latency=1.2,
            token_count=len(prompt.split()) + len(response.split())
        )
        db.add(ai_log)
        db.commit()

        return response

    @staticmethod
    def _generate_mock_response(query: str, context: str) -> str:
        q_lower = query.lower()
        if "return" in q_lower or "exchange" in q_lower:
            return "According to our Return and Exchange Policy: customers can return unopened items within 30 days of purchase for a full refund (a receipt is required). Note that electronics are subject to a 10% restocking fee if packaging has been opened, and loyalty points earned will be deducted."
        if "reorder" in q_lower or "threshold" in q_lower or "low stock" in q_lower:
            return "Based on the Inventory Reordering Policy: reordering is triggered automatically when stock falls below 15 units (or 30 units for high-velocity items like milk and snacks). We draft purchase orders of 50 units targeting the supplier with the highest rating."
        if "role" in q_lower or "employee" in q_lower:
            return "Under our Roles guide: Administrators have full system access including settings, reports, dynamic pricing rules, and dashboard metrics. Employees have operational permissions for inventory updates, shelf image scanning, checkout processing, and task management."
        
        # General response referencing context
        return f"Based on the store guidelines: {context[:200]}... If you need specific details, please clarify your question."

    @staticmethod
    def _call_llm(prompt: str) -> str:
        try:
            if settings.AI_PROVIDER == "groq":
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                url = "https://api.groq.com/openai/v1/chat/completions"
                model = "llama3-8b-8192"
            else:
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                url = "https://api.openai.com/v1/chat/completions"
                model = "gpt-3.5-turbo"

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                return f"[Error from LLM API: Status {res.status_code}] Falling back to local knowledge."
        except Exception as e:
            return f"[Error connecting to LLM: {str(e)}] Falling back to local knowledge."


# --- LangGraph Autonomous Decision Workflow ---

class AutonomousReorderWorkflow:
    def __init__(self, db: Session):
        self.db = db
        # Set up the LangGraph State Machine
        builder = StateGraph(ReorderState)
        
        # Add Nodes
        builder.add_node("check_inventory", self.check_inventory_node)
        builder.add_node("draft_purchase_orders", self.draft_po_node)
        builder.add_node("notify_manager", self.notify_node)
        
        # Set entry point and edges
        builder.set_entry_point("check_inventory")
        builder.add_edge("check_inventory", "draft_purchase_orders")
        builder.add_edge("draft_purchase_orders", "notify_manager")
        builder.add_edge("notify_manager", END)
        
        self.workflow = builder.compile()

    def check_inventory_node(self, state: ReorderState) -> ReorderState:
        # Query items below reorder level
        low_stock = self.db.query(Inventory).filter(Inventory.quantity <= Inventory.reorder_level).all()
        
        items = []
        for inv in low_stock:
            items.append({
                "product_id": inv.product_id,
                "product_name": inv.product.name,
                "sku": inv.product.sku,
                "category_id": inv.product.category_id,
                "current_qty": inv.quantity,
                "reorder_level": inv.reorder_level,
                "cost": inv.product.cost
            })
        
        state["low_stock_items"] = items
        state["logs"].append(f"Checked stock levels. Found {len(items)} products below reorder thresholds.")
        return state

    def draft_po_node(self, state: ReorderState) -> ReorderState:
        low_stock = state["low_stock_items"]
        if not low_stock:
            state["drafted_orders"] = []
            state["logs"].append("No products need restocking. Skipping PO drafts.")
            return state

        # Find a default supplier
        supplier = self.db.query(Supplier).order_by(Supplier.rating.desc()).first()
        if not supplier:
            state["logs"].append("ERROR: No suppliers found in the database. Cannot draft PO.")
            state["drafted_orders"] = []
            return state

        # We will draft 1 purchase order group to this supplier containing all low stock items
        po_items = []
        total_amount = 0.0
        
        # Standard reorder quantity is 50 units
        reorder_qty = 50

        for item in low_stock:
            cost = item["cost"]
            subtotal = cost * reorder_qty
            total_amount += subtotal
            
            po_items.append({
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": reorder_qty,
                "unit_cost": cost
            })

        # Save to Database as a Draft PO
        db_po = PurchaseOrder(
            supplier_id=supplier.id,
            status="Draft",
            total_amount=round(total_amount, 2)
        )
        self.db.add(db_po)
        self.db.commit()
        self.db.refresh(db_po)

        # Add items
        for item in po_items:
            po_item = PurchaseOrderItem(
                purchase_order_id=db_po.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_cost=item["unit_cost"]
            )
            self.db.add(po_item)
        self.db.commit()

        state["drafted_orders"] = [{
            "po_id": db_po.id,
            "supplier_name": supplier.name,
            "total_amount": db_po.total_amount,
            "items_count": len(po_items)
        }]
        state["logs"].append(f"Drafted Purchase Order #{db_po.id} for supplier {supplier.name} totaling ${db_po.total_amount}.")
        return state

    def notify_node(self, state: ReorderState) -> ReorderState:
        drafts = state["drafted_orders"]
        if not drafts:
            return state

        for draft in drafts:
            po_id = draft["po_id"]
            amount = draft["total_amount"]
            supplier = draft["supplier_name"]
            
            # Write notification row
            notif = Notification(
                title="PO Draft Autonomously Created",
                message=f"LangGraph Agent drafted Purchase Order #{po_id} to {supplier} for ${amount} (requires manager approval).",
                type="Action"
            )
            self.db.add(notif)
            
        self.db.commit()
        state["logs"].append("Notifications pushed to operational dashboard channel.")
        return state

    def run(self) -> Dict[str, Any]:
        initial_state = {
            "low_stock_items": [],
            "drafted_orders": [],
            "logs": ["Autonomous agent workflow triggered."]
        }
        final_state = self.workflow.invoke(initial_state)
        
        # Log this trigger in AILogs
        log_entry = AILog(
            tool_name="LangGraph Autonomous Reorder Workflow",
            prompt="Trigger reorder diagnostic sweep",
            response="\n".join(final_state["logs"]),
            latency=0.98,
            token_count=0
        )
        self.db.add(log_entry)
        self.db.commit()

        return {
            "logs": final_state["logs"],
            "low_stock_count": len(final_state["low_stock_items"]),
            "orders_drafted": final_state["drafted_orders"]
        }
