import logging
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from typing import Optional

from src.models.otp_code import OTPCode
from src.config import settings

logger = logging.getLogger(__name__)

class OTPService:

    @staticmethod
    def generate_otp_code(db: Session, email: str) -> str:
        # Генерируем случайный код для отправки на почту
        code = str(random.randint(100000, 999999))

        otp = OTPCode(
            email=email,
            code=code,
            expires_at=OTPCode.create_expiry_time()
        )

        db.add(otp)
        db.commit()

        logger.info(f"Создан OTP код для {email}: {code}")
        return code

    @staticmethod
    def verify_otp(db: Session, email: str, code: str) -> tuple[bool, Optional[str]]:
        # Ищем последний неиспользованный код для этого email
        otp = (
            db.query(OTPCode)
            .filter(OTPCode.email == email, OTPCode.is_used == False)
            .order_by(OTPCode.created_at.desc())
            .first()
        )

        if not otp:
            # Проверяем, может быть код уже использован или истек
            last_otp = (
                db.query(OTPCode)
                .filter(OTPCode.email == email)
                .order_by(OTPCode.created_at.desc())
                .first()
            )
            if last_otp and last_otp.is_used:
                return False, "Код уже использован. Запросите новый код"
            if last_otp and last_otp.is_expired():
                return False, "Код истёк. Запросите новый код"
            return False, "OTP код не найден. Запросите новый код"

        if not otp.is_valid(code):
            if otp.is_expired():
                return False, "OTP код истёк. Запросите новый код"
            return False, "Неверный OTP код"

        otp.is_used = True
        db.commit()

        logger.info(f"OTP код успешно проверен для {email}")
        return True, None

    @staticmethod
    def send_otp_email(email: str, code: str):
        """
        Отправка OTP кода на email
        """
        logger.info(f"📧 Отправка OTP на {email}")
        
        if not settings.SMTP_ENABLED or not settings.SMTP_USERNAME:
            logger.info(f"💡 SMTP отключен. OTP код для {email}: {code}")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Ваш код подтверждения: {code}"
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #9333ea; text-align: center; padding: 20px; background-color: #f3f4f6; border-radius: 8px; letter-spacing: 8px; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Подтверждение email</h2>
        <p>Добро пожаловать в Bank Aggregator!</p>
        <p>Ваш код подтверждения:</p>
        <div class="code">{code}</div>
        <p>Код действителен в течение {settings.OTP_EXPIRE_MINUTES} минут.</p>
        <p>Если вы не регистрировались в нашем сервисе, просто проигнорируйте это письмо.</p>
        <div class="footer">
            <p>© 2025 Bank Aggregator. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""
            
            text_body = f"""
Добро пожаловать в Bank Aggregator!

Ваш код подтверждения: {code}

Код действителен в течение {settings.OTP_EXPIRE_MINUTES} минут.

Если вы не регистрировались в нашем сервисе, просто проигнорируйте это письмо.

---
© 2025 Bank Aggregator
"""
            
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ OTP код отправлен на {email}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            logger.info(f"📧 Резервный вывод - OTP код для {email}: {code}")
    
    @staticmethod
    def send_password_reset_email(email: str, code: str):
        """
        Отправка OTP кода для сброса пароля
        """
        if not settings.SMTP_ENABLED or not settings.SMTP_USERNAME:
            logger.info(f"📧 OTP код для сброса пароля {email}: {code}")
            logger.info(f"💡 SMTP отключен - используйте этот код для сброса пароля")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Сброс пароля: {code}"
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #dc2626; text-align: center; padding: 20px; background-color: #fee2e2; border-radius: 8px; letter-spacing: 8px; }}
        .warning {{ background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🔒 Сброс пароля</h2>
        <p>Вы запросили сброс пароля для вашего аккаунта в Bank Aggregator.</p>
        <p>Ваш код подтверждения:</p>
        <div class="code">{code}</div>
        <p>Код действителен в течение {settings.OTP_EXPIRE_MINUTES} минут.</p>
        <div class="warning">
            <strong>⚠️ Внимание!</strong>
            <p>Если вы НЕ запрашивали сброс пароля, немедленно проигнорируйте это письмо и обратитесь в поддержку.</p>
        </div>
        <div class="footer">
            <p>© 2025 Bank Aggregator. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""
            
            text_body = f"""
🔒 Сброс пароля

Вы запросили сброс пароля для вашего аккаунта в Bank Aggregator.

Ваш код подтверждения: {code}

Код действителен в течение {settings.OTP_EXPIRE_MINUTES} минут.

⚠️ ВНИМАНИЕ!
Если вы НЕ запрашивали сброс пароля, немедленно проигнорируйте это письмо и обратитесь в поддержку.

---
© 2025 Bank Aggregator
"""
            
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Код для сброса пароля отправлен на {email}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            logger.info(f"📧 Резервный вывод - OTP код для сброса пароля {email}: {code}")
