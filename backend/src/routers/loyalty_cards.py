"""
API роутер для карт лояльности
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.dependencies import get_current_user
from src.services.loyalty_card_service import LoyaltyCardService
from src.schemas.loyalty_card import (
    LoyaltyCardCreate,
    LoyaltyCardUpdate,
    LoyaltyCardResponse,
    BarcodeResponse
)


router = APIRouter(prefix="/api/loyalty-cards", tags=["Loyalty Cards"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_loyalty_card(
    card_data: LoyaltyCardCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Создать новую карту лояльности
    
    Поддерживаемые типы карт:
    - magnit (Магнит)
    - pyaterochka (Пятёрочка)
    - lenta (Лента)
    - auchan (Ашан)
    - metro (Metro)
    - letual (Летуаль)
    - golden_apple (Золотое Яблоко)
    - rivegauche (Рив Гош)
    - azbuka_vkusa (Азбука Вкуса)
    - okey (О'кей)
    - perekrestok (Перекрёсток)
    - diksi (Дикси)
    - other (Другая)
    
    Типы штрих-кодов:
    - EAN13 (по умолчанию)
    - CODE128
    - QR
    """
    try:
        card = LoyaltyCardService.create_card(db, current_user.id, card_data)
        
        return {
            "success": True,
            "data": {
                "message": "Карта лояльности успешно добавлена",
                "card": {
                    "id": card.id,
                    "card_type": card.card_type.value,
                    "card_name": LoyaltyCardService.get_card_display_name(card.card_type),
                    "masked_number": LoyaltyCardService.mask_card_number(card.card_number),
                    "barcode_type": card.barcode_type.value,
                    "created_at": card.created_at.isoformat()
                }
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=dict)
async def get_loyalty_cards(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить все карты лояльности пользователя"""
    cards = LoyaltyCardService.get_user_cards(db, current_user.id)
    
    return {
        "success": True,
        "data": [
            {
                "id": card.id,
                "card_type": card.card_type.value,
                "card_name": card.card_name or LoyaltyCardService.get_card_display_name(card.card_type),
                "masked_number": LoyaltyCardService.mask_card_number(card.card_number),
                "barcode_type": card.barcode_type.value,
                "created_at": card.created_at.isoformat()
            }
            for card in cards
        ]
    }


@router.get("/{card_id}", response_model=dict)
async def get_loyalty_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить карту по ID с полным номером"""
    card = LoyaltyCardService.get_card(db, card_id, current_user.id)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    return {
        "success": True,
        "data": {
            "id": card.id,
            "card_type": card.card_type.value,
            "card_name": card.card_name or LoyaltyCardService.get_card_display_name(card.card_type),
            "card_number": card.card_number,  # Полный номер
            "masked_number": LoyaltyCardService.mask_card_number(card.card_number),
            "barcode_type": card.barcode_type.value,
            "created_at": card.created_at.isoformat()
        }
    }


@router.get("/{card_id}/barcode", response_model=dict)
async def get_card_barcode(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Получить штрих-код или QR-код для карты
    
    Возвращает изображение в формате base64 (data:image/png;base64,...)
    которое можно сразу использовать в <img src="..." />
    """
    card = LoyaltyCardService.get_card(db, card_id, current_user.id)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    try:
        barcode_data = LoyaltyCardService.generate_barcode(
            card.card_number,
            card.barcode_type.value
        )
        
        return {
            "success": True,
            "data": {
                "barcode_data": barcode_data,
                "barcode_type": card.barcode_type.value,
                "card_number": card.card_number,
                "card_name": card.card_name or LoyaltyCardService.get_card_display_name(card.card_type)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации штрих-кода: {str(e)}"
        )


@router.put("/{card_id}", response_model=dict)
async def update_loyalty_card(
    card_id: int,
    card_data: LoyaltyCardUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновить карту лояльности"""
    card = LoyaltyCardService.update_card(db, card_id, current_user.id, card_data)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    return {
        "success": True,
        "data": {
            "message": "Карта успешно обновлена",
            "card": {
                "id": card.id,
                "card_type": card.card_type.value,
                "card_name": card.card_name or LoyaltyCardService.get_card_display_name(card.card_type),
                "masked_number": LoyaltyCardService.mask_card_number(card.card_number)
            }
        }
    }


@router.delete("/{card_id}", response_model=dict)
async def delete_loyalty_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удалить карту лояльности"""
    success = LoyaltyCardService.delete_card(db, card_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    return {
        "success": True,
        "data": {
            "message": "Карта успешно удалена"
        }
    }


@router.get("/types/list", response_model=dict)
async def get_card_types():
    """
    Получить список всех поддерживаемых типов карт
    
    Этот endpoint НЕ требует авторизации
    """
    return {
        "success": True,
        "data": [
            {"id": "magnit", "name": "Магнит", "icon": "🛒"},
            {"id": "pyaterochka", "name": "Пятёрочка", "icon": "🍎"},
            {"id": "lenta", "name": "Лента", "icon": "🏪"},
            {"id": "auchan", "name": "Ашан", "icon": "🛍️"},
            {"id": "metro", "name": "Metro", "icon": "🏬"},
            {"id": "letual", "name": "Летуаль", "icon": "💄"},
            {"id": "golden_apple", "name": "Золотое Яблоко", "icon": "✨"},
            {"id": "rivegauche", "name": "Рив Гош", "icon": "💅"},
            {"id": "azbuka_vkusa", "name": "Азбука Вкуса", "icon": "🥗"},
            {"id": "okey", "name": "О'кей", "icon": "🛒"},
            {"id": "perekrestok", "name": "Перекрёсток", "icon": "🏪"},
            {"id": "diksi", "name": "Дикси", "icon": "🛍️"},
            {"id": "other", "name": "Другая карта", "icon": "💳"}
        ]
    }

