import logging
from sqlalchemy.orm import Session
from typing import Optional, Tuple
from datetime import date

from src.models.user import User
from src.utils.security import hash_password, verify_password
from src.utils.validators import validate_password_strength, validate_age

logger = logging.getLogger(__name__)

class AuthService:

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        name: str,
        phone: str,
        birth_date: date,
        referral_code: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None, "Пользователь с таким email уже существует"
        
        # Проверка уникальности телефона
        if phone:
            existing_phone = db.query(User).filter(User.phone == phone).first()
            if existing_phone:
                return None, "Пользователь с таким номером телефона уже существует"

        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            return None, error_msg

        if not validate_age(birth_date):
            return None, "Вам должно быть минимум 18 лет"

        hashed = hash_password(password)

        new_user = User(
            email=email,
            password_hash=hashed,
            name=name,
            phone=phone,
            birth_date=birth_date,
            is_verified=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Обработка реферального кода (если указан)
        if referral_code:
            try:
                from src.services.referral_service import ReferralService
                ReferralService.register_referral(db, referral_code, new_user.id)
                logger.info(f"Зарегистрирован реферал {new_user.id} по коду {referral_code}")
            except Exception as e:
                logger.warning(f"Ошибка регистрации реферала: {e}")
                # Не блокируем регистрацию, если реферальный код неверный

        logger.info(f"Создан новый пользователь: {email}, телефон: {phone}")
        return new_user, None

    @staticmethod
    def verify_user(db: Session, email: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None

        user.is_verified = True
        db.commit()
        db.refresh(user)

        logger.info(f"Email подтверждён для пользователя: {email}")
        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None, "Неверный email или пароль"

        if not verify_password(password, user.password_hash):
            return None, "Неверный email или пароль"

        if not user.is_verified:
            return None, "Аккаунт не подтвержден. Пожалуйста, подтвердите email."

        logger.info(f"Пользователь авторизован: {email}")
        return user, None
