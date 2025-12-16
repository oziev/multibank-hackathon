from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date
from typing import Optional
from src.constants.constants import AccountType

class SignUpRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    password: str
    name: str
    phone: str
    birth_date: date = Field(..., alias='birthDate')
    referral_code: Optional[str] = Field(None, alias='referralCode')  # Опциональный реферальный код

class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    code: str = Field(..., alias='otpCode')

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    birth_date: date = Field(..., serialization_alias='birthDate')
    account_type: AccountType = Field(..., serialization_alias='accountType')

class SignUpResponse(BaseModel):
    message: str
    email: str

class SignInResponse(BaseModel):
    message: str
    user: UserResponse

class PasswordResetRequest(BaseModel):
    """Запрос на сброс пароля"""
    email: EmailStr

class PasswordResetVerify(BaseModel):
    """Подтверждение сброса пароля"""
    model_config = ConfigDict(populate_by_name=True)
    
    email: EmailStr
    code: str = Field(..., alias='otpCode')
    new_password: str = Field(..., alias='newPassword', min_length=8)

class ProfileUpdateRequest(BaseModel):
    """Обновление профиля пользователя"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = None
    birth_date: Optional[date] = Field(None, alias='birthDate')
    phone: Optional[str] = None
    avatar_url: Optional[str] = Field(None, alias='avatarUrl')
