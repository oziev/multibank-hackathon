"""
Модели для платежей и переводов
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class PaymentType(str, enum.Enum):
    """Типы платежей"""
    CARD_TO_CARD = "card_to_card"  # С карты на карту
    TO_PERSON = "to_person"  # Людям (по телефону)
    CASH = "cash"  # Наличные
    TO_ORGANIZATION = "to_organization"  # Организациям
    MOBILE = "mobile"  # Мобильная связь
    UTILITIES = "utilities"  # ЖКХ
    INTERNET = "internet"  # Интернет
    TV = "tv"  # Телевидение
    PHONE = "phone"  # Телефон
    ELECTRICITY = "electricity"  # Электроэнергия
    PREMIUM = "premium"  # Покупка Premium


class PaymentStatus(str, enum.Enum):
    """Статусы платежей"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(Base):
    """Платеж или перевод"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Тип платежа
    payment_type = Column(SQLEnum(PaymentType), nullable=False, index=True)
    
    # Сумма
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")
    
    # Отправитель
    from_account_id = Column(Integer, nullable=True)  # ID счета отправителя
    from_account_name = Column(String(255), nullable=True)
    
    # Получатель
    to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Если перевод внутри системы
    to_phone = Column(String(20), nullable=True)  # Номер телефона получателя
    to_account = Column(String(255), nullable=True)  # Номер счета получателя
    to_name = Column(String(255), nullable=True)  # Имя получателя
    
    # Описание и назначение
    description = Column(Text, nullable=True)
    purpose = Column(String(255), nullable=True)
    
    # Статус
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # ID транзакции в банке (если есть)
    bank_payment_id = Column(String(255), nullable=True, unique=True)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    recipient = relationship("User", foreign_keys=[to_user_id])

    def __repr__(self):
        return f"<Payment(id={self.id}, type={self.payment_type}, amount={self.amount}, status={self.status})>"


class PaymentTemplate(Base):
    """Шаблон платежа для быстрых операций"""
    __tablename__ = "payment_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Тип платежа
    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    
    # Название шаблона
    name = Column(String(255), nullable=False)
    
    # Получатель
    to_phone = Column(String(20), nullable=True)
    to_account = Column(String(255), nullable=True)
    to_name = Column(String(255), nullable=True)
    
    # Сумма (опционально, может быть переменной)
    amount = Column(Float, nullable=True)
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь
    user = relationship("User", back_populates="payment_templates")

    def __repr__(self):
        return f"<PaymentTemplate(id={self.id}, name={self.name}, type={self.payment_type})>"

