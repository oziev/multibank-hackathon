"""
API роутер для платежей и переводов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.services.payment_service import PaymentService
from src.schemas.payment import (
    TransferRequest,
    TransferByPhoneRequest,
    UtilityPaymentRequest,
    PaymentResponse,
    PaymentHistoryItem,
    UserSearchResult
)


router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("/transfer-by-phone", response_model=dict)
@router.post("/to-person", response_model=dict)
async def transfer_by_phone(
    request: TransferByPhoneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Перевод денег зарегистрированному пользователю по номеру телефона
    
    Это внутренний перевод в нашей системе.
    Деньги НЕ списываются с реального счета (это sandbox).
    """
    try:
        payment, error = PaymentService.create_internal_transfer(
            db,
            current_user.id,
            request.from_account_id,
            request.to_phone,
            request.amount,
            request.description
        )
        
        if error:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Платеж уже сохранен в PaymentService.create_internal_transfer
        # Просто обновляем его из БД
        db.refresh(payment)
        
        return {
            "success": True,
            "data": {
                "message": f"Перевод {request.amount}₽ успешно выполнен!",
                "payment": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status.value,
                    "to_name": payment.to_name,
                    "to_phone": payment.to_phone,
                    "description": payment.description,
                    "created_at": payment.created_at.isoformat(),
                    "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
                }
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания перевода: {str(e)}"
        )


@router.post("/transfer-card", response_model=dict)
async def transfer_card(
    request: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Перевод на карту по номеру счета"""
    if not request.to_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите номер счета получателя"
        )
    
    payment, error = PaymentService.create_card_transfer(
        db,
        current_user.id,
        request.from_account_id,
        request.to_account,
        request.to_account,  # to_name пока = номеру счета
        request.amount,
        request.description
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "success": True,
        "data": {
            "message": "Перевод отправлен в обработку",
            "payment": {
                "id": payment.id,
                "amount": payment.amount,
                "status": payment.status.value,
                "to_account": payment.to_account
            }
        }
    }


@router.post("/utility", response_model=dict)
async def pay_utility(
    request: UtilityPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Оплата услуг (ЖКХ, связь, интернет и т.д.)"""
    payment, error = PaymentService.create_utility_payment(
        db,
        current_user.id,
        request.from_account_id,
        request.payment_type,
        request.provider,
        request.account_number,
        request.amount
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "success": True,
        "data": {
            "message": f"Платеж {request.amount}₽ успешно выполнен!",
            "payment": {
                "id": payment.id,
                "amount": payment.amount,
                "status": payment.status.value,
                "provider": request.provider,
                "account_number": request.account_number
            }
        }
    }


@router.get("/history", response_model=dict)
async def get_payment_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить историю платежей пользователя"""
    payments = PaymentService.get_user_payments(db, current_user.id, limit, offset)
    
    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "paymentType": p.payment_type.value,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status.value,
                "description": p.description,
                "toName": p.to_name,
                "toPhone": p.to_phone,
                "toUserId": p.to_user_id,  # Добавляем ID получателя
                "fromUserId": p.user_id,  # Добавляем ID отправителя
                "fromAccountName": p.from_account_name,
                "createdAt": p.created_at.isoformat(),
                "completedAt": p.completed_at.isoformat() if p.completed_at else None,
                "isIncoming": p.to_user_id == current_user.id if p.to_user_id else False  # Флаг входящего платежа
            }
            for p in payments
        ],
        "pagination": {
            "total": len(payments),
            "limit": limit,
            "offset": offset
        }
    }


@router.get("/search-user", response_model=dict)
async def search_user_by_phone(
    phone: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Поиск пользователя по номеру телефона для перевода
    
    Возвращает информацию о получателе, если он зарегистрирован
    """
    user = PaymentService.search_user_by_phone(db, phone)
    
    if not user:
        return {
            "success": False,
            "error": {
                "message": "Пользователь с таким номером не найден"
            }
        }
    
    return {
        "success": True,
        "data": {
            "userId": user.id,
            "name": user.name,
            "phone": user.phone,
            "avatarUrl": user.avatar_url
        }
    }

