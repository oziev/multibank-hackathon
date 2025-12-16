import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MockBankService:
    """
    Микросервис/заглушки для данных, которых нет в банковском API.
    Используется для эмуляции банковских операций и предоставления данных,
    которые не доступны через стандартное Open Banking API.
    """

    @staticmethod
    def create_mock_account(
        user_id: int,
        bank_id: int,
        account_type: str = "checking",
        initial_balance: float = 0.0
    ) -> Dict:
        """Создать тестовый счет (заглушка)"""
        account_id = f"mock_acc_{bank_id}_{user_id}_{random.randint(1000, 9999)}"
        
        return {
            "accountId": account_id,
            "accountName": f"Тестовый {account_type} счет",
            "currency": "RUB",
            "accountType": account_type,
            "balance": initial_balance,
            "isMock": True
        }

    @staticmethod
    def create_mock_card(
        user_id: int,
        bank_id: int,
        account_number: str,
        card_type: str = "debit"
    ) -> Dict:
        """Выпустить тестовую карту (заглушка)"""
        card_id = f"mock_card_{bank_id}_{user_id}_{random.randint(1000, 9999)}"
        
        # Генерируем номер карты (формат: 16 цифр)
        card_number = f"4{random.randint(100000000000000, 999999999999999)}"
        
        return {
            "cardId": card_id,
            "cardNumber": card_number,
            "maskedNumber": f"{card_number[:4]} **** **** {card_number[-4:]}",
            "cardType": card_type,
            "cardName": "Visa Classic",
            "status": "active",
            "accountNumber": account_number,
            "isMock": True
        }

    @staticmethod
    def get_mock_products(bank_id: int) -> List[Dict]:
        """Получить каталог тестовых продуктов"""
        products = [
            {
                "productId": f"mock_prod_{bank_id}_card_001",
                "productType": "card",
                "productName": "Дебетовая карта с кешбеком",
                "description": "Карта с кешбеком 2% на все покупки",
                "interestRate": None,
                "minAmount": 0,
                "maxAmount": None,
                "features": ["cashback", "mobile_payment"]
            },
            {
                "productId": f"mock_prod_{bank_id}_deposit_001",
                "productType": "deposit",
                "productName": "Вклад Надежный",
                "description": "Вклад под 8.5% годовых, от 10,000₽",
                "interestRate": 8.5,
                "minAmount": 10000,
                "maxAmount": None,
                "termMonths": 12
            },
            {
                "productId": f"mock_prod_{bank_id}_loan_001",
                "productType": "loan",
                "productName": "Потребительский кредит",
                "description": "Кредит до 3,000,000₽ под 12.9% годовых",
                "interestRate": 12.9,
                "minAmount": 100000,
                "maxAmount": 3000000,
                "termMonths": 60
            },
            {
                "productId": f"mock_prod_{bank_id}_premium_001",
                "productType": "premium_service",
                "productName": "Премиум подписка банка",
                "description": "Премиум услуги банка с расширенными возможностями",
                "interestRate": None,
                "minAmount": 0,
                "monthlyFee": 299
            }
        ]

        return products

    @staticmethod
    def get_mock_cashback_info(
        user_id: int,
        month: str
    ) -> Dict:
        """Получить информацию о кешбеке (заглушка для данных, которых нет в API)"""
        # Эмулируем данные о кешбеке
        return {
            "month": month,
            "total_cashback": round(random.uniform(500, 5000), 2),
            "average_rate": round(random.uniform(1.5, 5.0), 2),
            "transactions_with_cashback": random.randint(10, 100),
            "categories": {
                "FOOD": {
                    "cashback": round(random.uniform(100, 1000), 2),
                    "rate": 4.0
                },
                "RESTAURANT": {
                    "cashback": round(random.uniform(50, 500), 2),
                    "rate": 7.0
                },
                "TRANSPORT": {
                    "cashback": round(random.uniform(20, 200), 2),
                    "rate": 2.5
                }
            },
            "isMock": True
        }

    @staticmethod
    def get_mock_family_accounts(
        user_id: int,
        family_member_ids: List[int]
    ) -> List[Dict]:
        """Получить счета членов семьи (заглушка для межбанковского доступа)"""
        # В реальности это должно работать через согласия, но для данных,
        # которых нет в API, используем заглушки
        accounts = []
        for member_id in family_member_ids:
            accounts.append({
                "userId": member_id,
                "accountId": f"mock_family_acc_{member_id}",
                "accountName": "Семейный счет",
                "balance": round(random.uniform(1000, 50000), 2),
                "currency": "RUB",
                "isMock": True
            })
        return accounts

    @staticmethod
    def simulate_bank_operation(
        operation_type: str,
        **kwargs
    ) -> Dict:
        """Симулировать банковскую операцию (для тестирования)"""
        operations = {
            "card_issue": lambda: {
                "status": "completed",
                "card_id": f"card_{random.randint(100000, 999999)}",
                "estimated_delivery": (datetime.now() + timedelta(days=7)).isoformat()
            },
            "account_open": lambda: {
                "status": "completed",
                "account_id": f"acc_{random.randint(100000, 999999)}",
                "account_number": f"40817{random.randint(1000000000, 9999999999)}"
            },
            "deposit_open": lambda: {
                "status": "completed",
                "agreement_id": f"dep_{random.randint(100000, 999999)}",
                "interest_rate": 8.5
            }
        }

        if operation_type in operations:
            return operations[operation_type]()
        else:
            return {"status": "unknown", "error": f"Unknown operation: {operation_type}"}

