from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class ReferralStatus(enum.Enum):
    PENDING = "pending"  # Ожидает активации (пользователь зарегистрировался, но не выполнил условия)
    COMPLETED = "completed"  # Условия выполнены (пользователь купил Premium или выполнил другие условия)
    REWARDED = "rewarded"  # Награда выплачена
    CANCELLED = "cancelled"  # Отменено

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referral_code = Column(String(50), nullable=False, index=True)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING, nullable=False)
    reward_amount = Column(Numeric(10, 2), default=0, nullable=False)
    reward_paid = Column(String(10), default="0", nullable=False)  # "0" или "1" для совместимости
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_sent")
    referred = relationship("User", foreign_keys=[referred_id], backref="referrals_received")

    def __repr__(self):
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, referred_id={self.referred_id}, status={self.status.value})>"

