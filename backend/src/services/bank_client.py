import logging
import httpx
from typing import Dict, Any, Optional, List
import redis
from datetime import datetime, timedelta

from src.config import settings
from src.constants.bank_config import get_bank_url, get_bank_name

logger = logging.getLogger(__name__)

class BankClient:

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _get_bank_config(self, bank_id: int) -> Dict[str, str]:
        return {
            "base_url": get_bank_url(bank_id),
            "name": get_bank_name(bank_id),
            "client_id": settings.TEAM_CLIENT_ID,
            "client_secret": settings.TEAM_CLIENT_SECRET
        }

    def get_bank_token(self, user_id: int, bank_id: int) -> str:
        token_key = f"bank_token:{user_id}:{bank_id}"

        cached_token = self.redis_client.get(token_key)
        if cached_token:
            logger.info(f"✅ Используем кешированный токен для банка {bank_id}")
            return cached_token

        bank_config = self._get_bank_config(bank_id)
        url = f"{bank_config['base_url']}/auth/bank-token"

        params = {
            "client_id": bank_config["client_id"],
            "client_secret": bank_config["client_secret"]
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, params=params)
                response.raise_for_status()

                data = response.json()
                token = data.get("access_token")

                if not token:
                    raise ValueError("Токен не получен от банка")

                self.redis_client.setex(token_key, 82800, token)

                logger.info(f"✅ Получен новый токен для банка {bank_id} ({bank_config['name']})")
                return token

        except Exception as e:
            logger.error(f"❌ Ошибка получения токена от банка {bank_id}: {e}")
            if settings.DEBUG:
                mock_token = f"mock_token_{bank_config['name']}_dev"
                logger.warning(f"⚠️  Используем mock токен для разработки")
                return mock_token
            raise

    def create_consent(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        permissions: List[str]
    ) -> str:
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/account-consents/request"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requesting-Bank": bank_config["client_id"],
            "Content-Type": "application/json"
        }

        body = {
            "client_id": client_id,
            "permissions": permissions,
            "reason": "Агрегация счетов для Bank Aggregator",
            "requesting_bank": bank_config["client_id"],
            "requesting_bank_name": "Bank Aggregator App"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()

                data = response.json()
                consent_id = data.get("consent_id")
                consent_status = data.get("status", "unknown")

                if not consent_id:
                    if consent_status == "pending":
                        logger.warning(f"⚠️  Consent pending в банке {bank_id} - требуется ручное подтверждение")
                        consent_id = data.get("request_id", f"pending_{bank_id}_{user_id}")
                    else:
                        raise ValueError("Consent ID не получен")

                consent_key = f"consent:{user_id}:{bank_id}"
                self.redis_client.setex(consent_key, settings.CONSENT_REQUEST_TTL, consent_id)

                if consent_status == "approved":
                    logger.info(f"✅ Consent {consent_id} одобрен для банка {bank_id}")
                else:
                    logger.warning(f"⚠️  Consent {consent_id} в статусе: {consent_status}")

                return consent_id

        except Exception as e:
            logger.error(f"❌ Ошибка создания consent: {e}")
            if settings.DEBUG:
                mock_consent = f"consent_{bank_id}_{user_id}_dev"
                logger.warning(f"⚠️  Используем mock consent для разработки")
                return mock_consent
            raise

    def get_accounts(
        self,
        user_id: int,
        bank_id: int,
        client_id: str
    ) -> List[Dict[str, Any]]:
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        consent_key = f"consent:{user_id}:{bank_id}"
        consent_id = self.redis_client.get(consent_key)

        if not consent_id:
            consent_id = self.create_consent(
                user_id,
                bank_id,
                client_id,
                ["ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"]
            )

        url = f"{bank_config['base_url']}/accounts"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requesting-Bank": bank_config["client_id"],
            "X-Consent-Id": consent_id
        }

        params = {
            "client_id": client_id
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                accounts = []
                if "data" in data and "account" in data["data"]:
                    for acc in data["data"]["account"]:
                        accounts.append({
                            "accountId": acc.get("accountId"),
                            "accountName": acc.get("nickname", "Счёт"),
                            "currency": acc.get("currency", "RUB"),
                            "accountType": acc.get("accountType", "Personal")
                        })

                logger.info(f"✅ Получено {len(accounts)} счетов из {bank_config['name']}")
                return accounts

        except Exception as e:
            logger.error(f"❌ Ошибка получения счетов: {e}")
            if settings.DEBUG:
                logger.warning(f"⚠️  Используем mock данные для разработки")
                return [
                    {
                        "accountId": f"{bank_config['name']}_acc_001",
                        "accountName": "Основной счёт",
                        "currency": "RUB",
                        "accountType": "Personal"
                    }
                ]
            raise

    def get_account_balance(
        self,
        user_id: int,
        bank_id: int,
        account_id: str,
        client_id: str
    ) -> Dict[str, Any]:
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        consent_key = f"consent:{user_id}:{bank_id}"
        consent_id = self.redis_client.get(consent_key)

        if not consent_id:
            consent_id = self.create_consent(
                user_id,
                bank_id,
                client_id,
                ["ReadAccountsDetail", "ReadBalances"]
            )

        url = f"{bank_config['base_url']}/accounts/{account_id}/balances"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requesting-Bank": bank_config["client_id"],
            "X-Consent-Id": consent_id
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                if "data" in data and "balance" in data["data"]:
                    balances = data["data"]["balance"]
                    if balances:
                        first_balance = balances[0]
                        return {
                            "amount": float(first_balance.get("amount", {}).get("amount", 0)),
                            "currency": first_balance.get("amount", {}).get("currency", "RUB")
                        }

                logger.info(f"✅ Получен баланс для счёта {account_id}")
                return {"amount": 0, "currency": "RUB"}

        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            if settings.DEBUG:
                import random
                return {
                    "amount": round(random.uniform(1000, 50000), 2),
                    "currency": "RUB"
                }
            raise

    def get_account_transactions(
        self,
        user_id: int,
        bank_id: int,
        account_id: str,
        client_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        consent_key = f"consent:{user_id}:{bank_id}"
        consent_id = self.redis_client.get(consent_key)

        if not consent_id:
            consent_id = self.create_consent(
                user_id,
                bank_id,
                client_id,
                ["ReadTransactionsDetail"]
            )

        url = f"{bank_config['base_url']}/accounts/{account_id}/transactions"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requesting-Bank": bank_config["client_id"],
            "X-Consent-Id": consent_id
        }

        params = {
            "limit": limit
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                transactions = []
                if "data" in data and "transaction" in data["data"]:
                    for txn in data["data"]["transaction"]:
                        amount_data = txn.get("amount", {})
                        transactions.append({
                            "id": txn.get("transactionId", ""),
                            "date": txn.get("bookingDateTime", datetime.utcnow().isoformat()),
                            "description": txn.get("transactionInformation", "Транзакция"),
                            "amount": float(amount_data.get("amount", 0)),
                            "currency": amount_data.get("currency", "RUB"),
                            "type": txn.get("creditDebitIndicator", "debit").lower()
                        })

                logger.info(f"✅ Получено {len(transactions)} транзакций для {account_id}")
                return transactions

        except Exception as e:
            logger.error(f"❌ Ошибка получения транзакций: {e}")
            if settings.DEBUG:
                import random
                transactions = []
                for i in range(min(limit, 5)):
                    transactions.append({
                        "id": f"txn_{random.randint(10000, 99999)}",
                        "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                        "description": random.choice([
                            "Покупка в магазине",
                            "Оплата ресторана",
                            "Перевод",
                            "Снятие наличных"
                        ]),
                        "amount": round(random.uniform(-500, 1000), 2),
                        "currency": "RUB",
                        "type": "debit" if random.random() > 0.3 else "credit"
                    })
                return transactions
            raise

    # ========== НОВЫЕ API ИЗ api_new.txt ==========

    def create_payment_consent_vrp(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        debtor_account: str,
        vrp_max_individual_amount: float,
        vrp_daily_limit: float,
        vrp_monthly_limit: float,
        valid_until: str
    ) -> Dict[str, Any]:
        """Создать VRP согласие для подписок (Variable Recurring Payments)"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/payment-consents/request"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requesting-Bank": bank_config["client_id"],
            "Content-Type": "application/json"
        }

        body = {
            "requesting_bank": bank_config["client_id"],
            "client_id": client_id,
            "consent_type": "vrp",
            "debtor_account": debtor_account,
            "vrp_max_individual_amount": vrp_max_individual_amount,
            "vrp_daily_limit": vrp_daily_limit,
            "vrp_monthly_limit": vrp_monthly_limit,
            "valid_until": valid_until,
            "reason": "Подписка на банковские услуги через Bank Aggregator"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()

                data = response.json()
                consent_id = data.get("consent_id") or data.get("data", {}).get("consentId")

                logger.info(f"✅ Создано VRP согласие {consent_id} для банка {bank_id}")
                return {
                    "consent_id": consent_id,
                    "status": data.get("status", "approved")
                }

        except Exception as e:
            logger.error(f"❌ Ошибка создания VRP согласия: {e}")
            if settings.DEBUG:
                mock_consent = f"vrp_consent_{bank_id}_{user_id}_dev"
                logger.warning(f"⚠️  Используем mock VRP consent для разработки")
                return {"consent_id": mock_consent, "status": "approved"}
            raise

    def get_products(
        self,
        user_id: int,
        bank_id: int,
        product_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получить каталог продуктов банка"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/products"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {}
        if product_type:
            params["product_type"] = product_type

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                
                products = []
                if isinstance(data, list):
                    products = data
                elif "data" in data:
                    if isinstance(data["data"], list):
                        products = data["data"]
                    elif "product" in data["data"]:
                        products = data["data"]["product"]

                logger.info(f"✅ Получено {len(products)} продуктов из {bank_config['name']}")
                return products

        except Exception as e:
            logger.error(f"❌ Ошибка получения продуктов: {e}")
            if settings.DEBUG:
                logger.warning(f"⚠️  Используем mock продукты для разработки")
                return [
                    {
                        "productId": f"prod-{bank_config['name']}-card-001",
                        "productType": "card",
                        "productName": "Дебетовая карта",
                        "description": "Карта с кешбеком 2%",
                        "interestRate": None,
                        "minAmount": 0,
                        "maxAmount": None
                    },
                    {
                        "productId": f"prod-{bank_config['name']}-deposit-001",
                        "productType": "deposit",
                        "productName": "Вклад Надежный",
                        "description": "Вклад под 8.5% годовых",
                        "interestRate": 8.5,
                        "minAmount": 10000,
                        "maxAmount": None
                    }
                ]
            raise

    def get_product_details(
        self,
        user_id: int,
        bank_id: int,
        product_id: str
    ) -> Dict[str, Any]:
        """Получить детали продукта"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/products/{product_id}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                return data if isinstance(data, dict) else {"data": data}

        except Exception as e:
            logger.error(f"❌ Ошибка получения деталей продукта: {e}")
            if settings.DEBUG:
                return {
                    "productId": product_id,
                    "productType": "card",
                    "productName": "Дебетовая карта",
                    "description": "Mock продукт"
                }
            raise

    def create_product_agreement_consent(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        read_product_agreements: bool = True,
        open_product_agreements: bool = True,
        close_product_agreements: bool = False,
        allowed_product_types: List[str] = None,
        max_amount: float = None,
        valid_until: str = None
    ) -> Dict[str, Any]:
        """Создать согласие на управление договорами с продуктами"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/product-agreement-consents/request"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        body = {
            "requesting_bank": bank_config["client_id"],
            "client_id": client_id,
            "read_product_agreements": read_product_agreements,
            "open_product_agreements": open_product_agreements,
            "close_product_agreements": close_product_agreements,
            "reason": "Оформление подписок на банковские услуги"
        }

        if allowed_product_types:
            body["allowed_product_types"] = allowed_product_types
        if max_amount:
            body["max_amount"] = max_amount
        if valid_until:
            body["valid_until"] = valid_until

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()

                data = response.json()
                consent_id = data.get("consent_id") or data.get("data", {}).get("consentId")

                logger.info(f"✅ Создано согласие на управление договорами {consent_id}")
                return {
                    "consent_id": consent_id,
                    "status": data.get("status", "approved")
                }

        except Exception as e:
            logger.error(f"❌ Ошибка создания согласия на управление договорами: {e}")
            if settings.DEBUG:
                mock_consent = f"product_consent_{bank_id}_{user_id}_dev"
                logger.warning(f"⚠️  Используем mock consent для разработки")
                return {"consent_id": mock_consent, "status": "approved"}
            raise

    def create_product_agreement(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        product_id: str,
        amount: float,
        term_months: Optional[int] = None,
        source_account_id: Optional[str] = None,
        product_agreement_consent_id: str = None
    ) -> Dict[str, Any]:
        """Открыть договор с продуктом (депозит, кредит, карта)"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/product-agreements"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if product_agreement_consent_id:
            headers["X-Product-Agreement-Consent-Id"] = product_agreement_consent_id
        headers["X-Requesting-Bank"] = bank_config["client_id"]

        body = {
            "product_id": product_id,
            "amount": amount
        }

        if term_months:
            body["term_months"] = term_months
        if source_account_id:
            body["source_account_id"] = source_account_id

        params = {"client_id": client_id}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body, params=params)
                response.raise_for_status()

                data = response.json()
                agreement_id = data.get("agreement_id") or data.get("data", {}).get("agreementId")

                logger.info(f"✅ Создан договор с продуктом {agreement_id}")
                return {
                    "agreement_id": agreement_id,
                    "status": data.get("status", "active")
                }

        except Exception as e:
            logger.error(f"❌ Ошибка создания договора с продуктом: {e}")
            if settings.DEBUG:
                mock_agreement = f"agreement_{bank_id}_{user_id}_{product_id}_dev"
                logger.warning(f"⚠️  Используем mock agreement для разработки")
                return {"agreement_id": mock_agreement, "status": "active"}
            raise

    def create_card(
        self,
        user_id: int,
        bank_id: int,
        client_id: str,
        account_number: str,
        card_name: str = "Visa Classic",
        card_type: str = "debit",
        consent_id: str = None
    ) -> Dict[str, Any]:
        """Выпустить новую карту и привязать к счету"""
        bank_config = self._get_bank_config(bank_id)
        token = self.get_bank_token(user_id, bank_id)

        url = f"{bank_config['base_url']}/cards"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if consent_id:
            headers["X-Consent-Id"] = consent_id
        headers["X-Requesting-Bank"] = bank_config["client_id"]

        body = {
            "account_number": account_number,
            "card_name": card_name,
            "card_type": card_type
        }

        params = {"client_id": client_id}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body, params=params)
                response.raise_for_status()

                data = response.json()
                card_id = data.get("card_id") or data.get("data", {}).get("cardId")

                logger.info(f"✅ Выпущена карта {card_id}")
                return {
                    "card_id": card_id,
                    "status": data.get("status", "active")
                }

        except Exception as e:
            logger.error(f"❌ Ошибка выпуска карты: {e}")
            if settings.DEBUG:
                mock_card = f"card_{bank_id}_{user_id}_dev"
                logger.warning(f"⚠️  Используем mock карту для разработки")
                return {"card_id": mock_card, "status": "active"}
            raise
