"""
Схемы для целей накопления
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ContributionRuleCreate(BaseModel):
    """Создание правила пополнения"""
    source_account_id: int
    rule_type: str = Field(..., description="fixed_amount, percentage_purchase, percentage_income, rounding, end_of_month_balance")
    fixed_amount: Optional[float] = None
    percentage: Optional[float] = Field(None, ge=0, le=100)


class SavingsGoalCreate(BaseModel):
    """Создание цели накопления"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: float = Field(..., gt=0)
    target_account_id: Optional[int] = None
    target_date: Optional[datetime] = None
    image_url: Optional[str] = None
    contribution_rules: List[ContributionRuleCreate] = []


class SavingsGoalUpdate(BaseModel):
    """Обновление цели"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[datetime] = None
    image_url: Optional[str] = None
    status: Optional[str] = None


class ContributionRuleResponse(BaseModel):
    """Ответ с правилом пополнения"""
    id: int
    source_account_id: int
    rule_type: str
    fixed_amount: Optional[float]
    percentage: Optional[float]
    is_active: bool
    
    class Config:
        from_attributes = True


class SavingsGoalResponse(BaseModel):
    """Ответ с целью накопления"""
    id: int
    name: str
    description: Optional[str]
    target_amount: float
    current_amount: float
    progress_percentage: float
    status: str
    target_date: Optional[datetime]
    image_url: Optional[str]
    contribution_rules: List[ContributionRuleResponse]
    created_at: datetime
    estimated_completion_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class BudgetLimitCreate(BaseModel):
    """Создание лимита для члена группы"""
    user_id: int
    monthly_limit: float = Field(..., ge=0)
    daily_limit: float = Field(..., ge=0)
    notify_at_percentage: float = Field(80.0, ge=0, le=100)


class BudgetLimitResponse(BaseModel):
    """Ответ с лимитом"""
    id: int
    user_id: int
    user_name: str
    monthly_limit: float
    daily_limit: float
    current_month_spent: float
    current_day_spent: float
    notify_at_percentage: float
    percentage_used: float
    
    class Config:
        from_attributes = True

