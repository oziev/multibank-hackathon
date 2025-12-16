"""
Схемы для карт лояльности
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LoyaltyCardCreate(BaseModel):
    """Схема для создания карты лояльности"""
    card_type: str = Field(..., description="Тип карты: magnit, pyaterochka, letual и т.д.")
    card_number: str = Field(..., description="Номер карты")
    card_name: Optional[str] = Field(None, description="Название карты (опционально)")
    barcode_type: Optional[str] = Field("EAN13", description="Тип штрих-кода: EAN13, CODE128, QR")


class LoyaltyCardUpdate(BaseModel):
    """Схема для обновления карты"""
    card_name: Optional[str] = Field(None, description="Новое название карты")
    card_number: Optional[str] = Field(None, description="Новый номер карты")


class LoyaltyCardResponse(BaseModel):
    """Схема ответа с картой лояльности"""
    id: int
    card_type: str
    card_number: str
    masked_number: str
    card_name: Optional[str]
    barcode_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BarcodeResponse(BaseModel):
    """Ответ с сгенерированным штрих-кодом"""
    barcode_data: str  # Base64 encoded image
    barcode_type: str
    card_number: str

