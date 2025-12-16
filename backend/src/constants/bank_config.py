from typing import Dict

BANK_URLS = {
    1: "https://vbank.open.bankingapi.ru",
    2: "https://sbank.open.bankingapi.ru",
    3: "https://abank.open.bankingapi.ru",
}

BANK_NAMES = {
    1: "vbank",
    2: "sbank",
    3: "abank"
}

BANK_NAME_TO_ID = {
    "vbank": 1,
    "sbank": 2,
    "abank": 3
}

def get_bank_url(bank_id: int) -> str:
    return BANK_URLS.get(bank_id, BANK_URLS[1])

def get_bank_name(bank_id: int) -> str:
    return BANK_NAMES.get(bank_id, "vbank")
