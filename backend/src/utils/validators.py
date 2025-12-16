import re
from datetime import datetime, date
from typing import Optional

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"

    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"

    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"

    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру"

    return True, None

def validate_age(birth_date: date) -> bool:
    today = datetime.now().date()
    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age >= 18
