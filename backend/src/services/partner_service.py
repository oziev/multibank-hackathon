import logging
import secrets
import string
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from src.models.partner import Partner, PartnerTransaction, PartnerStatus
from src.models.user import User

logger = logging.getLogger(__name__)

class PartnerService:
    @staticmethod
    def generate_api_key() -> str:
        """Генерация API ключа для партнера"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

    @staticmethod
    def generate_api_secret() -> str:
        """Генерация секретного ключа для партнера"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_partner(
        db: Session,
        name: str,
        commission_rate: float = 0.0,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> Tuple[Optional[Partner], Optional[str]]:
        """Создать нового партнера (только для админов)"""
        # Проверяем уникальность имени
        existing = db.query(Partner).filter(Partner.name == name).first()
        if existing:
            return None, "Партнер с таким именем уже существует"

        api_key = PartnerService.generate_api_key()
        api_secret = PartnerService.generate_api_secret()

        partner = Partner(
            name=name,
            api_key=api_key,
            api_secret=api_secret,
            commission_rate=Decimal(str(commission_rate)),
            contact_email=contact_email,
            contact_phone=contact_phone,
            status=PartnerStatus.PENDING
        )

        db.add(partner)
        db.commit()
        db.refresh(partner)

        logger.info(f"✅ Создан партнер {name} с API ключом {api_key[:8]}...")
        return partner, None

    @staticmethod
    def authenticate_partner(
        db: Session,
        api_key: str
    ) -> Tuple[Optional[Partner], Optional[str]]:
        """Аутентификация партнера по API ключу"""
        partner = db.query(Partner).filter(Partner.api_key == api_key).first()
        if not partner:
            return None, "Неверный API ключ"

        if partner.status != PartnerStatus.ACTIVE:
            return None, f"Партнер не активен. Статус: {partner.status.value}"

        return partner, None

    @staticmethod
    def get_partner_stats(
        db: Session,
        partner_id: int
    ) -> Dict:
        """Получить статистику партнера"""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return {}

        transactions = db.query(PartnerTransaction).filter(
            PartnerTransaction.partner_id == partner_id
        ).all()

        total_amount = sum([float(t.amount) for t in transactions])
        total_commission = sum([float(t.commission) for t in transactions])
        completed_count = len([t for t in transactions if t.status == "completed"])

        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "status": partner.status.value,
            "commission_rate": float(partner.commission_rate),
            "total_transactions": len(transactions),
            "completed_transactions": completed_count,
            "total_amount": total_amount,
            "total_commission": total_commission,
            "pending_commission": total_commission - sum([float(t.commission) for t in transactions if t.status == "completed"])
        }

    @staticmethod
    def create_partner_transaction(
        db: Session,
        partner_id: int,
        user_id: int,
        transaction_type: str,
        amount: float,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[PartnerTransaction], Optional[str]]:
        """Создать транзакцию партнера"""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return None, "Партнер не найден"

        commission = Decimal(str(amount)) * partner.commission_rate / Decimal("100")

        transaction = PartnerTransaction(
            partner_id=partner_id,
            user_id=user_id,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            commission=commission,
            status="pending",
            extra_data=str(metadata) if metadata else None
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"✅ Создана транзакция партнера {partner_id}: {transaction_type}, сумма: {amount}, комиссия: {commission}")
        return transaction, None

    @staticmethod
    def get_partner_transactions(
        db: Session,
        partner_id: int,
        limit: int = 100
    ) -> List[PartnerTransaction]:
        """Получить транзакции партнера"""
        return db.query(PartnerTransaction).filter(
            PartnerTransaction.partner_id == partner_id
        ).order_by(PartnerTransaction.created_at.desc()).limit(limit).all()

