"""
Customer Churn Prediction System — FastAPI application entrypoint.

Run with: uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import check_connection
from app.routers import datasets, olap, training, predictions
from app.routers.predictions import predict_router

app = FastAPI(
    title="Customer Churn Prediction System API",
    description="Backend API for dataset management, OLAP analytics, ML training, and churn prediction.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(olap.router)
app.include_router(training.router)
app.include_router(predictions.router)
app.include_router(predict_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Basic global error handler so unexpected failures don't leak stack traces."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/")
def root():
    return {
        "service": "Customer Churn Prediction System",
        "status": "running",
        "mongodb_connected": check_connection(),
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "mongodb_connected": check_connection(), "env": settings.env}
