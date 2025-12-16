from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    bank_id = Column(Integer, nullable=False, index=True)

    account_id = Column(String(255), nullable=False)

    account_name = Column(String(255), nullable=True)

    consent_id = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    
    priority = Column(Integer, default=999, nullable=False)  # Приоритет для списания (1 = высший)
    
    is_hidden = Column(Boolean, default=False, nullable=False)  # Скрыть баланс счета

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="bank_accounts")

    def __repr__(self):
        return f"<BankAccount(id={self.id}, user_id={self.user_id}, bank_id={self.bank_id})>"
