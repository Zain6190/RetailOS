import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.init_db import init_db
from backend.app.core.websocket import manager

# Import routers
from backend.app.api.auth import router as auth_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.sales import router as sales_router
from backend.app.api.agents import router as agents_router
from backend.app.api.reports import router as reports_router
from backend.app.api.tasks import router as tasks_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SmartStore AI - Autonomous Retail Operating System API",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Startup Initialization
@app.on_event("startup")
def startup_event():
    print("Initializing SmartStore AI database...")
    init_db()
    print("Database initialization and seeding complete.")

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "system": "SmartStore AI Operating System Backend",
        "version": "1.0.0"
    }

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep connection open and listen for client messages (if any)
        while True:
            data = await websocket.receive_text()
            # Echo or process messages if required
            await websocket.send_json({"type": "System", "message": f"Received: {data}"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Include Router endpoints
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(inventory_router, prefix=f"{settings.API_V1_STR}/inventory", tags=["Inventory Management"])
app.include_router(sales_router, prefix=f"{settings.API_V1_STR}/sales", tags=["Sales Management"])
app.include_router(agents_router, prefix=f"{settings.API_V1_STR}/agents", tags=["AI & Agents"])
app.include_router(reports_router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reporting Engine"])
app.include_router(tasks_router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Task Management"])


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
