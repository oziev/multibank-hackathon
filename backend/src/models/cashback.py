from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class CashbackData(Base):
    __tablename__ = "cashback_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)  # Формат: YYYY-MM
    total_cashback = Column(Numeric(10, 2), default=0, nullable=False)
    transactions_count = Column(Integer, default=0, nullable=False)
    average_cashback_rate = Column(Numeric(5, 2), default=0, nullable=False)  # Средний процент кешбека
    categories_breakdown = Column(Text, nullable=True)  # JSON строка с разбивкой по категориям
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="cashback_data")

    def __repr__(self):
        return f"<CashbackData(id={self.id}, user_id={self.user_id}, month={self.month}, total={self.total_cashback})>"

class CashbackConsent(Base):
    __tablename__ = "cashback_consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True, index=True)  # Будет создана позже
    consent_given = Column(String(10), default="0", nullable=False)  # "0" или "1"
    consent_date = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="cashback_consents")

    def __repr__(self):
        return f"<CashbackConsent(id={self.id}, user_id={self.user_id}, partner_id={self.partner_id}, consent={self.consent_given})>"

