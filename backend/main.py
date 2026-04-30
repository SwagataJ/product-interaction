"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.kpis import router as kpi_router
from .api.store import router as store_router
from .api.events import router as events_router
from .api.chat import router as chat_router

app = FastAPI(
    title="Product Journey Tracker API",
    description="Backend for In-Store Product Journey Tracker — Westside Demo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpi_router)
app.include_router(store_router)
app.include_router(events_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"ok": True}
