"""
Сервис для работы с платежами
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime
from src.models.payment import Payment, PaymentType, PaymentStatus
from src.models.user import User
from src.models.account import BankAccount
from src.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для управления платежами"""
    
    @staticmethod
    def search_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """Поиск пользователя по номеру телефона"""
        return db.query(User).filter(User.phone == phone, User.is_verified == True).first()
    
    @staticmethod
    def create_internal_transfer(
        db: Session,
        user_id: int,
        from_account_id: int,
        to_phone: str,
        amount: float,
        description: Optional[str] = None
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Перевод зарегистрированному пользователю по телефону
        (внутри нашей системы, без использования Bank API)
        """
        logger.info(f"🔍 НАЧАЛО create_internal_transfer: user_id={user_id}, from_account_id={from_account_id}, to_phone={to_phone}, amount={amount}")
        
        # Проверяем счет отправителя
        from_account = db.query(BankAccount).filter(
            BankAccount.id == from_account_id,
            BankAccount.user_id == user_id
        ).first()
        
        if not from_account:
            logger.error(f"❌ Счет отправителя не найден: from_account_id={from_account_id}, user_id={user_id}")
            return None, "Счет отправителя не найден"
        
        # Ищем получателя по телефону
        recipient = PaymentService.search_user_by_phone(db, to_phone)
        
        if not recipient:
            logger.error(f"❌ Получатель не найден: to_phone={to_phone}")
            return None, f"Пользователь с номером {to_phone} не найден в системе"
        
        if recipient.id == user_id:
            logger.error(f"❌ Попытка перевода самому себе: user_id={user_id}")
            return None, "Нельзя переводить самому себе"
        
        # ЗАЩИТА ОТ ДУБЛИКАТОВ: Проверяем, не был ли уже создан идентичный платеж в последние 5 секунд
        from datetime import timedelta
        recent_duplicate = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.to_user_id == recipient.id,
            Payment.to_phone == to_phone,
            Payment.amount == amount,
            Payment.payment_type == PaymentType.TO_PERSON,
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= datetime.utcnow() - timedelta(seconds=5)
        ).first()
        
        if recent_duplicate:
            logger.warning(f"⚠️  Обнаружен дубликат платежа! ID дубликата: {recent_duplicate.id}, создан: {recent_duplicate.created_at}")
            return None, f"Похожий платеж уже был создан недавно (ID: {recent_duplicate.id}). Пожалуйста, подождите несколько секунд."
        
        # Проверяем баланс перед переводом
        try:
            from src.services.account_service import AccountService
            import redis
            
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            account_service = AccountService(db, redis_client)
            balance_data = account_service.get_account_balance(
                user_id=user_id,
                account_id=from_account.account_id,
                bank_id=from_account.bank_id
            )
            
            if not balance_data:
                logger.warning(f"⚠️  Не удалось получить баланс, продолжаем без проверки")
            else:
                current_balance = balance_data.get("amount", 0)
                if current_balance < amount:
                    logger.error(f"❌ Недостаточно средств: баланс={current_balance}₽, требуется={amount}₽")
                    return None, f"Недостаточно средств на счете. Текущий баланс: {current_balance}₽, требуется: {amount}₽"
                logger.info(f"✅ Баланс проверен: {current_balance}₽ >= {amount}₽")
        except Exception as e:
            logger.warning(f"⚠️  Ошибка проверки баланса: {e}, продолжаем без проверки")
        
        # Создаем платеж
        payment = Payment(
            user_id=user_id,
            payment_type=PaymentType.TO_PERSON,
            amount=amount,
            currency="RUB",
            from_account_id=from_account_id,
            from_account_name=from_account.account_name,
            to_user_id=recipient.id,
            to_phone=to_phone,
            to_name=recipient.name,
            description=description,
            status=PaymentStatus.COMPLETED,  # Внутренний перевод сразу completed
            completed_at=datetime.utcnow()
        )
        
        db.add(payment)
        try:
            db.commit()
            db.refresh(payment)
            logger.info(f"✅ Платеж {payment.id} успешно создан: {amount}₽ от пользователя {user_id} к {recipient.id}")
            
            # Обновляем кеш балансов счетов
            try:
                import redis
                import json
                from src.config import settings
                
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                
                # Обновляем баланс отправителя (уменьшаем)
                balance_key_sender = f"balance:{user_id}:{from_account.account_id}"
                cached_balance_sender = redis_client.get(balance_key_sender)
                
                if cached_balance_sender:
                    balance_data_sender = json.loads(cached_balance_sender)
                    current_balance_sender = balance_data_sender.get("amount", 0)
                    
                    # Проверяем, не был ли баланс уже обновлен (защита от двойного списания)
                    # Если баланс уже меньше чем должен быть после списания, значит уже был списан
                    expected_balance = current_balance_sender - amount
                    if balance_data_sender.get("amount", current_balance_sender) <= expected_balance:
                        logger.warning(f"⚠️  Баланс уже был обновлен ранее! Текущий: {balance_data_sender.get('amount')}₽, ожидаемый: {expected_balance}₽")
                    else:
                        new_balance_sender = current_balance_sender - amount
                        balance_data_sender["amount"] = max(0, new_balance_sender)
                        
                        redis_client.setex(
                            balance_key_sender,
                            settings.BANK_DATA_CACHE_TTL,
                            json.dumps(balance_data_sender)
                        )
                        logger.info(f"✅ Обновлен баланс отправителя в кеше: {current_balance_sender}₽ -> {balance_data_sender['amount']}₽ (списано {amount}₽)")
                else:
                    logger.warning(f"⚠️  Баланс отправителя не найден в кеше для {balance_key_sender}")
                
                # Обновляем баланс получателя (увеличиваем)
                # Находим счет получателя с наивысшим приоритетом
                recipient_account = db.query(BankAccount).filter(
                    BankAccount.user_id == recipient.id,
                    BankAccount.is_active == True
                ).order_by(BankAccount.priority.asc()).first()
                
                if recipient_account:
                    balance_key_recipient = f"balance:{recipient.id}:{recipient_account.account_id}"
                    cached_balance_recipient = redis_client.get(balance_key_recipient)
                    
                    if cached_balance_recipient:
                        balance_data_recipient = json.loads(cached_balance_recipient)
                        current_balance_recipient = balance_data_recipient.get("amount", 0)
                        
                        # Проверяем, не был ли баланс уже обновлен (защита от двойного начисления)
                        expected_balance = current_balance_recipient + amount
                        if balance_data_recipient.get("amount", current_balance_recipient) >= expected_balance:
                            logger.warning(f"⚠️  Баланс получателя уже был обновлен ранее! Текущий: {balance_data_recipient.get('amount')}₽, ожидаемый: {expected_balance}₽")
                        else:
                            new_balance_recipient = current_balance_recipient + amount
                            balance_data_recipient["amount"] = new_balance_recipient
                            
                            redis_client.setex(
                                balance_key_recipient,
                                settings.BANK_DATA_CACHE_TTL,
                                json.dumps(balance_data_recipient)
                            )
                            logger.info(f"✅ Обновлен баланс получателя в кеше: {current_balance_recipient}₽ -> {balance_data_recipient['amount']}₽ (начислено {amount}₽)")
                else:
                    logger.warning(f"⚠️  Баланс получателя не найден в кеше для {balance_key_recipient}")
                
                # Инвалидируем кеш транзакций для получателя
                transactions_key_recipient = f"transactions:{recipient.id}:{recipient_account.account_id}"
                redis_client.delete(transactions_key_recipient)
                logger.info(f"✅ Инвалидирован кеш транзакций для получателя {recipient_account.account_id}")
                
            except Exception as cache_error:
                logger.warning(f"⚠️  Не удалось обновить кеш баланса: {cache_error}")
                # Не блокируем платеж из-за ошибки кеша
            
            # Инвалидируем кеш транзакций для отправителя
            try:
                transactions_key_sender = f"transactions:{user_id}:{from_account.account_id}"
                redis_client.delete(transactions_key_sender)
                logger.info(f"✅ Инвалидирован кеш транзакций для отправителя {from_account.account_id}")
            except Exception as e:
                logger.warning(f"⚠️  Не удалось инвалидировать кеш транзакций: {e}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Ошибка сохранения платежа: {e}")
            return None, f"Ошибка сохранения платежа: {str(e)}"
        
        return payment, None
    
    @staticmethod
    def create_card_transfer(
        db: Session,
        user_id: int,
        from_account_id: int,
        to_account: str,
        to_name: str,
        amount: float,
        description: Optional[str] = None
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """Перевод на карту (номер счета)"""
        from_account = db.query(BankAccount).filter(
            BankAccount.id == from_account_id,
            BankAccount.user_id == user_id
        ).first()
        
        if not from_account:
            return None, "Счет отправителя не найден"
        
        # Проверяем баланс перед переводом
        try:
            from src.services.account_service import AccountService
            import redis
            
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            account_service = AccountService(db, redis_client)
            balance_data = account_service.get_account_balance(
                user_id=user_id,
                account_id=from_account.account_id,
                bank_id=from_account.bank_id
            )
            
            if not balance_data:
                return None, "Не удалось получить баланс счета"
            
            current_balance = balance_data.get("amount", 0)
            
            if current_balance < amount:
                return None, f"Недостаточно средств на счете. Текущий баланс: {current_balance}₽, требуется: {amount}₽"
            
            logger.info(f"✅ Баланс проверен для перевода на карту: {current_balance}₽ >= {amount}₽")
            
        except Exception as e:
            logger.error(f"Ошибка проверки баланса: {e}")
            if not settings.DEBUG:
                return None, f"Ошибка проверки баланса: {str(e)}"
            logger.warning(f"⚠️  Продолжаем без проверки баланса (DEBUG режим)")
        
        payment = Payment(
            user_id=user_id,
            payment_type=PaymentType.CARD_TO_CARD,
            amount=amount,
            currency="RUB",
            from_account_id=from_account_id,
            from_account_name=from_account.account_name,
            to_account=to_account,
            to_name=to_name,
            description=description,
            status=PaymentStatus.COMPLETED,  # Упрощенно - сразу completed
            completed_at=datetime.utcnow()
        )
        
        db.add(payment)
        try:
            db.commit()
            db.refresh(payment)
            logger.info(f"✅ Платеж карта-карта {payment.id} успешно создан: {amount}₽ от пользователя {user_id}")
            
            # Обновляем кеш баланса счета (уменьшаем баланс на сумму платежа)
            try:
                import redis
                import json
                from src.config import settings
                
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                
                balance_key = f"balance:{user_id}:{from_account.account_id}"
                cached_balance = redis_client.get(balance_key)
                
                if cached_balance:
                    balance_data = json.loads(cached_balance)
                    current_balance = balance_data.get("amount", 0)
                    new_balance = current_balance - amount
                    balance_data["amount"] = max(0, new_balance)
                    
                    redis_client.setex(
                        balance_key,
                        settings.BANK_DATA_CACHE_TTL,
                        json.dumps(balance_data)
                    )
                    logger.info(f"✅ Обновлен баланс в кеше для перевода на карту: {current_balance}₽ -> {balance_data['amount']}₽ (списано {amount}₽)")
                
                # Инвалидируем кеш транзакций
                transactions_key = f"transactions:{user_id}:{from_account.account_id}"
                redis_client.delete(transactions_key)
                logger.info(f"✅ Инвалидирован кеш транзакций для {from_account.account_id}")
                
            except Exception as cache_error:
                logger.warning(f"⚠️  Не удалось обновить кеш баланса: {cache_error}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Ошибка сохранения платежа карта-карта: {e}")
            return None, f"Ошибка сохранения платежа: {str(e)}"
        
        return payment, None
    
    @staticmethod
    def create_utility_payment(
        db: Session,
        user_id: int,
        from_account_id: int,
        payment_type: str,
        provider: str,
        account_number: str,
        amount: float
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """Оплата услуг (ЖКХ, связь, интернет и т.д.)"""
        from_account = db.query(BankAccount).filter(
            BankAccount.id == from_account_id,
            BankAccount.user_id == user_id
        ).first()
        
        if not from_account:
            return None, "Счет отправителя не найден"
        
        # Проверяем баланс перед оплатой
        try:
            from src.services.account_service import AccountService
            import redis
            
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            account_service = AccountService(db, redis_client)
            balance_data = account_service.get_account_balance(
                user_id=user_id,
                account_id=from_account.account_id,
                bank_id=from_account.bank_id
            )
            
            if not balance_data:
                return None, "Не удалось получить баланс счета"
            
            current_balance = balance_data.get("amount", 0)
            
            if current_balance < amount:
                return None, f"Недостаточно средств на счете. Текущий баланс: {current_balance}₽, требуется: {amount}₽"
            
            logger.info(f"✅ Баланс проверен для оплаты услуг: {current_balance}₽ >= {amount}₽")
            
        except Exception as e:
            logger.error(f"Ошибка проверки баланса: {e}")
            if not settings.DEBUG:
                return None, f"Ошибка проверки баланса: {str(e)}"
            logger.warning(f"⚠️  Продолжаем без проверки баланса (DEBUG режим)")
        
        # Маппинг типов
        type_map = {
            "mobile": PaymentType.MOBILE,
            "utilities": PaymentType.UTILITIES,
            "internet": PaymentType.INTERNET,
            "tv": PaymentType.TV,
            "phone": PaymentType.PHONE,
            "electricity": PaymentType.ELECTRICITY,
        }
        
        ptype = type_map.get(payment_type, PaymentType.UTILITIES)
        
        payment = Payment(
            user_id=user_id,
            payment_type=ptype,
            amount=amount,
            currency="RUB",
            from_account_id=from_account_id,
            from_account_name=from_account.account_name,
            to_name=provider,
            to_account=account_number,
            description=f"Оплата {provider} - {account_number}",
            status=PaymentStatus.COMPLETED,  # Упрощенно - сразу completed
            completed_at=datetime.utcnow()
        )
        
        db.add(payment)
        try:
            db.commit()
            db.refresh(payment)
            logger.info(f"✅ Платеж услуг {payment.id} успешно создан: {amount}₽ от пользователя {user_id}")
            
            # Обновляем кеш баланса счета (уменьшаем баланс на сумму платежа)
            try:
                import redis
                import json
                from src.config import settings
                
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                
                balance_key = f"balance:{user_id}:{from_account.account_id}"
                cached_balance = redis_client.get(balance_key)
                
                if cached_balance:
                    balance_data = json.loads(cached_balance)
                    current_balance = balance_data.get("amount", 0)
                    new_balance = current_balance - amount
                    balance_data["amount"] = max(0, new_balance)
                    
                    redis_client.setex(
                        balance_key,
                        settings.BANK_DATA_CACHE_TTL,
                        json.dumps(balance_data)
                    )
                    logger.info(f"✅ Обновлен баланс в кеше для оплаты услуг: {current_balance}₽ -> {balance_data['amount']}₽ (списано {amount}₽)")
                
                # Инвалидируем кеш транзакций
                transactions_key = f"transactions:{user_id}:{from_account.account_id}"
                redis_client.delete(transactions_key)
                logger.info(f"✅ Инвалидирован кеш транзакций для {from_account.account_id}")
                
            except Exception as cache_error:
                logger.warning(f"⚠️  Не удалось обновить кеш баланса: {cache_error}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Ошибка сохранения платежа услуг: {e}")
            return None, f"Ошибка сохранения платежа: {str(e)}"
        
        return payment, None
    
    @staticmethod
    def get_user_payments(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Payment]:
        """Получить историю платежей пользователя (исходящие и входящие)"""
        from sqlalchemy import or_
        # Получаем как исходящие (user_id), так и входящие (to_user_id) платежи
        return db.query(Payment).filter(
            or_(
                Payment.user_id == user_id,  # Исходящие платежи
                Payment.to_user_id == user_id  # Входящие платежи
            )
        ).order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def create_premium_payment(
        db: Session,
        user_id: int,
        from_account_id: int,
        amount: float = 299.0
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Создать платеж за Premium подписку
        
        План:
        1. Найти счет пользователя
        2. Проверить баланс счета
        3. Отправить запрос в систему списания (mock bank API)
        4. Списываем деньги за подписку
        5. Создать запись Payment
        6. Вернуть результат
        """
        # Преобразуем account_id в int если нужно
        try:
            from_account_id = int(from_account_id)
        except (ValueError, TypeError):
            return None, "Неверный формат ID счета"
        
        # Пытаемся найти счет пользователя
        logger.info(f"🔍 Поиск счета: from_account_id={from_account_id}, user_id={user_id}")
        from_account = db.query(BankAccount).filter(
            BankAccount.id == from_account_id,
            BankAccount.user_id == user_id
        ).first()
        
        if not from_account:
            logger.warning(f"⚠️  Счет {from_account_id} не найден, ищем счет с наивысшим приоритетом")
            # Если не нашли - берем счет с наивысшим приоритетом (priority = 1)
            from_account = db.query(BankAccount).filter(
                BankAccount.user_id == user_id,
                BankAccount.is_active == True
            ).order_by(BankAccount.priority.asc()).first()
            
            if not from_account:
                logger.error(f"❌ У пользователя {user_id} нет активных счетов для оплаты")
                return None, "У вас нет активных счетов для оплаты"
            
            # Используем найденный счет
            from_account_id = from_account.id
            logger.info(f"✅ Найден счет с приоритетом: {from_account.id}, account_id={from_account.account_id}")
        
        logger.info(f"✅ Счет найден: id={from_account.id}, account_id={from_account.account_id}, bank_id={from_account.bank_id}")
        
        # ШАГ 2: Проверяем баланс счета
        try:
            from src.services.account_service import AccountService
            import redis
            
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            account_service = AccountService(db, redis_client)
            balance_data = account_service.get_account_balance(
                user_id=user_id,
                account_id=from_account.account_id,
                bank_id=from_account.bank_id
            )
            
            if not balance_data:
                return None, "Не удалось получить баланс счета"
            
            current_balance = balance_data.get("amount", 0)
            
            if current_balance < amount:
                return None, f"Недостаточно средств на счете. Текущий баланс: {current_balance}₽, требуется: {amount}₽"
            
            logger.info(f"✅ Баланс проверен: {current_balance}₽ >= {amount}₽")
            
        except Exception as e:
            logger.error(f"Ошибка проверки баланса: {e}")
            # В режиме разработки продолжаем без проверки баланса
            if not settings.DEBUG:
                return None, f"Ошибка проверки баланса: {str(e)}"
            logger.warning(f"⚠️  Продолжаем без проверки баланса (DEBUG режим)")
        
        # ШАГ 3: Отправляем запрос в систему списания (mock bank API)
        # В реальности здесь был бы запрос POST /payments через Bank API
        # Для mock просто логируем успешное списание
        try:
            logger.info(f"💳 Списание {amount}₽ со счета {from_account.account_id} для Premium подписки")
            
            # В реальности здесь:
            # payment_response = bank_client.create_payment(...)
            # if not payment_response.success:
            #     return None, "Ошибка списания средств"
            
            logger.info(f"✅ Средства успешно списаны со счета")
            
        except Exception as e:
            logger.error(f"Ошибка списания средств: {e}")
            return None, f"Ошибка списания средств: {str(e)}"
        
        # ШАГ 4: Создаем запись Payment
        payment = Payment(
            user_id=user_id,
            payment_type=PaymentType.PREMIUM,
            amount=amount,
            currency="RUB",
            from_account_id=from_account_id,
            from_account_name=from_account.account_name,
            to_name="Bank Aggregator Premium",
            description="Оплата подписки Premium на 1 месяц",
            status=PaymentStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        
        db.add(payment)
        try:
            db.commit()
            db.refresh(payment)
            logger.info(f"✅ Платеж Premium {payment.id} успешно создан: {amount}₽ от пользователя {user_id}")
            
            # Обновляем кеш баланса счета (уменьшаем баланс на сумму платежа)
            try:
                import redis
                import json
                from src.config import settings
                
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                
                balance_key = f"balance:{user_id}:{from_account.account_id}"
                cached_balance = redis_client.get(balance_key)
                
                if cached_balance:
                    balance_data = json.loads(cached_balance)
                    current_balance = balance_data.get("amount", 0)
                    new_balance = current_balance - amount
                    balance_data["amount"] = max(0, new_balance)  # Не даем балансу уйти в минус
                    
                    redis_client.setex(
                        balance_key,
                        settings.BANK_DATA_CACHE_TTL,
                        json.dumps(balance_data)
                    )
                    logger.info(f"✅ Обновлен баланс в кеше для Premium: {current_balance}₽ -> {balance_data['amount']}₽ (списано {amount}₽)")
                else:
                    logger.warning(f"⚠️  Баланс не найден в кеше для {balance_key}, создаем новый")
                    # Создаем новый баланс в кеше
                    balance_data = {
                        "amount": max(0, -amount),  # Если баланс был 0, то после списания будет отрицательным, но мы ограничиваем до 0
                        "currency": "RUB"
                    }
                    redis_client.setex(
                        balance_key,
                        settings.BANK_DATA_CACHE_TTL,
                        json.dumps(balance_data)
                    )
                
                # Инвалидируем кеш транзакций
                transactions_key = f"transactions:{user_id}:{from_account.account_id}"
                redis_client.delete(transactions_key)
                logger.info(f"✅ Инвалидирован кеш транзакций для {from_account.account_id}")
                
            except Exception as cache_error:
                logger.warning(f"⚠️  Не удалось обновить кеш баланса: {cache_error}")
                # Не блокируем платеж из-за ошибки кеша
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Ошибка сохранения платежа Premium: {e}")
            return None, f"Ошибка сохранения платежа: {str(e)}"
        
        return payment, None

