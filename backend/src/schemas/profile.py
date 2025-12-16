from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date
from typing import Optional

class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = None
    birth_date: Optional[date] = Field(None, alias='birthDate')
    phone: Optional[str] = None
    avatar_url: Optional[str] = Field(None, alias='avatarUrl')

class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    role: str

class AccountRenameRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    account_name: str = Field(..., alias='accountName')

