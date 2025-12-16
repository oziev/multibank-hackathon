"""
API роутер для верификации телефона
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Optional
from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.services.otp_service import OTPService
from src.utils.responses import success_response, error_response

router = APIRouter(prefix="/api/verification", tags=["Verification"])

@router.post("/send-phone-code")
async def send_phone_verification_code(
    request: dict = Body(default={}),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отправить код подтверждения на телефон"""
    # Если передан phone в запросе, обновляем телефон пользователя
    phone = request.get('phone') if request else None
    if phone:
        # Обновляем телефон пользователя
        current_user.phone = phone
        db.commit()
        db.refresh(current_user)
    elif not current_user.phone:
        return error_response("Номер телефона не указан", 400)
    
    phone_to_use = current_user.phone
    otp_code = OTPService.generate_otp_code(db, phone_to_use)
    
    # В реальности здесь была бы отправка SMS
    # Сейчас просто логируем
    print(f"📱 SMS код для {phone_to_use}: {otp_code}")
    
    return success_response({
        "message": f"Код отправлен на {phone_to_use}",
        "phone": phone_to_use,
        "otpCode": otp_code  # Для разработки
    })

@router.post("/verify-phone")
async def verify_phone(
    request: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Подтвердить номер телефона кодом"""
    code = request.get('code')
    if not code:
        return error_response("Код не указан", 400)
    
    if not current_user.phone:
        return error_response("Номер телефона не указан", 400)
    
    # Используем verify_otp с phone как email (OTPCode хранит в поле email)
    is_valid, error_msg = OTPService.verify_otp(db, current_user.phone, code)
    
    if not is_valid:
        return error_response(error_msg or "Неверный код", 400)
    
    # Помечаем телефон как подтвержденный
    # (можно добавить поле phone_verified в модель User)
    
    return success_response({
        "message": "Номер телефона подтвержден",
        "phone": current_user.phone
    })

