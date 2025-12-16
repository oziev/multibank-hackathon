from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class SubscriptionStatus(enum.Enum):
    PENDING = "pending"  # Ожидает обработки
    ACTIVE = "active"  # Активна
    CANCELLED = "cancelled"  # Отменена
    EXPIRED = "expired"  # Истекла

class ServiceType(enum.Enum):
    CARD_ISSUE = "card_issue"  # Выпуск карты
    ACCOUNT_OPEN = "account_open"  # Открытие счета
    PREMIUM_SERVICE = "premium_service"  # Премиум услуга банка (например, ВТБ+)
    DEPOSIT = "deposit"  # Открытие депозита
    LOAN = "loan"  # Оформление кредита

class BankSubscription(Base):
    __tablename__ = "bank_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bank_id = Column(Integer, nullable=False, index=True)
    service_type = Column(Enum(ServiceType), nullable=False)
    product_id = Column(String(100), nullable=True)  # ID продукта из каталога банка
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    subscription_date = Column(DateTime(timezone=True), server_default=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    # ID согласий и договоров из банковского API
    payment_consent_id = Column(String(100), nullable=True)  # ID VRP согласия для подписок
    product_agreement_id = Column(String(100), nullable=True)  # ID договора с продуктом
    product_agreement_consent_id = Column(String(100), nullable=True)  # ID согласия на управление договорами
    # Партнерская информация
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True, index=True)  # Будет создана позже
    # Дополнительные данные
    extra_data = Column(Text, nullable=True)  # JSON с дополнительными данными
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="bank_subscriptions")

    def __repr__(self):
        return f"<BankSubscription(id={self.id}, user_id={self.user_id}, service_type={self.service_type.value}, status={self.status.value})>"

