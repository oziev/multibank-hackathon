import logging
import json
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import redis

from src.models.bank_subscription import BankSubscription, SubscriptionStatus, ServiceType
from src.models.account import BankAccount
from src.models.user import User
from src.services.bank_client import BankClient
from src.services.account_service import AccountService

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.bank_client = BankClient(redis_client)
        self.account_service = AccountService(db, redis_client)

    def get_available_products(
        self,
        user_id: int,
        bank_id: int,
        product_type: Optional[str] = None
    ) -> List[Dict]:
        """Получить каталог доступных продуктов банка"""
        try:
            products = self.bank_client.get_products(user_id, bank_id, product_type)
            return products
        except Exception as e:
            logger.error(f"Ошибка получения продуктов: {e}")
            return []

    def create_subscription(
        self,
        user_id: int,
        bank_id: int,
        service_type: ServiceType,
        product_id: str,
        account_id: Optional[int] = None,
        amount: Optional[float] = None,
        term_months: Optional[int] = None,
        partner_id: Optional[int] = None
    ) -> Tuple[Optional[BankSubscription], Optional[str]]:
        """Создать подписку на банковскую услугу"""
        try:
            # Получаем счет пользователя
            if account_id:
                account = self.db.query(BankAccount).filter(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id
                ).first()
                if not account:
                    return None, "Счет не найден"
                account_number = account.account_id
            else:
                # Берем первый активный счет
                accounts = self.account_service.get_user_accounts(user_id, bank_id)
                if not accounts:
                    return None, "У вас нет активных счетов в этом банке"
                account_number = accounts[0]["accountId"]

            # Получаем client_id для банка
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, "Пользователь не найден"

            # Формируем client_id (в реальности это должно быть из настроек банка)
            client_id = f"user_{user_id}_bank_{bank_id}"

            # Создаем подписку в БД
            subscription = BankSubscription(
                user_id=user_id,
                bank_id=bank_id,
                service_type=service_type,
                product_id=product_id,
                status=SubscriptionStatus.PENDING,
                partner_id=partner_id
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

            # В зависимости от типа услуги создаем соответствующие согласия и договоры
            if service_type == ServiceType.CARD_ISSUE:
                # Выпуск карты
                result = self._create_card_subscription(
                    user_id, bank_id, client_id, account_number, product_id, subscription
                )
            elif service_type == ServiceType.ACCOUNT_OPEN:
                # Открытие счета
                result = self._create_account_subscription(
                    user_id, bank_id, client_id, product_id, subscription
                )
            elif service_type == ServiceType.DEPOSIT:
                # Открытие депозита
                result = self._create_deposit_subscription(
                    user_id, bank_id, client_id, account_number, product_id, amount, term_months, subscription
                )
            elif service_type == ServiceType.PREMIUM_SERVICE:
                # Премиум услуга (например, ВТБ+)
                result = self._create_premium_service_subscription(
                    user_id, bank_id, client_id, account_number, product_id, subscription
                )
            else:
                return None, f"Неподдерживаемый тип услуги: {service_type.value}"

            if result[1]:  # Есть ошибка
                subscription.status = SubscriptionStatus.CANCELLED
                self.db.commit()
                return None, result[1]

            subscription.status = SubscriptionStatus.ACTIVE
            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"✅ Создана подписка {subscription.id} на {service_type.value}")
            return subscription, None

        except Exception as e:
            logger.error(f"Ошибка создания подписки: {e}")
            self.db.rollback()
            return None, f"Ошибка создания подписки: {str(e)}"

    def _create_card_subscription(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        account_number: str,
        product_id: str,
        subscription: BankSubscription
    ) -> Tuple[Optional[str], Optional[str]]:
        """Создать подписку на выпуск карты"""
        try:
            # Создаем согласие на управление договорами
            consent_result = self.bank_client.create_product_agreement_consent(
                user_id, bank_id, client_id,
                read_product_agreements=True,
                open_product_agreements=True,
                allowed_product_types=["card"]
            )
            subscription.product_agreement_consent_id = consent_result["consent_id"]

            # Выпускаем карту
            card_result = self.bank_client.create_card(
                user_id, bank_id, client_id,
                account_number,
                card_name="Visa Classic",
                card_type="debit",
                consent_id=consent_result["consent_id"]
            )
            
            subscription.product_agreement_id = card_result.get("card_id")
            self.db.commit()

            return card_result.get("card_id"), None
        except Exception as e:
            logger.error(f"Ошибка создания подписки на карту: {e}")
            return None, str(e)

    def _create_account_subscription(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        product_id: str,
        subscription: BankSubscription
    ) -> Tuple[Optional[str], Optional[str]]:
        """Создать подписку на открытие счета"""
        try:
            # Создаем согласие на управление договорами
            consent_result = self.bank_client.create_product_agreement_consent(
                user_id, bank_id, client_id,
                read_product_agreements=True,
                open_product_agreements=True,
                allowed_product_types=["account"]
            )
            subscription.product_agreement_consent_id = consent_result["consent_id"]

            # Открываем счет через Product Agreements (если продукт поддерживает)
            # Или используем существующий API создания счета
            # Пока используем mock
            agreement_id = f"account_{bank_id}_{user_id}_{datetime.utcnow().timestamp()}"
            subscription.product_agreement_id = agreement_id
            self.db.commit()

            return agreement_id, None
        except Exception as e:
            logger.error(f"Ошибка создания подписки на счет: {e}")
            return None, str(e)

    def _create_deposit_subscription(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        account_number: str,
        product_id: str,
        amount: float,
        term_months: Optional[int],
        subscription: BankSubscription
    ) -> Tuple[Optional[str], Optional[str]]:
        """Создать подписку на открытие депозита"""
        try:
            # Создаем согласие на управление договорами
            consent_result = self.bank_client.create_product_agreement_consent(
                user_id, bank_id, client_id,
                read_product_agreements=True,
                open_product_agreements=True,
                allowed_product_types=["deposit"],
                max_amount=amount
            )
            subscription.product_agreement_consent_id = consent_result["consent_id"]

            # Открываем депозит
            agreement_result = self.bank_client.create_product_agreement(
                user_id, bank_id, client_id,
                product_id, amount, term_months, account_number,
                consent_result["consent_id"]
            )

            subscription.product_agreement_id = agreement_result["agreement_id"]
            self.db.commit()

            return agreement_result["agreement_id"], None
        except Exception as e:
            logger.error(f"Ошибка создания подписки на депозит: {e}")
            return None, str(e)

    def _create_premium_service_subscription(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        account_number: str,
        product_id: str,
        subscription: BankSubscription
    ) -> Tuple[Optional[str], Optional[str]]:
        """Создать подписку на премиум услугу (например, ВТБ+)"""
        try:
            # Создаем VRP согласие для автоматических платежей
            valid_until = (datetime.utcnow() + timedelta(days=365)).isoformat()
            vrp_result = self.bank_client.create_payment_consent_vrp(
                user_id, bank_id, client_id,
                account_number,
                vrp_max_individual_amount=1000.0,  # Макс сумма одного платежа
                vrp_daily_limit=3000.0,  # Дневной лимит
                vrp_monthly_limit=50000.0,  # Месячный лимит
                valid_until=valid_until
            )

            subscription.payment_consent_id = vrp_result["consent_id"]

            # Создаем согласие на управление договорами
            consent_result = self.bank_client.create_product_agreement_consent(
                user_id, bank_id, client_id,
                read_product_agreements=True,
                open_product_agreements=True,
                allowed_product_types=["account", "card"]
            )
            subscription.product_agreement_consent_id = consent_result["consent_id"]

            self.db.commit()

            return vrp_result["consent_id"], None
        except Exception as e:
            logger.error(f"Ошибка создания подписки на премиум услугу: {e}")
            return None, str(e)

    def get_user_subscriptions(
        self,
        user_id: int,
        bank_id: Optional[int] = None
    ) -> List[BankSubscription]:
        """Получить список подписок пользователя"""
        query = self.db.query(BankSubscription).filter(BankSubscription.user_id == user_id)

        if bank_id:
            query = query.filter(BankSubscription.bank_id == bank_id)

        return query.order_by(BankSubscription.created_at.desc()).all()

    def cancel_subscription(
        self,
        subscription_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Отменить подписку"""
        subscription = self.db.query(BankSubscription).filter(
            BankSubscription.id == subscription_id,
            BankSubscription.user_id == user_id
        ).first()

        if not subscription:
            return False, "Подписка не найдена"

        if subscription.status == SubscriptionStatus.CANCELLED:
            return False, "Подписка уже отменена"

        try:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"✅ Подписка {subscription_id} отменена")
            return True, None
        except Exception as e:
            logger.error(f"Ошибка отмены подписки: {e}")
            self.db.rollback()
            return False, f"Ошибка отмены подписки: {str(e)}"

