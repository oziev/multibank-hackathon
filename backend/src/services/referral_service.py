import logging
import secrets
import string
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Dict, List
from decimal import Decimal
from datetime import datetime

from src.models.user import User
from src.models.referral import Referral, ReferralStatus
from src.constants.constants import AccountType

logger = logging.getLogger(__name__)

class ReferralService:
    # Награды за рефералов
    REWARD_REGISTRATION = Decimal("50.00")  # 50₽ за регистрацию
    REWARD_PREMIUM = Decimal("100.00")  # 100₽ за покупку Premium приглашенным
    MIN_WITHDRAWAL = Decimal("500.00")  # Минимальная сумма для вывода

    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """Генерация уникального реферального кода"""
        # Формат: REF{USER_ID}{RANDOM}
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        code = f"REF{user_id}{random_part}"
        return code

    @staticmethod
    def get_or_create_referral_code(db: Session, user_id: int) -> str:
        """Получить или создать реферальный код для пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Пользователь не найден")

        if user.referral_code:
            return user.referral_code

        # Генерируем новый код
        max_attempts = 10
        for _ in range(max_attempts):
            code = ReferralService.generate_referral_code(user_id)
            existing = db.query(User).filter(User.referral_code == code).first()
            if not existing:
                user.referral_code = code
                db.commit()
                db.refresh(user)
                logger.info(f"Создан реферальный код {code} для пользователя {user_id}")
                return code

        raise ValueError("Не удалось создать уникальный реферальный код")

    @staticmethod
    def validate_referral_code(db: Session, code: str) -> Tuple[Optional[User], Optional[str]]:
        """Проверить валидность реферального кода"""
        if not code or len(code) < 5:
            return None, "Неверный формат реферального кода"

        user = db.query(User).filter(User.referral_code == code).first()
        if not user:
            return None, "Реферальный код не найден"

        if user.id == user.referred_by_id:  # Нельзя использовать свой код
            return None, "Нельзя использовать свой реферальный код"

        return user, None

    @staticmethod
    def register_referral(
        db: Session,
        referral_code: str,
        new_user_id: int
    ) -> Tuple[Optional[Referral], Optional[str]]:
        """Зарегистрировать реферала при регистрации нового пользователя"""
        referrer, error = ReferralService.validate_referral_code(db, referral_code)
        if error or not referrer:
            return None, error or "Реферальный код не найден"

        new_user = db.query(User).filter(User.id == new_user_id).first()
        if not new_user:
            return None, "Новый пользователь не найден"

        # Проверяем, не регистрировался ли уже по этому коду
        existing = db.query(Referral).filter(
            Referral.referrer_id == referrer.id,
            Referral.referred_id == new_user_id
        ).first()

        if existing:
            return existing, None

        # Создаем запись о реферале
        referral = Referral(
            referrer_id=referrer.id,
            referred_id=new_user_id,
            referral_code=referral_code,
            status=ReferralStatus.PENDING
        )

        # Устанавливаем связь
        new_user.referred_by_id = referrer.id

        db.add(referral)
        db.commit()
        db.refresh(referral)

        logger.info(f"Зарегистрирован реферал: {new_user_id} по коду {referral_code} от {referrer.id}")

        # Начисляем награды за регистрацию
        ReferralService._reward_registration(db, referral)

        return referral, None

    @staticmethod
    def _reward_registration(db: Session, referral: Referral):
        """Начислить награды за регистрацию"""
        try:
            # Награда пригласившему
            referrer = db.query(User).filter(User.id == referral.referrer_id).first()
            if referrer:
                referrer.referral_rewards += ReferralService.REWARD_REGISTRATION
                referral.reward_amount += ReferralService.REWARD_REGISTRATION

            # Награда новому пользователю
            referred = db.query(User).filter(User.id == referral.referred_id).first()
            if referred:
                referred.referral_rewards += ReferralService.REWARD_REGISTRATION

            referral.status = ReferralStatus.COMPLETED
            referral.completed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Начислены награды за регистрацию реферала {referral.id}")
        except Exception as e:
            logger.error(f"Ошибка начисления наград: {e}")
            db.rollback()

    @staticmethod
    def reward_premium_purchase(db: Session, user_id: int):
        """Начислить награду за покупку Premium приглашенным пользователем"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.referred_by_id:
            return

        # Находим реферальную запись
        referral = db.query(Referral).filter(
            Referral.referred_id == user_id,
            Referral.referrer_id == user.referred_by_id
        ).first()

        if not referral:
            return

        # Проверяем, не начисляли ли уже награду за Premium
        if referral.reward_amount >= ReferralService.REWARD_REGISTRATION + ReferralService.REWARD_PREMIUM:
            return

        try:
            referrer = db.query(User).filter(User.id == user.referred_by_id).first()
            if referrer:
                referrer.referral_rewards += ReferralService.REWARD_PREMIUM
                referral.reward_amount += ReferralService.REWARD_PREMIUM

            db.commit()
            logger.info(f"Начислена награда за Premium для реферала {referral.id}")
        except Exception as e:
            logger.error(f"Ошибка начисления награды за Premium: {e}")
            db.rollback()

    @staticmethod
    def get_referral_stats(db: Session, user_id: int) -> Dict:
        """Получить статистику рефералов пользователя"""
        referrals = db.query(Referral).filter(Referral.referrer_id == user_id).all()
        user = db.query(User).filter(User.id == user_id).first()

        total_referrals = len(referrals)
        completed_referrals = len([r for r in referrals if r.status == ReferralStatus.COMPLETED])
        total_rewards = float(user.referral_rewards) if user else 0.0
        total_paid = sum([float(r.reward_amount) for r in referrals if r.reward_paid == "1"])
        
        # Получаем или создаем реферальный код
        referral_code = None
        if user:
            referral_code = ReferralService.get_or_create_referral_code(db, user_id)

        return {
            "referral_code": referral_code,
            "total_referrals": total_referrals,
            "completed_referrals": completed_referrals,
            "pending_referrals": total_referrals - completed_referrals,
            "total_rewards": total_rewards,
            "pending_rewards": total_rewards - total_paid,
            "total_paid": total_paid,
            "available_rewards": total_rewards - total_paid,
            "can_claim": (total_rewards - total_paid) >= ReferralService.MIN_WITHDRAWAL,
            "min_claim_amount": float(ReferralService.MIN_WITHDRAWAL)
        }

    @staticmethod
    def get_referral_list(db: Session, user_id: int) -> List[Dict]:
        """Получить список приглашенных пользователей"""
        referrals = db.query(Referral).filter(Referral.referrer_id == user_id).all()

        result = []
        for referral in referrals:
            referred_user = db.query(User).filter(User.id == referral.referred_id).first()
            result.append({
                "id": referral.id,
                "referred_user_id": referred_user.id if referred_user else None,
                "referred_user_email": referred_user.email if referred_user else "Неизвестно",
                "referred_user_name": referred_user.name if referred_user else "Неизвестно",
                "status": referral.status.value,
                "reward_amount": float(referral.reward_amount),
                "reward_paid": referral.reward_paid == "1",
                "created_at": referral.created_at.isoformat() if referral.created_at else None,
                "completed_at": referral.completed_at.isoformat() if referral.completed_at else None
            })

        return result

    @staticmethod
    def claim_reward(db: Session, user_id: int) -> Tuple[bool, Optional[str]]:
        """Запросить выплату награды"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден"

        available = user.referral_rewards
        paid = sum([float(r.reward_amount) for r in user.referrals_sent if r.reward_paid == "1"])
        withdrawable = available - Decimal(str(paid))

        if withdrawable < ReferralService.MIN_WITHDRAWAL:
            return False, f"Минимальная сумма для вывода: {ReferralService.MIN_WITHDRAWAL}₽. Доступно: {withdrawable}₽"

        # В реальном приложении здесь была бы интеграция с платежной системой
        # Пока просто помечаем как выплаченные
        try:
            referrals = db.query(Referral).filter(
                Referral.referrer_id == user_id,
                Referral.reward_paid == "0"
            ).all()

            for referral in referrals:
                referral.reward_paid = "1"
                referral.status = ReferralStatus.REWARDED

            db.commit()
            logger.info(f"Выплата награды пользователю {user_id}: {withdrawable}₽")
            return True, f"Запрос на выплату {withdrawable}₽ отправлен. Ожидайте обработки."
        except Exception as e:
            logger.error(f"Ошибка выплаты награды: {e}")
            db.rollback()
            return False, "Ошибка при обработке запроса на выплату"

