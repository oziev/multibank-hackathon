import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_user
from src.models.user import User
from src.models.bank_subscription import BankSubscription, SubscriptionStatus, ServiceType
from src.services.subscription_service import SubscriptionService
from src.utils.responses import success_response, error_response
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

class CreateSubscriptionRequest(BaseModel):
    bank_id: int = Field(..., alias="bankId")
    service_type: str = Field(..., alias="serviceType")  # card_issue, account_open, deposit, premium_service
    product_id: str = Field(..., alias="productId")
    account_id: Optional[int] = Field(None, alias="accountId")
    amount: Optional[float] = None
    term_months: Optional[int] = Field(None, alias="termMonths")
    partner_id: Optional[int] = Field(None, alias="partnerId")

    class Config:
        populate_by_name = True

@router.get("/products")
async def get_products(
    bank_id: int = Query(..., description="ID банка"),
    product_type: Optional[str] = Query(None, description="Тип продукта (card, deposit, loan, account)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить каталог доступных продуктов банка"""
    try:
        service = SubscriptionService(db, redis_client)
        products = service.get_available_products(current_user.id, bank_id, product_type)
        return success_response({"products": products})
    except Exception as e:
        logger.error(f"Ошибка получения продуктов: {e}")
        return error_response("Ошибка получения каталога продуктов", 500)

@router.get("")
async def get_subscriptions(
    bank_id: Optional[int] = Query(None, description="ID банка (опционально)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить список подписок пользователя"""
    try:
        service = SubscriptionService(db, redis_client)
        subscriptions = service.get_user_subscriptions(current_user.id, bank_id)
        
        result = []
        for sub in subscriptions:
            result.append({
                "id": sub.id,
                "bank_id": sub.bank_id,
                "service_type": sub.service_type.value,
                "product_id": sub.product_id,
                "status": sub.status.value,
                "subscription_date": sub.subscription_date.isoformat() if sub.subscription_date else None,
                "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
                "payment_consent_id": sub.payment_consent_id,
                "product_agreement_id": sub.product_agreement_id
            })

        return success_response({"subscriptions": result})
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return error_response("Ошибка получения списка подписок", 500)

@router.post("/bank-services")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Оформить подписку на банковскую услугу"""
    try:
        # Валидация типа услуги
        try:
            service_type = ServiceType(request.service_type)
        except ValueError:
            return error_response(f"Неподдерживаемый тип услуги: {request.service_type}", 400)

        service = SubscriptionService(db, redis_client)
        subscription, error = service.create_subscription(
            current_user.id,
            request.bank_id,
            service_type,
            request.product_id,
            request.account_id,
            request.amount,
            request.term_months,
            request.partner_id
        )

        if error:
            return error_response(error, 400)

        return success_response({
            "subscription_id": subscription.id,
            "status": subscription.status.value,
            "message": "Подписка успешно оформлена"
        }, 201)

    except Exception as e:
        logger.error(f"Ошибка создания подписки: {e}")
        return error_response("Ошибка создания подписки", 500)

@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Получить детали подписки"""
    try:
        subscription = db.query(BankSubscription).filter(
            BankSubscription.id == subscription_id,
            BankSubscription.user_id == current_user.id
        ).first()

        if not subscription:
            return error_response("Подписка не найдена", 404)

        result = {
            "id": subscription.id,
            "bank_id": subscription.bank_id,
            "service_type": subscription.service_type.value,
            "product_id": subscription.product_id,
            "status": subscription.status.value,
            "subscription_date": subscription.subscription_date.isoformat() if subscription.subscription_date else None,
            "cancelled_at": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            "payment_consent_id": subscription.payment_consent_id,
            "product_agreement_id": subscription.product_agreement_id,
            "product_agreement_consent_id": subscription.product_agreement_consent_id
        }

        if subscription.extra_data:
            import json
            result["metadata"] = json.loads(subscription.extra_data)

        return success_response(result)
    except Exception as e:
        logger.error(f"Ошибка получения подписки: {e}")
        return error_response("Ошибка получения деталей подписки", 500)

@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Отменить подписку"""
    try:
        service = SubscriptionService(db, redis_client)
        success, error = service.cancel_subscription(subscription_id, current_user.id)

        if error:
            return error_response(error, 400)

        return success_response({"message": "Подписка успешно отменена"})
    except Exception as e:
        logger.error(f"Ошибка отмены подписки: {e}")
        return error_response("Ошибка отмены подписки", 500)

