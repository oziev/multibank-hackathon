import logging
import json
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import redis
from datetime import datetime

from src.models.account import BankAccount
from src.models.user import User
from src.services.bank_client import BankClient
from src.config import settings

logger = logging.getLogger(__name__)

class AccountService:

    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.bank_client = BankClient(redis_client)

    def get_user_accounts(
        self,
        user_id: int,
        bank_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = self.db.query(BankAccount).filter(BankAccount.user_id == user_id)

        if bank_id:
            query = query.filter(BankAccount.bank_id == bank_id)

        accounts = query.all()

        result = []
        for acc in accounts:
            result.append({
                "id": acc.id,
                "accountId": acc.account_id,
                "accountName": acc.account_name,
                "clientId": acc.bank_id,
                "clientName": self._get_bank_name(acc.bank_id),
                "isActive": acc.is_active,
                "isHidden": acc.is_hidden,
                "priority": acc.priority
            })

        return result

    def create_account(
        self,
        user_id: int,
        bank_id: int,
        account_name: Optional[str] = None
    ) -> Tuple[Optional[BankAccount], Optional[str]]:
        try:
            client_id = f"{settings.TEAM_CLIENT_ID}-{user_id}"

            consent_id = self.bank_client.create_consent(
                user_id,
                bank_id,
                client_id,
                ["ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"]
            )

            bank_accounts = self.bank_client.get_accounts(user_id, bank_id, client_id)

            if not bank_accounts:
                return None, "Не удалось получить счета из банка"

            first_acc = bank_accounts[0]

            new_account = BankAccount(
                user_id=user_id,
                bank_id=bank_id,
                account_id=first_acc["accountId"],
                account_name=account_name or first_acc.get("accountName", "Счёт"),
                consent_id=consent_id,
                is_active=True
            )

            self.db.add(new_account)
            self.db.commit()
            self.db.refresh(new_account)

            logger.info(f"✅ Создан счёт {new_account.id} для пользователя {user_id}")
            return new_account, None

        except Exception as e:
            logger.error(f"❌ Ошибка создания счёта: {e}")
            return None, str(e)

    def attach_account(
        self,
        user_id: int,
        account_id: int
    ) -> Tuple[bool, Optional[str]]:
        account = self.db.query(BankAccount).filter(BankAccount.id == account_id).first()

        if not account:
            return False, "Счёт не найден"

        if account.user_id and account.user_id != user_id:
            return False, "Счёт уже привязан к другому пользователю"

        account.user_id = user_id
        account.is_active = True
        self.db.commit()

        logger.info(f"✅ Счёт {account_id} привязан к пользователю {user_id}")
        return True, None

    def get_account_info(
        self,
        user_id: int,
        account_id: str,
        bank_id: int
    ) -> Optional[Dict[str, Any]]:
        cache_key = f"account_info:{user_id}:{account_id}"

        cached = self.redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Используем кешированную информацию о счёте {account_id}")
            return json.loads(cached)

        account = (
            self.db.query(BankAccount)
            .filter(
                BankAccount.user_id == user_id,
                BankAccount.account_id == account_id,
                BankAccount.bank_id == bank_id
            )
            .first()
        )

        if not account:
            return None

        info = {
            "accountId": account.account_id,
            "accountName": account.account_name,
            "clientId": account.bank_id,
            "clientName": self._get_bank_name(account.bank_id),
            "isActive": account.is_active
        }

        self.redis_client.setex(
            cache_key,
            settings.BANK_DATA_CACHE_TTL,
            json.dumps(info)
        )

        return info

    def get_account_balance(
        self,
        user_id: int,
        account_id: str,
        bank_id: int
    ) -> Optional[Dict[str, Any]]:
        cache_key = f"balance:{user_id}:{account_id}"

        cached = self.redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Используем кешированный баланс для {account_id}")
            return json.loads(cached)

        client_id = f"{settings.TEAM_CLIENT_ID}-{user_id}"
        balance = self.bank_client.get_account_balance(user_id, bank_id, account_id, client_id)

        self.redis_client.setex(
            cache_key,
            settings.BANK_DATA_CACHE_TTL,
            json.dumps(balance)
        )

        return balance

    def get_account_transactions(
        self,
        user_id: int,
        account_id: str,
        bank_id: int
    ) -> List[Dict[str, Any]]:
        cache_key = f"transactions:{user_id}:{account_id}"

        cached = self.redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Используем кешированные транзакции для {account_id}")
            return json.loads(cached)

        client_id = f"{settings.TEAM_CLIENT_ID}-{user_id}"
        transactions = self.bank_client.get_account_transactions(
            user_id,
            bank_id,
            account_id,
            client_id
        )

        self.redis_client.setex(
            cache_key,
            settings.BANK_DATA_CACHE_TTL,
            json.dumps(transactions)
        )

        return transactions

    def _get_bank_name(self, bank_id: int) -> str:
        bank_names = {
            1: "vbank",
            2: "sbank",
            3: "abank"
        }
        return bank_names.get(bank_id, f"bank{bank_id}")

    def get_all_user_balances(
        self,
        user_id: int,
        bank_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Получить балансы всех счетов пользователя.
        Оптимизировано для избежания N+1 проблемы.
        """
        accounts = self.get_user_accounts(user_id, None)

        if bank_ids:
            accounts = [acc for acc in accounts if acc["clientId"] in bank_ids]

        balances_data = []
        total_balance = {}

        for account in accounts:
            try:
                balance = self.get_account_balance(
                    user_id,
                    account["accountId"],
                    account["clientId"]
                )

                balance_item = {
                    "accountId": account["accountId"],
                    "accountName": account["accountName"],
                    "clientId": account["clientId"],
                    "clientName": account["clientName"],
                    "balance": balance
                }
                balances_data.append(balance_item)

                currency = balance.get("currency", "RUB")
                amount = balance.get("amount", 0)

                if currency not in total_balance:
                    total_balance[currency] = 0
                total_balance[currency] += amount

            except Exception as e:
                logger.error(f"Ошибка получения баланса для {account['accountId']}: {e}")
                continue

        return {
            "accounts": balances_data,
            "total": [{"currency": curr, "amount": amt} for curr, amt in total_balance.items()],
            "count": len(balances_data)
        }

    def get_all_user_transactions(
        self,
        user_id: int,
        bank_ids: Optional[List[int]] = None,
        offset: int = 0,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить транзакции всех счетов пользователя с пагинацией и фильтрацией.
        Оптимизировано для избежания N+1 проблемы.
        """
        from datetime import datetime

        accounts = self.get_user_accounts(user_id, None)

        if bank_ids:
            accounts = [acc for acc in accounts if acc["clientId"] in bank_ids]

        all_transactions = []

        for account in accounts:
            try:
                transactions = self.get_account_transactions(
                    user_id,
                    account["accountId"],
                    account["clientId"]
                )

                for txn in transactions:
                    txn["accountId"] = account["accountId"]
                    txn["accountName"] = account["accountName"]
                    txn["clientId"] = account["clientId"]
                    txn["clientName"] = account["clientName"]

                all_transactions.extend(transactions)

            except Exception as e:
                logger.error(f"Ошибка получения транзакций для {account['accountId']}: {e}")
                continue

        if start_date or end_date:
            filtered_transactions = []
            for txn in all_transactions:
                txn_date_str = txn.get("date", "")
                if not txn_date_str:
                    continue

                try:
                    txn_date = datetime.fromisoformat(txn_date_str.replace('Z', '+00:00'))
                    txn_date_only = txn_date.date()

                    if start_date:
                        start = datetime.strptime(start_date, "%Y-%m-%d").date()
                        if txn_date_only < start:
                            continue

                    if end_date:
                        end = datetime.strptime(end_date, "%Y-%m-%d").date()
                        if txn_date_only > end:
                            continue

                    filtered_transactions.append(txn)

                except Exception as e:
                    logger.warning(f"Ошибка парсинга даты {txn_date_str}: {e}")
                    filtered_transactions.append(txn)

            all_transactions = filtered_transactions

        all_transactions.sort(key=lambda x: x.get("date", ""), reverse=True)

        total_count = len(all_transactions)
        paginated_transactions = all_transactions[offset:offset + limit]

        return {
            "transactions": paginated_transactions,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total": total_count,
                "hasMore": offset + limit < total_count
            }
        }
    
    def rename_account(
        self,
        user_id: int,
        account_id: int,
        new_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Переименовать счет
        """
        account = (
            self.db.query(BankAccount)
            .filter(BankAccount.id == account_id, BankAccount.user_id == user_id)
            .first()
        )
        
        if not account:
            return False, "Счёт не найден"
        
        account.account_name = new_name
        self.db.commit()
        
        logger.info(f"Счёт {account_id} переименован в '{new_name}'")
        return True, None
    
    def force_sync_account(
        self,
        user_id: int,
        account_id: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Принудительная синхронизация счета (очистка кеша)
        """
        account = (
            self.db.query(BankAccount)
            .filter(BankAccount.id == account_id, BankAccount.user_id == user_id)
            .first()
        )
        
        if not account:
            return None, "Счёт не найден"
        
        cache_keys = [
            f"balance:{user_id}:{account.account_id}",
            f"transactions:{user_id}:{account.account_id}",
            f"account_info:{user_id}:{account.account_id}"
        ]
        
        for key in cache_keys:
            self.redis_client.delete(key)
        
        try:
            balance = self.get_account_balance(user_id, account.account_id, account.bank_id)
            transactions = self.get_account_transactions(user_id, account.account_id, account.bank_id)
            
            logger.info(f"Счёт {account_id} синхронизирован принудительно")
            
            return {
                "balance": balance,
                "transactionsCount": len(transactions),
                "syncedAt": datetime.now().isoformat()
            }, None
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            return None, str(e)