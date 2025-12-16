"""
Схемы для платежей
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TransferRequest(BaseModel):
    """Запрос на перевод денег"""
    from_account_id: int = Field(..., description="ID счета отправителя")
    amount: float = Field(..., gt=0, description="Сумма перевода")
    to_account: Optional[str] = Field(None, description="Номер счета получателя")
    to_phone: Optional[str] = Field(None, description="Телефон получателя")
    description: Optional[str] = Field(None, description="Комментарий")


class TransferByPhoneRequest(BaseModel):
    """Перевод зарегистрированному пользователю по телефону"""
    from_account_id: int = Field(..., alias='fromAccountId')
    to_phone: str = Field(..., alias='toPhone', description="Номер телефона получателя (+7...)")
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    
    class Config:
        populate_by_name = True


class UtilityPaymentRequest(BaseModel):
    """Оплата услуг (ЖКХ, связь и т.д.)"""
    from_account_id: int
    payment_type: str = Field(..., description="mobile, utilities, internet, tv, phone, electricity")
    provider: str = Field(..., description="Название провайдера")
    account_number: str = Field(..., description="Номер лицевого счета или телефона")
    amount: float = Field(..., gt=0)


class PaymentResponse(BaseModel):
    """Ответ на платеж"""
    id: int
    payment_type: str
    amount: float
    currency: str
    status: str
    description: Optional[str]
    to_name: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PaymentHistoryItem(BaseModel):
    """Элемент истории платежей"""
    id: int
    payment_type: str
    amount: float
    currency: str
    status: str
    description: Optional[str]
    to_name: Optional[str]
    from_account_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSearchResult(BaseModel):
    """Результат поиска пользователя"""
    user_id: int
    name: str
    phone: str
    avatar_url: Optional[str]

