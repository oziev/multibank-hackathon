import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_user
from src.models.user import User
from src.services.cashback_service import CashbackService
from src.utils.responses import success_response, error_response
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cashback", tags=["Cashback"])

@router.get("/aggregate")
async def get_aggregate_cashback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить агрегированные данные о кешбеке"""
    try:
        service = CashbackService(db, redis_client)
        aggregated = service.aggregate_cashback(current_user.id)
        return success_response(aggregated)
    except Exception as e:
        logger.error(f"Ошибка получения агрегированных данных: {e}")
        return error_response("Ошибка получения данных о кешбеке", 500)

@router.get("/monthly")
async def get_monthly_cashback(
    month: Optional[str] = Query(None, description="Месяц в формате YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить кешбек за конкретный месяц или за текущий месяц"""
    try:
        if not month:
            month = datetime.now().strftime("%Y-%m")

        service = CashbackService(db, redis_client)
        cashback_data = service.get_or_create_cashback_data(current_user.id, month)
        
        result = {
            "month": month,
            "total_cashback": float(cashback_data.total_cashback),
            "transactions_count": cashback_data.transactions_count,
            "average_cashback_rate": float(cashback_data.average_cashback_rate),
            "categories_breakdown": {}
        }

        if cashback_data.categories_breakdown:
            import json
            result["categories_breakdown"] = json.loads(cashback_data.categories_breakdown)

        return success_response(result)
    except Exception as e:
        logger.error(f"Ошибка получения месячных данных: {e}")
        return error_response("Ошибка получения данных о кешбеке", 500)

@router.get("/categories")
async def get_categories_breakdown(
    month: Optional[str] = Query(None, description="Месяц в формате YYYY-MM (опционально)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить разбивку кешбека по категориям"""
    try:
        service = CashbackService(db, redis_client)
        breakdown = service.get_categories_breakdown(current_user.id, month)
        return success_response({"categories": breakdown})
    except Exception as e:
        logger.error(f"Ошибка получения разбивки по категориям: {e}")
        return error_response("Ошибка получения разбивки по категориям", 500)

@router.post("/consent")
async def create_consent(
    partner_id: Optional[int] = None,
    expires_days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Создать согласие на экспорт данных о кешбеке"""
    try:
        service = CashbackService(db, redis_client)
        consent = service.create_consent(current_user.id, partner_id, expires_days)
        return success_response({
            "consent_id": consent.id,
            "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
            "message": "Согласие на экспорт данных предоставлено"
        })
    except Exception as e:
        logger.error(f"Ошибка создания согласия: {e}")
        return error_response("Ошибка создания согласия", 500)

@router.post("/export")
async def export_cashback_data(
    partner_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Экспорт данных о кешбеке для партнера (требует согласия)"""
    try:
        service = CashbackService(db, redis_client)
        export_data, error = service.export_cashback_data(current_user.id, partner_id)
        
        if error:
            return error_response(error, 403)
        
        return success_response({
            "data": export_data,
            "exported_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        return error_response("Ошибка экспорта данных", 500)

