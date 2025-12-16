from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class BankInfo(BaseModel):
    id: int
    name: str

class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_id: int = Field(..., alias='clientId')

class AccountAttachRequest(BaseModel):
    id: int

class BalanceResponse(BaseModel):
    amount: float
    currency: str

class TransactionResponse(BaseModel):
    id: str
    amount: float
    currency: str
    description: str
    date: datetime
    type: str

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    account_id: str = Field(..., serialization_alias='accountId')
    client_id: int = Field(..., serialization_alias='clientId')
    client_name: str = Field(..., serialization_alias='clientName')
    account_name: Optional[str] = Field(None, serialization_alias='accountName')
    is_active: bool = Field(..., serialization_alias='isActive')

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]

class ConsentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bank_id: int = Field(..., alias='bankId')
    permissions: List[str]
