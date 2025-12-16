from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.config import settings
from src.database import create_tables
from src.redis_client import redis_client

from src.routers import auth, accounts, groups, analytics, loyalty_cards, payments, premium, savings, family_budget, verification, referrals, cashback, subscriptions, partners, mock_bank

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Bank Aggregator API...")
    print(f"📊 Database: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    print(f"💾 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    create_tables()

    try:
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    print("✨ Application started successfully!")

    yield

    print("👋 Shutting down Bank Aggregator API...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API для агрегации банковских счетов",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_details = traceback.format_exc() if settings.DEBUG else None
    print(f"❌ Global Error Handler: {exc}")
    if error_details:
        print(f"📋 Traceback:\n{error_details}")
    
    # Если это HTTPException, возвращаем его как есть
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.detail
                }
            }
        )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Что-то пошло не так" if not settings.DEBUG else str(exc)
            }
        }
    )

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(groups.router)
app.include_router(analytics.router)
app.include_router(loyalty_cards.router)
app.include_router(payments.router)
app.include_router(premium.router)
app.include_router(savings.router)
app.include_router(family_budget.router)
app.include_router(verification.router)
app.include_router(referrals.router)
app.include_router(cashback.router)
app.include_router(subscriptions.router)
app.include_router(partners.router)
app.include_router(mock_bank.router)

@app.get("/", tags=["Health"])
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    }

@app.get("/health", tags=["Health"])
async def health():
    redis_status = "healthy"
    try:
        redis_client.ping()
    except:
        redis_status = "unhealthy"

    return {
        "success": True,
        "data": {
            "api": "healthy",
            "redis": redis_status,
            "version": settings.APP_VERSION
        }
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
