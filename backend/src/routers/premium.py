"""
API роутер для Premium подписки
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.constants.constants import AccountType
from src.services.payment_service import PaymentService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/premium", tags=["Premium"])


class PurchasePremiumRequest(BaseModel):
    """Запрос на покупку Premium"""
    from_account_id: int = Field(..., alias='fromAccountId')
    
    class Config:
        populate_by_name = True


@router.post("/purchase", response_model=dict)
async def purchase_premium(
    request: PurchasePremiumRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Покупка Premium подписки
    
    Списывает 299₽ с указанного счета и обновляет тариф на Premium.
    Создает транзакцию в истории платежей.
    """
    logger.info(f"🚀 НАЧАЛО: Покупка Premium, пользователь {current_user.id}")
    logger.info(f"📦 Тело запроса: fromAccountId={request.from_account_id}")
    # Проверяем, не Premium ли уже (система проверки подписки)
    logger.info(f"🔍 Проверка подписки для пользователя {current_user.id}, текущий тип: {current_user.account_type}")
    
    if current_user.account_type == AccountType.PREMIUM:
        # Дополнительная проверка: есть ли активная Premium подписка в платежах
        from src.models.payment import Payment, PaymentType, PaymentStatus
        from datetime import datetime, timedelta
        
        # Проверяем последний Premium платеж
        last_premium_payment = db.query(Payment).filter(
            Payment.user_id == current_user.id,
            Payment.payment_type == PaymentType.PREMIUM,
            Payment.status == PaymentStatus.COMPLETED
        ).order_by(Payment.created_at.desc()).first()
        
        if last_premium_payment:
            # Premium подписка действует 30 дней
            subscription_duration = timedelta(days=30)
            subscription_expires = last_premium_payment.created_at + subscription_duration
            
            if datetime.utcnow() < subscription_expires:
                logger.warning(f"⚠️  У пользователя {current_user.id} уже есть активная Premium подписка до {subscription_expires}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"У вас уже активна подписка Premium до {subscription_expires.strftime('%d.%m.%Y')}"
                )
            else:
                logger.info(f"ℹ️  Подписка пользователя {current_user.id} истекла, можно продлить")
        else:
            logger.warning(f"⚠️  У пользователя {current_user.id} account_type=PREMIUM, но нет платежей")
            # Если нет платежей, но тип PREMIUM - сбрасываем на FREE
            current_user.account_type = AccountType.FREE
            db.commit()
    
    # Получаем account_id из request
    from_account_id = request.from_account_id
    logger.info(f"🔍 Получен from_account_id: {from_account_id}")
    
    if not from_account_id or from_account_id == 0:
        logger.error(f"❌ Не указан счет для списания")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указан счет для списания"
        )
    
    # Создаем платеж
    logger.info(f"💳 Создание платежа Premium для пользователя {current_user.id}, счет: {from_account_id}")
    payment, error = PaymentService.create_premium_payment(
        db,
        current_user.id,
        from_account_id,
        amount=299.0
    )
    
    if error:
        logger.error(f"❌ Ошибка создания платежа Premium: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    logger.info(f"✅ Платеж Premium успешно создан: {payment.id}")
    
    # Обновляем тариф пользователя на Premium
    current_user.account_type = AccountType.PREMIUM
    try:
        db.commit()
        db.refresh(current_user)
        logger.info(f"✅ Тип аккаунта пользователя {current_user.id} обновлен на PREMIUM")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка обновления типа аккаунта: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления типа аккаунта"
        )
    
    # Начисляем награду рефералу за покупку Premium
    try:
        from src.services.referral_service import ReferralService
        ReferralService.reward_premium_purchase(db, current_user.id)
        logger.info(f"Начислена награда рефералу за покупку Premium пользователем {current_user.id}")
    except Exception as e:
        logger.warning(f"Ошибка начисления награды рефералу: {e}")
        # Не блокируем покупку Premium, если ошибка с рефералом
    
    return {
        "success": True,
        "data": {
            "message": "🎉 Поздравляем! Вы перешли на Premium!",
            "accountType": current_user.account_type.value,
            "payment": {
                "id": payment.id,
                "amount": payment.amount,
                "status": payment.status.value,
                "createdAt": payment.created_at.isoformat()
            }
        }
    }


@router.get("/status", response_model=dict)
async def get_premium_status(
    current_user: User = Depends(get_current_user)
):
    """Проверить статус Premium подписки"""
    is_premium = current_user.account_type == AccountType.PREMIUM
    
    return {
        "success": True,
        "data": {
            "isPremium": is_premium,
            "accountType": current_user.account_type.value,
            "features": {
                "maxGroups": 5 if is_premium else 1,
                "maxMembers": 20 if is_premium else 2,
                "unlimitedBanks": is_premium,
                "prioritySupport": is_premium
            }
        }
    }

