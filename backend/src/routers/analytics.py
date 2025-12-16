import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_verified_user
from src.models.user import User
from src.services.analytics_service import AnalyticsService
from src.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_analytics_overview(
    client_ids: Optional[str] = Query(None, description="ID банков через запятую"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AnalyticsService(db, redis_client)
    
    bank_ids = None
    if client_ids:
        try:
            bank_ids = [int(x.strip()) for x in client_ids.split(',')]
        except ValueError:
            return error_response("Неверный формат client_ids", 400)
    
    overview = service.get_user_overview(current_user.id, bank_ids)
    
    return success_response(overview)

@router.get("/categories")
async def get_categories_breakdown(
    start_date: Optional[str] = Query(None, description="Дата начала (ISO format)"),
    end_date: Optional[str] = Query(None, description="Дата окончания (ISO format)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AnalyticsService(db, redis_client)
    
    categories = service.get_categories_breakdown(current_user.id, start_date, end_date)
    
    return success_response(categories)

@router.get("/categories/list")
async def get_available_categories():
    from src.constants.mcc_mapping import CATEGORY_NAMES_RU
    from src.constants.constants import TransactionCategory
    
    categories = [
        {
            "id": cat.value,
            "name": CATEGORY_NAMES_RU.get(cat, cat.value)
        }
        for cat in TransactionCategory
    ]
    
    return success_response(categories)

@router.get("/insights")
async def get_advanced_insights(
    client_ids: Optional[str] = Query(None, description="ID банков через запятую"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Расширенная аналитика с выводами, советами и рекомендациями
    """
    redis_client = get_redis()
    service = AnalyticsService(db, redis_client)
    
    bank_ids = None
    if client_ids:
        try:
            bank_ids = [int(x.strip()) for x in client_ids.split(',')]
        except ValueError:
            return error_response("Неверный формат client_ids", 400)
    
    insights = service.get_advanced_insights(current_user.id, bank_ids)
    
    return success_response(insights)

