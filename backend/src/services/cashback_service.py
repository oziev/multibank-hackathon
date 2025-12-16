import logging
import json
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

from src.models.cashback import CashbackData, CashbackConsent
from src.services.account_service import AccountService
from src.constants.mcc_mapping import categorize_transaction
import redis

logger = logging.getLogger(__name__)

# Проценты кешбека по категориям (средние значения)
CASHBACK_RATES = {
    "FOOD": Decimal("4.0"),  # Продукты: 3-5%
    "RESTAURANT": Decimal("7.0"),  # Кафе/рестораны: 5-10%
    "TRANSPORT": Decimal("2.5"),  # Транспорт: 2-3%
    "ENTERTAINMENT": Decimal("1.5"),  # Развлечения: 1-2%
    "SHOPPING": Decimal("2.0"),  # Покупки: 1-3%
    "UTILITIES": Decimal("0.5"),  # Коммунальные услуги: 0.5-1%
    "HEALTH": Decimal("1.0"),  # Здоровье: 0.5-1.5%
    "EDUCATION": Decimal("1.0"),  # Образование: 0.5-1.5%
    "OTHER": Decimal("0.5")  # Остальное: 0.5-1%
}

class CashbackService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.account_service = AccountService(db, redis_client)

    def calculate_cashback(
        self,
        user_id: int,
        month: str  # Формат: YYYY-MM
    ) -> Dict:
        """Рассчитать кешбек за указанный месяц"""
        try:
            # Парсим месяц
            year, month_num = map(int, month.split("-"))
            month_start = datetime(year, month_num, 1)
            if month_num == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month_num + 1, 1)

            # Получаем все счета пользователя
            accounts = self.account_service.get_user_accounts(user_id, None)

            total_cashback = Decimal("0")
            transactions_count = 0
            category_breakdown = defaultdict(lambda: {"amount": Decimal("0"), "cashback": Decimal("0"), "count": 0})

            # Обрабатываем транзакции по всем счетам
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
                            
                            # Проверяем, что транзакция в нужном месяце
                            if not (month_start <= txn_date < month_end):
                                continue

                            # Только дебетовые транзакции (расходы)
                            if txn.get("type", "debit") != "debit":
                                continue

                            amount = Decimal(str(abs(txn["amount"])))
                            category = categorize_transaction(
                                txn.get("mccCode", ""),
                                txn.get("description", "")
                            )

                            # Получаем процент кешбека для категории
                            cashback_rate = CASHBACK_RATES.get(category, CASHBACK_RATES["OTHER"])
                            cashback_amount = (amount * cashback_rate) / Decimal("100")

                            total_cashback += cashback_amount
                            transactions_count += 1

                            category_breakdown[category]["amount"] += amount
                            category_breakdown[category]["cashback"] += cashback_amount
                            category_breakdown[category]["count"] += 1

                        except Exception as e:
                            logger.warning(f"Ошибка обработки транзакции: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Ошибка получения транзакций для счета {account['accountId']}: {e}")
                    continue

            # Вычисляем средний процент кешбека
            total_amount = sum([cat["amount"] for cat in category_breakdown.values()])
            average_rate = (total_cashback / total_amount * Decimal("100")) if total_amount > 0 else Decimal("0")

            # Форматируем разбивку по категориям
            categories_json = {}
            for category, data in category_breakdown.items():
                categories_json[category] = {
                    "amount": float(data["amount"]),
                    "cashback": float(data["cashback"]),
                    "count": data["count"],
                    "rate": float((data["cashback"] / data["amount"] * Decimal("100")) if data["amount"] > 0 else Decimal("0"))
                }

            return {
                "month": month,
                "total_cashback": float(total_cashback),
                "transactions_count": transactions_count,
                "average_cashback_rate": float(average_rate),
                "categories_breakdown": categories_json,
                "total_amount": float(total_amount)
            }

        except Exception as e:
            logger.error(f"Ошибка расчета кешбека: {e}")
            return {
                "month": month,
                "total_cashback": 0.0,
                "transactions_count": 0,
                "average_cashback_rate": 0.0,
                "categories_breakdown": {},
                "total_amount": 0.0
            }

    def get_or_create_cashback_data(
        self,
        user_id: int,
        month: str
    ) -> CashbackData:
        """Получить или создать запись о кешбеке за месяц"""
        cashback_data = self.db.query(CashbackData).filter(
            CashbackData.user_id == user_id,
            CashbackData.month == month
        ).first()

        if cashback_data:
            return cashback_data

        # Рассчитываем кешбек
        calculated = self.calculate_cashback(user_id, month)

        # Создаем новую запись
        cashback_data = CashbackData(
            user_id=user_id,
            month=month,
            total_cashback=Decimal(str(calculated["total_cashback"])),
            transactions_count=calculated["transactions_count"],
            average_cashback_rate=Decimal(str(calculated["average_cashback_rate"])),
            categories_breakdown=json.dumps(calculated["categories_breakdown"])
        )

        self.db.add(cashback_data)
        self.db.commit()
        self.db.refresh(cashback_data)

        return cashback_data

    def aggregate_cashback(self, user_id: int) -> Dict:
        """Агрегированные данные о кешбеке за все месяцы"""
        # Получаем данные за последние 12 месяцев
        months = []
        current = datetime.now()
        for i in range(12):
            month_date = current - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m")
            months.append(month_str)

        monthly_data = []
        total_cashback = Decimal("0")
        total_transactions = 0

        for month in months:
            cashback_data = self.get_or_create_cashback_data(user_id, month)
            breakdown = json.loads(cashback_data.categories_breakdown) if cashback_data.categories_breakdown else {}
            total_amount = sum([cat.get("amount", 0) for cat in breakdown.values()])
            
            monthly_data.append({
                "month": month,
                "total_cashback": float(cashback_data.total_cashback),
                "transactions_count": cashback_data.transactions_count,
                "average_cashback_rate": float(cashback_data.average_cashback_rate),
                "categories_breakdown": breakdown,
                "total_amount": total_amount
            })
            total_cashback += cashback_data.total_cashback
            total_transactions += cashback_data.transactions_count

        # Средний процент кешбека (взвешенный)
        total_amount = sum([d.get("total_amount", 0) for d in monthly_data])
        avg_rate = (total_cashback / Decimal(str(total_amount)) * Decimal("100")) if total_amount > 0 else Decimal("0")

        return {
            "total_cashback": float(total_cashback),
            "total_transactions": total_transactions,
            "average_monthly_cashback": float(total_cashback / Decimal("12")),
            "average_cashback_rate": float(avg_rate) if avg_rate else 0.0,
            "monthly_data": monthly_data
        }

    def get_categories_breakdown(
        self,
        user_id: int,
        month: Optional[str] = None
    ) -> Dict:
        """Разбивка кешбека по категориям"""
        if month:
            cashback_data = self.get_or_create_cashback_data(user_id, month)
            return json.loads(cashback_data.categories_breakdown) if cashback_data.categories_breakdown else {}
        else:
            # За последние 3 месяца
            current = datetime.now()
            categories_total = defaultdict(lambda: {"amount": Decimal("0"), "cashback": Decimal("0"), "count": 0})

            for i in range(3):
                month_date = current - timedelta(days=30 * i)
                month_str = month_date.strftime("%Y-%m")
                cashback_data = self.get_or_create_cashback_data(user_id, month_str)
                
                if cashback_data.categories_breakdown:
                    breakdown = json.loads(cashback_data.categories_breakdown)
                    for category, data in breakdown.items():
                        categories_total[category]["amount"] += Decimal(str(data["amount"]))
                        categories_total[category]["cashback"] += Decimal(str(data["cashback"]))
                        categories_total[category]["count"] += data["count"]

            result = {}
            for category, data in categories_total.items():
                result[category] = {
                    "amount": float(data["amount"]),
                    "cashback": float(data["cashback"]),
                    "count": data["count"],
                    "rate": float((data["cashback"] / data["amount"] * Decimal("100")) if data["amount"] > 0 else Decimal("0"))
                }

            return result

    def create_consent(
        self,
        user_id: int,
        partner_id: Optional[int] = None,
        expires_days: int = 90
    ) -> CashbackConsent:
        """Создать согласие на экспорт данных о кешбеке"""
        consent = CashbackConsent(
            user_id=user_id,
            partner_id=partner_id,
            consent_given="1",
            consent_date=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )

        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)

        return consent

    def export_cashback_data(
        self,
        user_id: int,
        partner_id: Optional[int] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Экспорт данных о кешбеке для партнера (требует согласия)"""
        # Проверяем согласие
        consent = self.db.query(CashbackConsent).filter(
            CashbackConsent.user_id == user_id,
            CashbackConsent.partner_id == partner_id,
            CashbackConsent.consent_given == "1"
        ).first()

        if not consent:
            return None, "Согласие на экспорт данных не предоставлено"

        if consent.expires_at and consent.expires_at < datetime.utcnow():
            return None, "Согласие на экспорт данных истекло"

        # Получаем агрегированные данные
        aggregated = self.aggregate_cashback(user_id)

        # Формируем данные для экспорта (анонимизированные)
        export_data = {
            "user_id_hash": f"user_{user_id}_hash",  # В реальности - хеш
            "total_cashback_12m": aggregated["total_cashback"],
            "average_monthly_cashback": aggregated["average_monthly_cashback"],
            "average_cashback_rate": aggregated["average_cashback_rate"],
            "total_transactions": aggregated["total_transactions"],
            "categories_breakdown": aggregated["monthly_data"][0]["categories_breakdown"] if aggregated["monthly_data"] else {}
        }

        return export_data, None

