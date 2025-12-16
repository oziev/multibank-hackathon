"""
Модель для карт лояльности магазинов
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class CardType(str, enum.Enum):
    """Типы карт лояльности"""
    MAGNIT = "magnit"
    PYATEROCHKA = "pyaterochka"
    LENTA = "lenta"
    AUCHAN = "auchan"
    METRO = "metro"
    LETUAL = "letual"
    GOLDEN_APPLE = "golden_apple"
    RIVEGAUCHE = "rivegauche"
    AZBUKA_VKUSA = "azbuka_vkusa"
    OKEY = "okey"
    PEREKRESTOK = "perekrestok"
    DIKSI = "diksi"
    OTHER = "other"


class BarcodeType(str, enum.Enum):
    """Типы штрих-кодов"""
    EAN13 = "EAN13"
    EAN8 = "EAN8"
    CODE128 = "CODE128"
    QR = "QR"


class LoyaltyCard(Base):
    """Карта лояльности магазина"""
    __tablename__ = "loyalty_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Тип карты (Магнит, Пятерочка и т.д.)
    card_type = Column(SQLEnum(CardType), nullable=False)
    
    # Номер карты
    card_number = Column(String(255), nullable=False)
    
    # Название (опционально, если пользователь хочет дать свое имя)
    card_name = Column(String(255), nullable=True)
    
    # Тип штрих-кода
    barcode_type = Column(SQLEnum(BarcodeType), default=BarcodeType.EAN13)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="loyalty_cards")

    def __repr__(self):
        return f"<LoyaltyCard(id={self.id}, type={self.card_type}, number=***{self.card_number[-4:]})>"

