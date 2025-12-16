import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import redis

from src.services.account_service import AccountService
from src.constants.mcc_mapping import categorize_transaction, CATEGORY_NAMES_RU
from src.constants.constants import TransactionCategory
from src.models.payment import Payment, PaymentType, PaymentStatus

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.account_service = AccountService(db, redis_client)
    
    def get_user_overview(
        self,
        user_id: int,
        bank_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Обзорная аналитика пользователя: балансы, доходы, расходы
        """
        accounts = self.account_service.get_user_accounts(user_id, None)
        
        if bank_ids:
            accounts = [acc for acc in accounts if acc["clientId"] in bank_ids]
        
        total_balance = 0.0
        balances_by_currency = {}
        
        for account in accounts:
            try:
                balance = self.account_service.get_account_balance(
                    user_id,
                    account["accountId"],
                    account["clientId"]
                )
                
                amount = balance.get("amount", 0)
                currency = balance.get("currency", "RUB")
                
                total_balance += amount
                
                if currency not in balances_by_currency:
                    balances_by_currency[currency] = 0
                balances_by_currency[currency] += amount
                
            except Exception as e:
                logger.error(f"Ошибка получения баланса: {e}")
                continue
        
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_expenses = 0.0
        current_income = 0.0
        previous_expenses = 0.0
        previous_income = 0.0
        
        category_totals = {}
        
        # Обрабатываем транзакции из Bank API
        for account in accounts:
            try:
                transactions = self.account_service.get_account_transactions(
                    user_id,
                    account["accountId"],
                    account["clientId"]
                )
                
                for txn in transactions:
                    try:
                        txn_date = datetime.fromisoformat(txn["date"].replace('Z', '+00:00'))
                        amount = abs(txn["amount"])
                        txn_type = txn.get("type", "debit")
                        
                        category = categorize_transaction(
                            txn.get("mccCode", ""),
                            txn.get("description", "")
                        )
                        
                        if txn_date >= current_month_start:
                            if txn_type == "debit":
                                current_expenses += amount
                                
                                if category not in category_totals:
                                    category_totals[category] = 0
                                category_totals[category] += amount
                            else:
                                current_income += amount
                        
                        elif txn_date >= previous_month_start and txn_date < current_month_start:
                            if txn_type == "debit":
                                previous_expenses += amount
                            else:
                                previous_income += amount
                    
                    except Exception as e:
                        logger.warning(f"Ошибка обработки транзакции: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Ошибка получения транзакций: {e}")
                continue
        
        # Обрабатываем внутренние платежи (Payment модель)
        try:
            from sqlalchemy import or_
            internal_payments = self.db.query(Payment).filter(
                or_(
                    Payment.user_id == user_id,  # Исходящие платежи
                    Payment.to_user_id == user_id  # Входящие платежи
                ),
                Payment.status == PaymentStatus.COMPLETED,
                Payment.completed_at.isnot(None)
            ).all()
            
            for payment in internal_payments:
                try:
                    payment_date = payment.completed_at
                    if not payment_date:
                        payment_date = payment.created_at
                    
                    amount = float(payment.amount)
                    
                    # Определяем, это доход или расход
                    is_incoming = payment.to_user_id == user_id if payment.to_user_id else False
                    is_outgoing = payment.user_id == user_id
                    
                    if payment_date >= current_month_start:
                        if is_outgoing:
                            # Исходящий платеж - это расход
                            current_expenses += amount
                            
                            # Определяем категорию по типу платежа
                            category = TransactionCategory.OTHER
                            if payment.payment_type == PaymentType.UTILITIES:
                                category = TransactionCategory.UTILITIES
                            elif payment.payment_type == PaymentType.MOBILE or payment.payment_type == PaymentType.PHONE:
                                category = TransactionCategory.COMMUNICATIONS
                            elif payment.payment_type == PaymentType.INTERNET:
                                category = TransactionCategory.COMMUNICATIONS
                            elif payment.payment_type == PaymentType.TV:
                                category = TransactionCategory.ENTERTAINMENT
                            elif payment.payment_type == PaymentType.ELECTRICITY:
                                category = TransactionCategory.UTILITIES
                            elif payment.payment_type == PaymentType.PREMIUM:
                                category = TransactionCategory.OTHER
                            elif payment.payment_type == PaymentType.TO_PERSON or payment.payment_type == PaymentType.CARD_TO_CARD:
                                category = TransactionCategory.TRANSFERS
                            
                            if category not in category_totals:
                                category_totals[category] = 0
                            category_totals[category] += amount
                        elif is_incoming:
                            # Входящий платеж - это доход
                            current_income += amount
                    
                    elif payment_date >= previous_month_start and payment_date < current_month_start:
                        if is_outgoing:
                            previous_expenses += amount
                        elif is_incoming:
                            previous_income += amount
                
                except Exception as e:
                    logger.warning(f"Ошибка обработки внутреннего платежа: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка получения внутренних платежей: {e}")
        
        top_categories = sorted(
            [
                {
                    "category": cat.value,
                    "categoryName": CATEGORY_NAMES_RU.get(cat, cat.value),
                    "amount": amount,
                    "percentage": round((amount / current_expenses * 100) if current_expenses > 0 else 0, 1)
                }
                for cat, amount in category_totals.items()
            ],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]
        
        expense_change = 0.0
        if previous_expenses > 0:
            expense_change = round(((current_expenses - previous_expenses) / previous_expenses) * 100, 1)
        
        income_change = 0.0
        if previous_income > 0:
            income_change = round(((current_income - previous_income) / previous_income) * 100, 1)
        
        return {
            "totalBalance": total_balance,
            "balanceByCurrency": balances_by_currency,
            "currentMonth": {
                "expenses": current_expenses,
                "income": current_income,
                "expenseChange": expense_change,
                "incomeChange": income_change
            },
            "topCategories": top_categories,
            "accountsCount": len(accounts)
        }
    
    def get_categories_breakdown(
        self,
        user_id: int,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Детальная разбивка расходов по категориям
        """
        accounts = self.account_service.get_user_accounts(user_id, None)
        
        category_data = {}
        
        # Обрабатываем транзакции из Bank API
        for account in accounts:
            try:
                transactions = self.account_service.get_account_transactions(
                    user_id,
                    account["accountId"],
                    account["clientId"]
                )
                
                for txn in transactions:
                    try:
                        txn_date = datetime.fromisoformat(txn["date"].replace('Z', '+00:00'))
                        
                        if start_date:
                            start = datetime.fromisoformat(start_date)
                            if txn_date < start:
                                continue
                        
                        if end_date:
                            end = datetime.fromisoformat(end_date)
                            if txn_date > end:
                                continue
                        
                        if txn.get("type") == "debit":
                            category = categorize_transaction(
                                txn.get("mccCode", ""),
                                txn.get("description", "")
                            )
                            
                            if category not in category_data:
                                category_data[category] = {
                                    "amount": 0,
                                    "count": 0,
                                    "transactions": []
                                }
                            
                            category_data[category]["amount"] += abs(txn["amount"])
                            category_data[category]["count"] += 1
                            category_data[category]["transactions"].append({
                                "id": txn["id"],
                                "date": txn["date"],
                                "description": txn["description"],
                                "amount": abs(txn["amount"])
                            })
                    
                    except Exception as e:
                        logger.warning(f"Ошибка обработки транзакции: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Ошибка получения транзакций: {e}")
                continue
        
        # Обрабатываем внутренние платежи (Payment модель) - только исходящие (расходы)
        try:
            from sqlalchemy import or_
            internal_payments = self.db.query(Payment).filter(
                Payment.user_id == user_id,  # Только исходящие платежи
                Payment.status == PaymentStatus.COMPLETED,
                Payment.completed_at.isnot(None)
            ).all()
            
            for payment in internal_payments:
                try:
                    payment_date = payment.completed_at
                    if not payment_date:
                        payment_date = payment.created_at
                    
                    if start_date:
                        start = datetime.fromisoformat(start_date)
                        if payment_date < start:
                            continue
                    
                    if end_date:
                        end = datetime.fromisoformat(end_date)
                        if payment_date > end:
                            continue
                    
                    # Определяем категорию по типу платежа
                    category = TransactionCategory.OTHER
                    if payment.payment_type == PaymentType.UTILITIES:
                        category = TransactionCategory.UTILITIES
                    elif payment.payment_type == PaymentType.MOBILE or payment.payment_type == PaymentType.PHONE:
                        category = TransactionCategory.COMMUNICATIONS
                    elif payment.payment_type == PaymentType.INTERNET:
                        category = TransactionCategory.COMMUNICATIONS
                    elif payment.payment_type == PaymentType.TV:
                        category = TransactionCategory.ENTERTAINMENT
                    elif payment.payment_type == PaymentType.ELECTRICITY:
                        category = TransactionCategory.UTILITIES
                    elif payment.payment_type == PaymentType.PREMIUM:
                        category = TransactionCategory.OTHER
                    elif payment.payment_type == PaymentType.TO_PERSON or payment.payment_type == PaymentType.CARD_TO_CARD:
                        category = TransactionCategory.TRANSFERS
                    
                    if category not in category_data:
                        category_data[category] = {
                            "amount": 0,
                            "count": 0,
                            "transactions": []
                        }
                    
                    amount = float(payment.amount)
                    category_data[category]["amount"] += amount
                    category_data[category]["count"] += 1
                    category_data[category]["transactions"].append({
                        "id": f"payment_{payment.id}",
                        "date": payment_date.isoformat(),
                        "description": payment.description or f"Платеж {payment.payment_type.value}",
                        "amount": amount
                    })
                
                except Exception as e:
                    logger.warning(f"Ошибка обработки внутреннего платежа: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка получения внутренних платежей: {e}")
        
        total_amount = sum(data["amount"] for data in category_data.values())
        
        result = []
        for category, data in category_data.items():
            result.append({
                "category": category.value,
                "categoryName": CATEGORY_NAMES_RU.get(category, category.value),
                "amount": data["amount"],
                "count": data["count"],
                "percentage": round((data["amount"] / total_amount * 100) if total_amount > 0 else 0, 1),
                "topTransactions": sorted(data["transactions"], key=lambda x: x["amount"], reverse=True)[:5]
            })
        
        return sorted(result, key=lambda x: x["amount"], reverse=True)
    
    def get_advanced_insights(
        self,
        user_id: int,
        bank_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Расширенная аналитика с выводами и советами
        """
        overview = self.get_user_overview(user_id, bank_ids)
        categories = self.get_categories_breakdown(user_id)
        
        current_month = overview.get("currentMonth", {})
        expenses = current_month.get("expenses", 0)
        income = current_month.get("income", 0)
        expense_change = current_month.get("expenseChange", 0)
        income_change = current_month.get("incomeChange", 0)
        top_categories = overview.get("topCategories", [])
        total_balance = overview.get("totalBalance", 0)
        
        # Рассчитываем метрики
        savings_rate = 0.0
        if income > 0:
            savings_rate = ((income - expenses) / income) * 100
        
        avg_daily_expense = expenses / 30 if expenses > 0 else 0
        avg_daily_income = income / 30 if income > 0 else 0
        
        # Анализ категорий
        largest_category = top_categories[0] if top_categories else None
        largest_category_percent = largest_category.get("percentage", 0) if largest_category else 0
        
        # Генерируем выводы
        insights = []
        recommendations = []
        warnings = []
        
        # Анализ сбережений
        if savings_rate < 0:
            warnings.append({
                "type": "critical",
                "title": "Отрицательный баланс",
                "message": f"Ваши расходы превышают доходы на {abs(savings_rate):.1f}%. Рекомендуем пересмотреть бюджет.",
                "action": "Пересмотреть расходы"
            })
        elif savings_rate < 10:
            warnings.append({
                "type": "warning",
                "title": "Низкая норма сбережений",
                "message": f"Вы откладываете только {savings_rate:.1f}% дохода. Рекомендуется откладывать минимум 20%.",
                "action": "Увеличить сбережения"
            })
        elif savings_rate >= 20:
            insights.append({
                "type": "positive",
                "title": "Отличная норма сбережений",
                "message": f"Вы откладываете {savings_rate:.1f}% дохода. Это отличный показатель!",
                "icon": "✅"
            })
        
        # Анализ динамики расходов
        if expense_change > 15:
            warnings.append({
                "type": "warning",
                "title": "Рост расходов",
                "message": f"Ваши расходы выросли на {expense_change:.1f}% по сравнению с прошлым месяцем.",
                "action": "Проанализировать причины роста"
            })
        elif expense_change < -10:
            insights.append({
                "type": "positive",
                "title": "Снижение расходов",
                "message": f"Отлично! Ваши расходы снизились на {abs(expense_change):.1f}%.",
                "icon": "📉"
            })
        
        # Анализ динамики доходов
        if income_change > 10:
            insights.append({
                "type": "positive",
                "title": "Рост доходов",
                "message": f"Ваши доходы выросли на {income_change:.1f}%!",
                "icon": "📈"
            })
        elif income_change < -10:
            warnings.append({
                "type": "warning",
                "title": "Снижение доходов",
                "message": f"Ваши доходы снизились на {abs(income_change):.1f}%. Рекомендуем пересмотреть бюджет.",
                "action": "Адаптировать расходы"
            })
        
        # Анализ категорий
        if largest_category_percent > 50:
            recommendations.append({
                "type": "suggestion",
                "title": "Концентрация расходов",
                "message": f"Категория '{largest_category.get('categoryName', '')}' занимает {largest_category_percent:.1f}% ваших расходов. Возможно, стоит диверсифицировать траты.",
                "action": "Проанализировать категорию"
            })
        
        # Рекомендации по категориям
        if len(top_categories) > 0:
            for cat in top_categories[:3]:
                if cat.get("percentage", 0) > 30:
                    amount_str = f"{cat.get('amount', 0):,.2f} ₽".replace(',', ' ')
                    recommendations.append({
                        "type": "info",
                        "title": f"Категория: {cat.get('categoryName', '')}",
                        "message": f"Составляет {cat.get('percentage', 0):.1f}% расходов ({amount_str}).",
                        "action": "Детальный анализ"
                    })
        
        # Прогноз на следующий месяц
        forecast_expenses = expenses * 1.05  # +5% к текущим расходам
        forecast_income = income * 1.02  # +2% к текущим доходам
        forecast_balance = forecast_income - forecast_expenses
        
        # Цели и достижения
        goals = []
        if savings_rate >= 20:
            goals.append({
                "title": "Цель сбережений достигнута",
                "status": "completed",
                "message": f"Вы откладываете {savings_rate:.1f}% дохода"
            })
        else:
            goals.append({
                "title": "Цель: откладывать 20% дохода",
                "status": "in_progress",
                "progress": min(100, (savings_rate / 20) * 100),
                "message": f"Текущий показатель: {savings_rate:.1f}%"
            })
        
        # Статистика по дням недели (mock, в реальности нужно анализировать транзакции)
        weekday_stats = {
            "monday": {"expenses": expenses * 0.12, "count": 8},
            "tuesday": {"expenses": expenses * 0.15, "count": 10},
            "wednesday": {"expenses": expenses * 0.14, "count": 9},
            "thursday": {"expenses": expenses * 0.16, "count": 11},
            "friday": {"expenses": expenses * 0.18, "count": 12},
            "saturday": {"expenses": expenses * 0.15, "count": 10},
            "sunday": {"expenses": expenses * 0.10, "count": 7}
        }
        
        most_active_day = max(weekday_stats.items(), key=lambda x: x[1]["expenses"])
        
        return {
            "metrics": {
                "savingsRate": round(savings_rate, 1),
                "avgDailyExpense": round(avg_daily_expense, 2),
                "avgDailyIncome": round(avg_daily_income, 2),
                "expenseToIncomeRatio": round((expenses / income * 100) if income > 0 else 0, 1),
                "totalBalance": total_balance,
                "daysUntilPayday": 15  # Mock
            },
            "insights": insights,
            "warnings": warnings,
            "recommendations": recommendations,
            "forecast": {
                "nextMonth": {
                    "expenses": round(forecast_expenses, 2),
                    "income": round(forecast_income, 2),
                    "balance": round(forecast_balance, 2)
                }
            },
            "goals": goals,
            "patterns": {
                "mostActiveDay": {
                    "day": most_active_day[0],
                    "expenses": round(most_active_day[1]["expenses"], 2),
                    "count": most_active_day[1]["count"]
                },
                "weekdayStats": weekday_stats
            },
            "summary": {
                "totalTransactions": sum(cat.get("count", 0) for cat in categories),
                "avgTransactionAmount": round(expenses / sum(cat.get("count", 1) for cat in categories), 2) if categories else 0,
                "largestCategory": largest_category
            }
        }

