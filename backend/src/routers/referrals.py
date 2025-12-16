import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.services.referral_service import ReferralService
from src.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/referrals", tags=["Referrals"])

@router.get("/my-code")
async def get_my_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить свой реферальный код"""
    try:
        code = ReferralService.get_or_create_referral_code(db, current_user.id)
        return success_response({
            "referral_code": code,
            "referral_link": f"https://bank-aggregator.app/sign-up?ref={code}"
        })
    except Exception as e:
        logger.error(f"Ошибка получения реферального кода: {e}")
        return error_response("Ошибка получения реферального кода", 500)

@router.post("/regenerate-code")
async def regenerate_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить (регенерировать) реферальный код"""
    try:
        # Сбрасываем текущий код
        current_user.referral_code = None
        db.commit()
        
        # Генерируем новый код
        code = ReferralService.get_or_create_referral_code(db, current_user.id)
        return success_response({
            "referral_code": code,
            "referral_link": f"https://bank-aggregator.app/sign-up?ref={code}",
            "message": "Реферальный код успешно обновлен"
        })
    except Exception as e:
        logger.error(f"Ошибка обновления реферального кода: {e}")
        return error_response("Ошибка обновления реферального кода", 500)

@router.get("/stats")
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику рефералов"""
    try:
        stats = ReferralService.get_referral_stats(db, current_user.id)
        return success_response(stats)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return error_response("Ошибка получения статистики", 500)

@router.get("/list")
async def get_referral_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список приглашенных пользователей"""
    try:
        referrals = ReferralService.get_referral_list(db, current_user.id)
        return success_response({"referrals": referrals})
    except Exception as e:
        logger.error(f"Ошибка получения списка рефералов: {e}")
        return error_response("Ошибка получения списка рефералов", 500)

@router.post("/claim-reward")
async def claim_reward(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Запросить выплату награды"""
    try:
        success, message = ReferralService.claim_reward(db, current_user.id)
        if success:
            return success_response({"message": message})
        else:
            return error_response(message, 400)
    except Exception as e:
        logger.error(f"Ошибка запроса выплаты: {e}")
        return error_response("Ошибка запроса выплаты", 500)

@router.get("/validate/{code}")
async def validate_referral_code(
    code: str,
    db: Session = Depends(get_db)
):
    """Проверить валидность реферального кода"""
    try:
        user, error = ReferralService.validate_referral_code(db, code)
        if error or not user:
            return error_response(error or "Реферальный код не найден", 404)
        
        return success_response({
            "valid": True,
            "referrer_name": user.name
        })
    except Exception as e:
        logger.error(f"Ошибка проверки кода: {e}")
        return error_response("Ошибка проверки кода", 500)

