"""
Модели для целей накопления
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class GoalStatus(str, enum.Enum):
    """Статусы целей"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ContributionRule(str, enum.Enum):
    """Правила пополнения цели"""
    FIXED_AMOUNT = "fixed_amount"  # Фиксированная сумма каждый месяц
    PERCENTAGE_PURCHASE = "percentage_purchase"  # % от каждой покупки
    PERCENTAGE_INCOME = "percentage_income"  # % от каждого дохода
    ROUNDING = "rounding"  # Округление покупок
    END_OF_MONTH_BALANCE = "end_of_month_balance"  # % от остатка в конце месяца


class SavingsGoal(Base):
    """Цель накопления"""
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Основная информация
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0, nullable=False)
    
    # Счет-цель (где накапливаются деньги)
    target_account_id = Column(Integer, nullable=True)  # ID счета в нашей БД
    target_bank_account = Column(String(255), nullable=True)  # ID счета в банке
    
    # Изображение цели
    image_url = Column(String(500), nullable=True)
    
    # Статус
    status = Column(SQLEnum(GoalStatus), default=GoalStatus.ACTIVE, nullable=False)
    
    # Даты
    target_date = Column(DateTime, nullable=True)  # Желаемая дата достижения
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="savings_goals")
    contribution_rules = relationship("GoalContributionRule", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SavingsGoal(id={self.id}, name={self.name}, target={self.target_amount})>"


class GoalContributionRule(Base):
    """Правило пополнения цели"""
    __tablename__ = "goal_contribution_rules"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Счет-источник
    source_account_id = Column(Integer, nullable=False)  # ID в нашей БД
    source_bank_account = Column(String(255), nullable=True)  # ID счета в банке
    
    # Правило
    rule_type = Column(SQLEnum(ContributionRule), nullable=False)
    
    # Параметры правила
    fixed_amount = Column(Float, nullable=True)  # Для FIXED_AMOUNT
    percentage = Column(Float, nullable=True)  # Для процентных правил (0-100)
    
    # Активность
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    last_executed = Column(DateTime, nullable=True)
    
    # Связь
    goal = relationship("SavingsGoal", back_populates="contribution_rules")

    def __repr__(self):
        return f"<GoalContributionRule(id={self.id}, type={self.rule_type}, goal_id={self.goal_id})>"


class FamilyBudgetLimit(Base):
    """Лимиты трат для членов группы"""
    __tablename__ = "family_budget_limits"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Лимиты
    monthly_limit = Column(Float, default=0.0, nullable=False)  # Месячный лимит
    daily_limit = Column(Float, default=0.0, nullable=False)  # Дневной лимит
    
    # Текущие траты
    current_month_spent = Column(Float, default=0.0, nullable=False)
    current_day_spent = Column(Float, default=0.0, nullable=False)
    
    # Уведомления
    notify_at_percentage = Column(Float, default=80.0, nullable=False)  # Уведомить при % лимита
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reset_date = Column(DateTime, default=datetime.utcnow)  # Когда последний раз сбрасывали
    
    # Связи
    group = relationship("Group")
    user = relationship("User")

    def __repr__(self):
        return f"<FamilyBudgetLimit(id={self.id}, user={self.user_id}, monthly={self.monthly_limit})>"

