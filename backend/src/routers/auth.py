import logging
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_user, get_current_verified_user
from src.schemas.auth import (
    SignUpRequest,
    SignUpResponse,
    VerifyEmailRequest,
    SignInRequest,
    SignInResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetVerify
)
from src.schemas.profile import ProfileUpdateRequest
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.session_service import SessionService
from src.services.otp_service import OTPService
from src.utils.responses import success_response, error_response
from src.config import settings
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/sign-up")
async def sign_up(
    request: SignUpRequest,
    db: Session = Depends(get_db)
):
    user, error = AuthService.create_user(
        db,
        request.email,
        request.password,
        request.name,
        request.phone,
        request.birth_date,
        request.referral_code
    )

    if error:
        return error_response(error, 400)

    otp_code = OTPService.generate_otp_code(db, user.email)
    OTPService.send_otp_email(user.email, otp_code)

    return success_response({
        "message": "Регистрация успешна! Проверьте email для подтверждения.",
        "email": user.email,
        "phone": user.phone,
        "otpCode": otp_code  # Всегда возвращаем для разработки
    }, 201)

@router.post("/send-otp")
async def send_otp(
    request: dict,
    db: Session = Depends(get_db)
):
    """Отправить код подтверждения на email"""
    email = request.get('email')
    if not email:
        return error_response("Email не указан", 400)
    
    try:
        otp_code = OTPService.generate_otp_code(db, email)
        OTPService.send_otp_email(email, otp_code)
        
        return success_response({
            "message": f"Код отправлен на {email}",
            "email": email,
            "otpCode": otp_code  # Для разработки
        })
    except Exception as e:
        logger.error(f"Ошибка отправки OTP: {e}")
        return error_response("Ошибка отправки кода", 500)

@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    is_valid, error = OTPService.verify_otp(db, request.email, request.code)

    if not is_valid:
        return error_response(error, 400)

    user = AuthService.verify_user(db, request.email)
    if not user:
        return error_response("Пользователь не найден", 404)

    session_id = SessionService.create_session(redis_client, user.id)

    json_response = success_response({
        "message": "Email подтверждён! Вы автоматически вошли в систему.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "birthDate": str(user.birth_date),
            "accountType": user.account_type.value,
            "isVerified": user.is_verified
        }
    })

    json_response.set_cookie(
        key="session-id",
        value=session_id,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )

    return json_response

@router.post("/sign-in")
async def sign_in(
    request: SignInRequest,
    response: Response,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    user, error = AuthService.authenticate_user(db, request.email, request.password)

    if error:
        return error_response(error, 401)

    session_id = SessionService.create_session(redis_client, user.id)

    json_response = success_response({
        "message": "Вход выполнен успешно",
        "user": {
            "id": user.id,
            "name": user.name,
            "birthDate": str(user.birth_date),
            "accountType": user.account_type.value
        }
    })

    json_response.set_cookie(
        key="session-id",
        value=session_id,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )

    return json_response

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_verified_user)):
    return success_response({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "birthDate": str(current_user.birth_date),
        "phone": current_user.phone,
        "avatarUrl": current_user.avatar_url,
        "accountType": current_user.account_type.value
    })

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    redis_client: redis.Redis = Depends(get_redis)
):
    session_id = request.cookies.get("session-id")

    if session_id:
        SessionService.delete_session(redis_client, session_id)

    json_response = success_response({
        "message": "Выход выполнен успешно"
    })

    json_response.delete_cookie("session-id")

    return json_response

@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if request.name is not None:
        current_user.name = request.name
    
    if request.birth_date is not None:
        current_user.birth_date = request.birth_date
    
    if request.phone is not None:
        current_user.phone = request.phone
    
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url
    
    db.commit()
    db.refresh(current_user)
    
    return success_response({
        "message": "Профиль успешно обновлен",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "birthDate": str(current_user.birth_date),
            "phone": current_user.phone,
            "avatarUrl": current_user.avatar_url,
            "accountType": current_user.account_type.value
        }
    })

@router.post("/reset-password/request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Запрос на сброс пароля
    
    Отправляет OTP код на email пользователя.
    НЕ требует авторизации.
    """
    # Проверяем существует ли пользователь
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Из соображений безопасности возвращаем success, чтобы не раскрывать существование email
        return success_response({
            "message": "Если email существует в системе, код для сброса пароля был отправлен на почту",
            "email": request.email
        })
    
    # Генерируем OTP код
    otp_code = OTPService.generate_otp_code(db, user.email)
    
    # Отправляем email
    OTPService.send_password_reset_email(user.email, otp_code)
    
    return success_response({
        "message": "Код для сброса пароля отправлен на email",
        "email": user.email,
        "otpCode": otp_code if (settings.DEBUG and not settings.SMTP_ENABLED) else None
    })

@router.post("/reset-password/verify")
async def verify_password_reset(
    request: PasswordResetVerify,
    db: Session = Depends(get_db)
):
    """
    Подтверждение сброса пароля и установка нового
    
    Проверяет OTP код и обновляет пароль пользователя.
    НЕ требует авторизации.
    """
    # Проверяем OTP код
    is_valid, error = OTPService.verify_otp(db, request.email, request.code)
    
    if not is_valid:
        return error_response(error, 400)
    
    # Находим пользователя
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        return error_response("Пользователь не найден", 404)
    
    # Обновляем пароль
    password_hash = AuthService.hash_password(request.new_password)
    user.password_hash = password_hash
    
    db.commit()
    
    logger.info(f"✅ Пароль успешно изменен для {user.email}")
    
    return success_response({
        "message": "Пароль успешно изменен. Войдите с новым паролем.",
        "email": user.email
    })
