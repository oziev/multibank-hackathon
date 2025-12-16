"""
Сервис для работы с картами лояльности
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
import base64
from src.models.loyalty_card import LoyaltyCard, CardType, BarcodeType
from src.schemas.loyalty_card import LoyaltyCardCreate, LoyaltyCardUpdate


class LoyaltyCardService:
    """Сервис для управления картами лояльности"""
    
    # Названия магазинов на русском
    CARD_NAMES = {
        CardType.MAGNIT: "Магнит",
        CardType.PYATEROCHKA: "Пятёрочка",
        CardType.LENTA: "Лента",
        CardType.AUCHAN: "Ашан",
        CardType.METRO: "Metro",
        CardType.LETUAL: "Летуаль",
        CardType.GOLDEN_APPLE: "Золотое Яблоко",
        CardType.RIVEGAUCHE: "Рив Гош",
        CardType.AZBUKA_VKUSA: "Азбука Вкуса",
        CardType.OKEY: "О'кей",
        CardType.PEREKRESTOK: "Перекрёсток",
        CardType.DIKSI: "Дикси",
        CardType.OTHER: "Другая карта",
    }
    
    @staticmethod
    def create_card(
        db: Session, 
        user_id: int, 
        card_data: LoyaltyCardCreate
    ) -> LoyaltyCard:
        """Создать карту лояльности"""
        # Проверяем, что такой карты еще нет
        existing = db.query(LoyaltyCard).filter(
            LoyaltyCard.user_id == user_id,
            LoyaltyCard.card_type == card_data.card_type,
            LoyaltyCard.card_number == card_data.card_number
        ).first()
        
        if existing:
            raise ValueError("Карта с таким номером уже существует")
        
        card = LoyaltyCard(
            user_id=user_id,
            card_type=CardType(card_data.card_type),
            card_number=card_data.card_number,
            card_name=card_data.card_name,
            barcode_type=BarcodeType(card_data.barcode_type) if card_data.barcode_type else BarcodeType.EAN13
        )
        
        db.add(card)
        db.commit()
        db.refresh(card)
        
        return card
    
    @staticmethod
    def get_user_cards(db: Session, user_id: int) -> List[LoyaltyCard]:
        """Получить все карты пользователя"""
        return db.query(LoyaltyCard).filter(
            LoyaltyCard.user_id == user_id
        ).order_by(LoyaltyCard.created_at.desc()).all()
    
    @staticmethod
    def get_card(db: Session, card_id: int, user_id: int) -> Optional[LoyaltyCard]:
        """Получить карту по ID"""
        return db.query(LoyaltyCard).filter(
            LoyaltyCard.id == card_id,
            LoyaltyCard.user_id == user_id
        ).first()
    
    @staticmethod
    def update_card(
        db: Session, 
        card_id: int, 
        user_id: int, 
        card_data: LoyaltyCardUpdate
    ) -> Optional[LoyaltyCard]:
        """Обновить карту"""
        card = LoyaltyCardService.get_card(db, card_id, user_id)
        
        if not card:
            return None
        
        if card_data.card_name is not None:
            card.card_name = card_data.card_name
        
        if card_data.card_number is not None:
            card.card_number = card_data.card_number
        
        db.commit()
        db.refresh(card)
        
        return card
    
    @staticmethod
    def delete_card(db: Session, card_id: int, user_id: int) -> bool:
        """Удалить карту"""
        card = LoyaltyCardService.get_card(db, card_id, user_id)
        
        if not card:
            return False
        
        db.delete(card)
        db.commit()
        
        return True
    
    @staticmethod
    def mask_card_number(card_number: str) -> str:
        """Маскировать номер карты"""
        if len(card_number) <= 4:
            return card_number
        
        return "*" * (len(card_number) - 4) + card_number[-4:]
    
    @staticmethod
    def generate_barcode(card_number: str, barcode_type: str = "EAN13") -> str:
        """
        Генерировать штрих-код
        Returns: Base64 encoded PNG image
        """
        buffer = BytesIO()
        
        if barcode_type == "QR":
            # Генерируем QR код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(card_number)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(buffer, format="PNG")
        
        else:
            # Генерируем штрих-код (EAN13, CODE128 и т.д.)
            try:
                # Пытаемся создать штрих-код указанного типа
                barcode_class = barcode.get_barcode_class(barcode_type.lower())
                
                # Для EAN13 нужно ровно 12 или 13 цифр
                if barcode_type == "EAN13":
                    # Дополняем или обрезаем до 12 цифр
                    digits_only = ''.join(filter(str.isdigit, card_number))
                    if len(digits_only) < 12:
                        digits_only = digits_only.ljust(12, '0')
                    elif len(digits_only) > 12:
                        digits_only = digits_only[:12]
                    card_number = digits_only
                
                barcode_instance = barcode_class(card_number, writer=ImageWriter())
                barcode_instance.write(buffer)
            
            except Exception as e:
                # Если не удалось - используем CODE128 (более универсальный)
                barcode_class = barcode.get_barcode_class('code128')
                barcode_instance = barcode_class(card_number, writer=ImageWriter())
                barcode_instance.write(buffer)
        
        # Кодируем в base64
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def get_card_display_name(card_type: CardType) -> str:
        """Получить русское название карты"""
        return LoyaltyCardService.CARD_NAMES.get(card_type, "Карта лояльности")

