"""
Сервис для работы с целями накопления
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from src.models.savings_goal import SavingsGoal, GoalContributionRule, FamilyBudgetLimit, GoalStatus, ContributionRule
from src.models.account import BankAccount
from src.models.user import User


class SavingsService:
    """Сервис для управления целями накопления"""
    
    @staticmethod
    def create_goal(
        db: Session,
        user_id: int,
        name: str,
        target_amount: float,
        description: Optional[str] = None,
        target_account_id: Optional[int] = None,
        target_date: Optional[datetime] = None,
        image_url: Optional[str] = None
    ) -> Tuple[Optional[SavingsGoal], Optional[str]]:
        """Создать новую цель накопления"""
        
        # Проверяем счет-цель если указан
        if target_account_id:
            account = db.query(BankAccount).filter(
                BankAccount.id == target_account_id,
                BankAccount.user_id == user_id
            ).first()
            
            if not account:
                return None, "Счет-цель не найден"
        
        goal = SavingsGoal(
            user_id=user_id,
            name=name,
            description=description,
            target_amount=target_amount,
            target_account_id=target_account_id,
            target_date=target_date,
            image_url=image_url,
            status=GoalStatus.ACTIVE
        )
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return goal, None
    
    @staticmethod
    def add_contribution_rule(
        db: Session,
        goal_id: int,
        user_id: int,
        source_account_id: int,
        rule_type: str,
        fixed_amount: Optional[float] = None,
        percentage: Optional[float] = None
    ) -> Tuple[Optional[GoalContributionRule], Optional[str]]:
        """Добавить правило пополнения к цели"""
        
        # Проверяем цель
        goal = db.query(SavingsGoal).filter(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user_id
        ).first()
        
        if not goal:
            return None, "Цель не найдена"
        
        # Проверяем счет-источник
        account = db.query(BankAccount).filter(
            BankAccount.id == source_account_id,
            BankAccount.user_id == user_id
        ).first()
        
        if not account:
            return None, "Счет-источник не найден"
        
        rule = GoalContributionRule(
            goal_id=goal_id,
            source_account_id=source_account_id,
            source_bank_account=account.account_id,
            rule_type=ContributionRule(rule_type),
            fixed_amount=fixed_amount,
            percentage=percentage,
            is_active=True
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        return rule, None
    
    @staticmethod
    def get_user_goals(db: Session, user_id: int) -> List[SavingsGoal]:
        """Получить все цели пользователя"""
        return db.query(SavingsGoal).filter(
            SavingsGoal.user_id == user_id
        ).order_by(SavingsGoal.created_at.desc()).all()
    
    @staticmethod
    def contribute_to_goal(
        db: Session,
        goal_id: int,
        user_id: int,
        amount: float
    ) -> Tuple[bool, Optional[str]]:
        """Внести средства в цель"""
        
        goal = db.query(SavingsGoal).filter(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user_id
        ).first()
        
        if not goal:
            return False, "Цель не найдена"
        
        if goal.status != GoalStatus.ACTIVE:
            return False, "Цель не активна"
        
        goal.current_amount += amount
        
        # Проверяем достижение цели
        if goal.current_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.utcnow()
        
        db.commit()
        
        return True, None
    
    @staticmethod
    def calculate_progress(goal: SavingsGoal) -> dict:
        """Рассчитать прогресс цели"""
        progress_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        remaining = goal.target_amount - goal.current_amount
        
        # Простая оценка даты завершения (если есть история)
        estimated_completion = None
        if goal.target_date:
            estimated_completion = goal.target_date
        elif goal.current_amount > 0 and goal.created_at:
            days_since_creation = (datetime.utcnow() - goal.created_at).days
            if days_since_creation > 0:
                daily_rate = goal.current_amount / days_since_creation
                if daily_rate > 0:
                    days_remaining = remaining / daily_rate
                    estimated_completion = datetime.utcnow() + timedelta(days=days_remaining)
        
        return {
            "progress_percentage": round(progress_percentage, 1),
            "remaining_amount": remaining,
            "estimated_completion_date": estimated_completion
        }


class FamilyBudgetService:
    """Сервис для семейного бюджета и лимитов"""
    
    @staticmethod
    def set_member_limit(
        db: Session,
        group_id: int,
        user_id: int,
        monthly_limit: float,
        daily_limit: float,
        notify_at: float = 80.0
    ) -> Tuple[Optional[FamilyBudgetLimit], Optional[str]]:
        """Установить лимит для члена группы"""
        
        # Проверяем существующий лимит
        limit = db.query(FamilyBudgetLimit).filter(
            FamilyBudgetLimit.group_id == group_id,
            FamilyBudgetLimit.user_id == user_id
        ).first()
        
        if limit:
            # Обновляем
            limit.monthly_limit = monthly_limit
            limit.daily_limit = daily_limit
            limit.notify_at_percentage = notify_at
        else:
            # Создаем новый
            limit = FamilyBudgetLimit(
                group_id=group_id,
                user_id=user_id,
                monthly_limit=monthly_limit,
                daily_limit=daily_limit,
                notify_at_percentage=notify_at
            )
            db.add(limit)
        
        db.commit()
        db.refresh(limit)
        
        return limit, None
    
    @staticmethod
    def get_group_limits(db: Session, group_id: int) -> List[FamilyBudgetLimit]:
        """Получить все лимиты группы"""
        return db.query(FamilyBudgetLimit).filter(
            FamilyBudgetLimit.group_id == group_id
        ).all()
    
    @staticmethod
    def check_limit_exceeded(db: Session, user_id: int, group_id: int, amount: float) -> Tuple[bool, Optional[str]]:
        """Проверить, превышен ли лимит"""
        
        limit = db.query(FamilyBudgetLimit).filter(
            FamilyBudgetLimit.group_id == group_id,
            FamilyBudgetLimit.user_id == user_id
        ).first()
        
        if not limit:
            return False, None  # Нет лимита - можно тратить
        
        # Проверяем дневной лимит
        if limit.daily_limit > 0 and (limit.current_day_spent + amount) > limit.daily_limit:
            return True, f"Превышен дневной лимит: {limit.daily_limit}₽"
        
        # Проверяем месячный лимит
        if limit.monthly_limit > 0 and (limit.current_month_spent + amount) > limit.monthly_limit:
            return True, f"Превышен месячный лимит: {limit.monthly_limit}₽"
        
        return False, None

