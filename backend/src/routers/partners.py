import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.models.partner import Partner, PartnerStatus
from src.services.partner_service import PartnerService
from src.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/partners", tags=["Partners"])

class CreatePartnerRequest(BaseModel):
    name: str
    commission_rate: float = Field(0.0, alias="commissionRate")
    contact_email: Optional[str] = Field(None, alias="contactEmail")
    contact_phone: Optional[str] = Field(None, alias="contactPhone")

    class Config:
        populate_by_name = True

class PartnerAuthRequest(BaseModel):
    api_key: str = Field(..., alias="apiKey")
    api_secret: str = Field(..., alias="apiSecret")

    class Config:
        populate_by_name = True

# Middleware для партнерской аутентификации
async def get_partner_from_header(
    x_partner_api_key: Optional[str] = Header(None, alias="X-Partner-API-Key"),
    db: Session = Depends(get_db)
) -> Optional[Partner]:
    """Получить партнера из заголовка API ключа"""
    if not x_partner_api_key:
        return None

    partner, error = PartnerService.authenticate_partner(db, x_partner_api_key)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return partner

@router.post("/register")
async def register_partner(
    request: CreatePartnerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Регистрация нового партнера (только для админов)"""
    # TODO: Добавить проверку прав администратора
    # if not current_user.is_admin:
    #     return error_response("Только администраторы могут создавать партнеров", 403)

    try:
        partner, error = PartnerService.create_partner(
            db,
            request.name,
            request.commission_rate,
            request.contact_email,
            request.contact_phone
        )

        if error:
            return error_response(error, 400)

        return success_response({
            "partner_id": partner.id,
            "name": partner.name,
            "api_key": partner.api_key,
            "api_secret": partner.api_secret,  # Возвращаем только при создании!
            "status": partner.status.value,
            "message": "Партнер успешно зарегистрирован. Сохраните API ключи!"
        }, 201)
    except Exception as e:
        logger.error(f"Ошибка регистрации партнера: {e}")
        return error_response("Ошибка регистрации партнера", 500)

@router.get("/{partner_id}/stats")
async def get_partner_stats(
    partner_id: int,
    partner: Optional[Partner] = Depends(get_partner_from_header),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику партнера"""
    # Проверяем, что запрос делает сам партнер или админ
    if partner and partner.id != partner_id:
        return error_response("Доступ запрещен", 403)

    try:
        stats = PartnerService.get_partner_stats(db, partner_id)
        return success_response(stats)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return error_response("Ошибка получения статистики", 500)

@router.get("/{partner_id}/transactions")
async def get_partner_transactions(
    partner_id: int,
    limit: int = Query(100, ge=1, le=1000),
    partner: Optional[Partner] = Depends(get_partner_from_header),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить транзакции партнера"""
    # Проверяем, что запрос делает сам партнер или админ
    if partner and partner.id != partner_id:
        return error_response("Доступ запрещен", 403)

    try:
        transactions = PartnerService.get_partner_transactions(db, partner_id, limit)
        
        result = []
        for txn in transactions:
            result.append({
                "id": txn.id,
                "user_id": txn.user_id,
                "transaction_type": txn.transaction_type,
                "amount": float(txn.amount),
                "commission": float(txn.commission),
                "status": txn.status,
                "created_at": txn.created_at.isoformat() if txn.created_at else None
            })

        return success_response({"transactions": result})
    except Exception as e:
        logger.error(f"Ошибка получения транзакций: {e}")
        return error_response("Ошибка получения транзакций", 500)

@router.post("/{partner_id}/subscriptions")
async def create_subscription_via_partner(
    partner_id: int,
    subscription_data: dict,
    partner: Partner = Depends(get_partner_from_header),
    db: Session = Depends(get_db)
):
    """Создать подписку через партнера (для партнерского API)"""
    if not partner or partner.id != partner_id:
        return error_response("Неверный API ключ партнера", 401)

    if partner.status != PartnerStatus.ACTIVE:
        return error_response("Партнер не активен", 403)

    try:
        from src.services.subscription_service import SubscriptionService
        from src.redis_client import get_redis
        from src.models.bank_subscription import ServiceType
        import redis

        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )

        service = SubscriptionService(db, redis_client)
        
        user_id = subscription_data.get("user_id")
        if not user_id:
            return error_response("user_id обязателен", 400)

        try:
            service_type = ServiceType(subscription_data.get("service_type"))
        except ValueError:
            return error_response(f"Неподдерживаемый тип услуги", 400)

        subscription, error = service.create_subscription(
            user_id,
            subscription_data.get("bank_id"),
            service_type,
            subscription_data.get("product_id"),
            subscription_data.get("account_id"),
            subscription_data.get("amount"),
            subscription_data.get("term_months"),
            partner_id
        )

        if error:
            return error_response(error, 400)

        # Создаем транзакцию партнера
        amount = subscription_data.get("amount", 0)
        PartnerService.create_partner_transaction(
            db,
            partner_id,
            user_id,
            "subscription",
            amount,
            {"subscription_id": subscription.id}
        )

        return success_response({
            "subscription_id": subscription.id,
            "status": subscription.status.value,
            "message": "Подписка успешно оформлена через партнера"
        }, 201)

    except Exception as e:
        logger.error(f"Ошибка создания подписки через партнера: {e}")
        return error_response("Ошибка создания подписки", 500)

