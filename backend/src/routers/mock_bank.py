import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.services.mock_bank_service import MockBankService
from src.utils.responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mock-bank", tags=["Mock Bank"])

@router.post("/accounts")
async def create_mock_account(
    bank_id: int = Query(..., description="ID банка"),
    account_type: str = Query("checking", description="Тип счета (checking, savings)"),
    initial_balance: float = Query(0.0, description="Начальный баланс"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать тестовый счет (заглушка для данных, которых нет в API)"""
    try:
        account = MockBankService.create_mock_account(
            current_user.id,
            bank_id,
            account_type,
            initial_balance
        )
        return success_response(account)
    except Exception as e:
        logger.error(f"Ошибка создания тестового счета: {e}")
        return {"success": False, "error": str(e)}, 500

@router.post("/cards")
async def create_mock_card(
    bank_id: int = Query(..., description="ID банка"),
    account_number: str = Query(..., description="Номер счета"),
    card_type: str = Query("debit", description="Тип карты (debit, credit)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выпустить тестовую карту (заглушка)"""
    try:
        card = MockBankService.create_mock_card(
            current_user.id,
            bank_id,
            account_number,
            card_type
        )
        return success_response(card)
    except Exception as e:
        logger.error(f"Ошибка выпуска тестовой карты: {e}")
        return {"success": False, "error": str(e)}, 500

@router.get("/products")
async def get_mock_products(
    bank_id: int = Query(..., description="ID банка"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить каталог тестовых продуктов (заглушка)"""
    try:
        products = MockBankService.get_mock_products(bank_id)
        return success_response({"products": products})
    except Exception as e:
        logger.error(f"Ошибка получения продуктов: {e}")
        return {"success": False, "error": str(e)}, 500

@router.get("/cashback")
async def get_mock_cashback(
    month: Optional[str] = Query(None, description="Месяц в формате YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о кешбеке (заглушка для данных, которых нет в API)"""
    try:
        from datetime import datetime
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        cashback_info = MockBankService.get_mock_cashback_info(current_user.id, month)
        return success_response(cashback_info)
    except Exception as e:
        logger.error(f"Ошибка получения информации о кешбеке: {e}")
        return {"success": False, "error": str(e)}, 500

