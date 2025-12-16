"""
API роутер для семейного бюджета и лимитов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.services.savings_service import FamilyBudgetService
from src.schemas.savings import BudgetLimitCreate, BudgetLimitResponse
from typing import List


router = APIRouter(prefix="/api/family-budget", tags=["Family Budget"])


@router.post("/groups/{group_id}/limits", response_model=dict)
async def set_member_limit(
    group_id: int,
    limit_data: BudgetLimitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Установить лимит для члена группы
    
    Только Owner и Admin могут устанавливать лимиты
    """
    from src.models.group import GroupMember
    from src.constants.constants import GroupRole
    
    # Проверяем права (owner или admin)
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member or member.role not in [GroupRole.OWNER, GroupRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец или администратор может устанавливать лимиты"
        )
    
    limit, error = FamilyBudgetService.set_member_limit(
        db,
        group_id,
        limit_data.user_id,
        limit_data.monthly_limit,
        limit_data.daily_limit,
        limit_data.notify_at_percentage
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "success": True,
        "data": {
            "message": "Лимит установлен!",
            "limit": {
                "id": limit.id,
                "userId": limit.user_id,
                "monthlyLimit": limit.monthly_limit,
                "dailyLimit": limit.daily_limit,
                "notifyAt": limit.notify_at_percentage
            }
        }
    }


@router.get("/groups/{group_id}/limits", response_model=dict)
async def get_group_limits(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все лимиты группы"""
    
    from src.models.group import GroupMember
    
    # Проверяем что пользователь - член группы
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь членом этой группы"
        )
    
    limits = FamilyBudgetService.get_group_limits(db, group_id)
    
    return {
        "success": True,
        "data": [
            {
                "id": l.id,
                "userId": l.user_id,
                "userName": l.user.name if l.user else "Unknown",
                "monthlyLimit": l.monthly_limit,
                "dailyLimit": l.daily_limit,
                "currentMonthSpent": l.current_month_spent,
                "currentDaySpent": l.current_day_spent,
                "notifyAt": l.notify_at_percentage,
                "percentageUsed": round((l.current_month_spent / l.monthly_limit * 100) if l.monthly_limit > 0 else 0, 1)
            }
            for l in limits
        ]
    }

