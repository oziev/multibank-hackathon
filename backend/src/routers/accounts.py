import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import redis

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_verified_user
from src.schemas.account import (
    AccountAttachRequest,
    AccountCreateRequest,
    AccountResponse,
    BalanceResponse,
    TransactionResponse
)
from src.schemas.profile import AccountRenameRequest
from src.models.user import User
from src.services.account_service import AccountService
from src.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.post("/attach")
async def attach_account(
    request: AccountAttachRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    success, error = service.attach_account(current_user.id, request.id)

    if not success:
        return error_response(error, 400)

    return success_response({
        "message": "Счёт успешно привязан",
        "accountId": request.id
    })

@router.get("")
async def get_accounts(
    client_id: Optional[int] = Query(None, description="ID банка для фильтрации"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    accounts = service.get_user_accounts(current_user.id, client_id)
    
    logger.info(f"📊 GET /api/accounts - user_id={current_user.id}, returned {len(accounts)} accounts")
    for acc in accounts:
        logger.info(f"   Account: id={acc.get('id')}, accountId={acc.get('accountId')}, isHidden={acc.get('isHidden')}")

    return success_response(accounts)

@router.post("")
async def create_account(
    request: AccountCreateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Подключить существующий счет из банка через OAuth"""
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    account, error = service.create_account(
        current_user.id,
        request.client_id,
        None
    )

    if error:
        return error_response(error, 400)

    return success_response({
        "message": "Счёт успешно создан",
        "account": {
            "accountId": account.account_id,
            "accountName": account.account_name,
            "clientId": account.bank_id,
            "isActive": account.is_active
        }
    }, 201)

@router.post("/create-direct")
async def create_account_direct(
    request: dict,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Создать счет напрямую в нашей системе (без подключения к реальному банку)
    
    Для удобства тестирования и создания виртуальных счетов
    """
    from src.models.account import BankAccount
    import uuid
    
    client_id = request.get('clientId', 1)
    account_name = request.get('accountName', 'Новый счет')
    initial_balance = request.get('initialBalance', 0.0)
    
    # Создаем виртуальный счет
    new_account = BankAccount(
        user_id=current_user.id,
        bank_id=client_id,
        account_id=f"virtual-{uuid.uuid4().hex[:12]}",
        account_name=account_name,
        consent_id=f"virtual-consent-{uuid.uuid4().hex[:8]}",
        is_active=True,
        priority=999,
        is_hidden=False
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    # Сохраняем начальный баланс в Redis для виртуальных счетов
    if initial_balance > 0:
        redis_client = get_redis()
        balance_key = f"virtual_balance:{new_account.id}"
        redis_client.set(balance_key, str(initial_balance), ex=86400 * 30)  # 30 дней
    
    return success_response({
        "message": "✅ Виртуальный счет успешно создан!",
        "account": {
            "id": new_account.id,
            "accountId": new_account.account_id,
            "accountName": new_account.account_name,
            "clientId": new_account.bank_id,
            "isActive": new_account.is_active,
            "initialBalance": initial_balance
        }
    }, 201)

@router.get("/{account_id}")
async def get_account(
    account_id: str,
    client_id: int = Query(..., description="ID банка"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    account_info = service.get_account_info(current_user.id, account_id, client_id)

    if not account_info:
        return error_response("Счёт не найден", 404)

    return success_response(account_info)

@router.get("/{account_id}/balances")
async def get_account_balances(
    account_id: str,
    client_id: int = Query(..., description="ID банка"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    balance = service.get_account_balance(current_user.id, account_id, client_id)

    if not balance:
        return error_response("Не удалось получить баланс", 404)

    return success_response(balance)

@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    client_id: int = Query(..., description="ID банка"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    transactions = service.get_account_transactions(current_user.id, account_id, client_id)

    return success_response(transactions)

@router.get("/balances/all")
async def get_all_balances(
    client_ids: Optional[str] = Query(None, description="ID банков через запятую (1,2,3)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    bank_ids = None
    if client_ids:
        try:
            bank_ids = [int(x.strip()) for x in client_ids.split(',')]
        except ValueError:
            return error_response("Неверный формат client_ids. Используйте: 1,2,3", 400)

    balances = service.get_all_user_balances(current_user.id, bank_ids)

    return success_response(balances)

@router.get("/transactions/all")
async def get_all_transactions(
    client_ids: Optional[str] = Query(None, description="ID банков через запятую (1,2,3)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей (max 100)"),
    start_date: Optional[str] = Query(None, description="Дата начала (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Дата окончания (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)

    bank_ids = None
    if client_ids:
        try:
            bank_ids = [int(x.strip()) for x in client_ids.split(',')]
        except ValueError:
            return error_response("Неверный формат client_ids. Используйте: 1,2,3", 400)

    transactions = service.get_all_user_transactions(
        current_user.id,
        bank_ids,
        offset,
        limit,
        start_date,
        end_date
    )

    return success_response(transactions)

@router.put("/{account_id}/rename")
async def rename_account(
    account_id: int,
    request: AccountRenameRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)
    
    success, error = service.rename_account(current_user.id, account_id, request.account_name)
    
    if not success:
        return error_response(error, 404)
    
    return success_response({
        "message": "Счёт успешно переименован",
        "accountId": account_id,
        "newName": request.account_name
    })

@router.post("/{account_id}/sync")
async def force_sync_account(
    account_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    redis_client = get_redis()
    service = AccountService(db, redis_client)
    
    sync_result, error = service.force_sync_account(current_user.id, account_id)
    
    if error:
        return error_response(error, 400)
    
    return success_response({
        "message": "Счёт успешно синхронизирован",
        "syncData": sync_result
    })

@router.put("/{account_id}/priority")
async def set_account_priority(
    account_id: int,
    priority: int = Query(..., ge=1, le=100, description="Приоритет счета (1 = высший)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Установить приоритет счета для автоматического списания
    
    1 = высший приоритет (списывать первым)
    2 = второй по приоритету
    и т.д.
    """
    from src.models.account import BankAccount
    
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == current_user.id
    ).first()
    
    if not account:
        return error_response("Счёт не найден", 404)
    
    account.priority = priority
    db.commit()
    
    return success_response({
        "message": f"Приоритет установлен: {priority}",
        "accountId": account_id,
        "priority": priority
    })

@router.get("/priority-order")
async def get_accounts_by_priority(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Получить счета в порядке приоритета"""
    from src.models.account import BankAccount
    
    accounts = db.query(BankAccount).filter(
        BankAccount.user_id == current_user.id,
        BankAccount.is_active == True
    ).order_by(BankAccount.priority).all()
    
    return success_response({
        "accounts": [
            {
                "id": acc.id,
                "accountId": acc.account_id,
                "accountName": acc.account_name,
                "clientId": acc.bank_id,
                "priority": acc.priority
            }
            for acc in accounts
        ]
    })

@router.put("/{account_id}/toggle-visibility")
async def toggle_account_visibility(
    account_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Скрыть/показать баланс счета"""
    from src.models.account import BankAccount
    
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == current_user.id
    ).first()
    
    if not account:
        return error_response("Счёт не найден", 404)
    
    account.is_hidden = not account.is_hidden
    db.commit()
    
    return success_response({
        "message": f"Баланс {'скрыт' if account.is_hidden else 'показан'}",
        "accountId": account_id,
        "isHidden": account.is_hidden
    })

@router.get("/{account_id}/statement")
async def get_account_statement(
    account_id: int,
    start_date: str = Query(None, description="Дата начала (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Дата окончания (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Получить выписку по счету
    
    Возвращает детальную информацию о счете и транзакциях за период
    """
    redis_client = get_redis()
    service = AccountService(db, redis_client)
    
    from src.models.account import BankAccount
    from datetime import datetime
    
    # Проверяем доступ к счету
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == current_user.id
    ).first()
    
    if not account:
        return error_response("Счёт не найден", 404)
    
    # Получаем баланс
    try:
        balance = service.get_account_balance(
            current_user.id,
            account.account_id,
            account.bank_id
        )
    except Exception as e:
        balance = {"amount": 0, "currency": "RUB"}
    
    # Получаем транзакции
    try:
        transactions = service.get_account_transactions(
            current_user.id,
            account.account_id,
            account.bank_id
        )
        
        # Фильтруем по датам если указаны
        if start_date or end_date:
            filtered_transactions = []
            for txn in transactions:
                txn_date = datetime.fromisoformat(txn["date"].replace('Z', '+00:00')).date()
                
                if start_date:
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    if txn_date < start:
                        continue
                
                if end_date:
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    if txn_date > end:
                        continue
                
                filtered_transactions.append(txn)
            
            transactions = filtered_transactions
    except Exception as e:
        transactions = []
    
    # Считаем статистику
    total_income = sum(abs(txn["amount"]) for txn in transactions if txn.get("type") == "credit")
    total_expenses = sum(abs(txn["amount"]) for txn in transactions if txn.get("type") == "debit")
    
    return success_response({
        "account": {
            "accountId": account.account_id,
            "accountName": account.account_name,
            "bankId": account.bank_id,
            "balance": balance.get("amount", 0),
            "currency": balance.get("currency", "RUB")
        },
        "period": {
            "startDate": start_date or "N/A",
            "endDate": end_date or "N/A"
        },
        "statistics": {
            "totalIncome": total_income,
            "totalExpenses": total_expenses,
            "netAmount": total_income - total_expenses,
            "transactionCount": len(transactions)
        },
        "transactions": transactions
    })

@router.get("/statements/all")
async def get_all_accounts_statement(
    start_date: str = Query(None, description="Дата начала (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Дата окончания (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Получить общую выписку по всем счетам"""
    redis_client = get_redis()
    service = AccountService(db, redis_client)
    
    from src.models.account import BankAccount
    from datetime import datetime
    
    accounts = db.query(BankAccount).filter(
        BankAccount.user_id == current_user.id,
        BankAccount.is_active == True
    ).all()
    
    total_balance = 0.0
    all_transactions = []
    accounts_summary = []
    
    for account in accounts:
        try:
            balance = service.get_account_balance(
                current_user.id,
                account.account_id,
                account.bank_id
            )
            balance_amount = balance.get("amount", 0)
            total_balance += balance_amount
            
            transactions = service.get_account_transactions(
                current_user.id,
                account.account_id,
                account.bank_id
            )
            
            # Фильтруем по датам
            if start_date or end_date:
                filtered = []
                for txn in transactions:
                    txn_date = datetime.fromisoformat(txn["date"].replace('Z', '+00:00')).date()
                    
                    if start_date:
                        start = datetime.strptime(start_date, "%Y-%m-%d").date()
                        if txn_date < start:
                            continue
                    
                    if end_date:
                        end = datetime.strptime(end_date, "%Y-%m-%d").date()
                        if txn_date > end:
                            continue
                    
                    filtered.append(txn)
                
                transactions = filtered
            
            all_transactions.extend(transactions)
            
            account_income = sum(abs(t["amount"]) for t in transactions if t.get("type") == "credit")
            account_expenses = sum(abs(t["amount"]) for t in transactions if t.get("type") == "debit")
            
            accounts_summary.append({
                "accountId": account.account_id,
                "accountName": account.account_name,
                "balance": balance_amount,
                "income": account_income,
                "expenses": account_expenses,
                "transactionCount": len(transactions)
            })
            
        except Exception as e:
            logger.error(f"Ошибка получения данных счета {account.id}: {e}")
            continue
    
    # Общая статистика
    total_income = sum(abs(t["amount"]) for t in all_transactions if t.get("type") == "credit")
    total_expenses = sum(abs(t["amount"]) for t in all_transactions if t.get("type") == "debit")
    
    # Сортируем транзакции по дате
    all_transactions.sort(key=lambda x: x["date"], reverse=True)
    
    return success_response({
        "summary": {
            "totalBalance": total_balance,
            "totalIncome": total_income,
            "totalExpenses": total_expenses,
            "netAmount": total_income - total_expenses,
            "accountsCount": len(accounts),
            "totalTransactions": len(all_transactions)
        },
        "period": {
            "startDate": start_date or "N/A",
            "endDate": end_date or "N/A"
        },
        "accounts": accounts_summary,
        "transactions": all_transactions[:100]  # Ограничиваем 100 транзакциями
    })
