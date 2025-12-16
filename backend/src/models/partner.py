from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class PartnerStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"

class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    api_secret = Column(String(255), nullable=False)
    status = Column(Enum(PartnerStatus), default=PartnerStatus.PENDING, nullable=False)
    commission_rate = Column(Numeric(5, 2), default=0, nullable=False)  # Процент комиссии
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("PartnerTransaction", back_populates="partner")

    def __repr__(self):
        return f"<Partner(id={self.id}, name={self.name}, status={self.status.value})>"

class PartnerTransaction(Base):
    __tablename__ = "partner_transactions"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # subscription, referral, cashback_export
    amount = Column(Numeric(10, 2), default=0, nullable=False)
    commission = Column(Numeric(10, 2), default=0, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, completed, failed
    extra_data = Column(String(500), nullable=True)  # JSON с дополнительными данными
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    partner = relationship("Partner", back_populates="transactions")
    user = relationship("User", backref="partner_transactions")

    def __repr__(self):
        return f"<PartnerTransaction(id={self.id}, partner_id={self.partner_id}, type={self.transaction_type}, amount={self.amount})>"

