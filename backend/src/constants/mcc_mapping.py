from typing import Dict
from src.constants.constants import TransactionCategory

MCC_TO_CATEGORY: Dict[str, TransactionCategory] = {
    "5411": TransactionCategory.GROCERIES,
    "5412": TransactionCategory.GROCERIES,
    "5422": TransactionCategory.GROCERIES,
    "5441": TransactionCategory.GROCERIES,
    "5451": TransactionCategory.GROCERIES,
    "5462": TransactionCategory.GROCERIES,
    "5499": TransactionCategory.GROCERIES,
    
    "5812": TransactionCategory.RESTAURANTS,
    "5813": TransactionCategory.RESTAURANTS,
    "5814": TransactionCategory.RESTAURANTS,
    
    "4121": TransactionCategory.TRANSPORT,
    "4131": TransactionCategory.TRANSPORT,
    "4784": TransactionCategory.TRANSPORT,
    "5541": TransactionCategory.TRANSPORT,
    "5542": TransactionCategory.TRANSPORT,
    "5551": TransactionCategory.TRANSPORT,
    "5561": TransactionCategory.TRANSPORT,
    "5571": TransactionCategory.TRANSPORT,
    "5599": TransactionCategory.TRANSPORT,
    
    "5611": TransactionCategory.CLOTHING,
    "5621": TransactionCategory.CLOTHING,
    "5631": TransactionCategory.CLOTHING,
    "5641": TransactionCategory.CLOTHING,
    "5651": TransactionCategory.CLOTHING,
    "5655": TransactionCategory.CLOTHING,
    "5661": TransactionCategory.CLOTHING,
    "5681": TransactionCategory.CLOTHING,
    "5691": TransactionCategory.CLOTHING,
    "5697": TransactionCategory.CLOTHING,
    "5698": TransactionCategory.CLOTHING,
    "5699": TransactionCategory.CLOTHING,
    
    "5912": TransactionCategory.HEALTH,
    "5975": TransactionCategory.HEALTH,
    "5976": TransactionCategory.HEALTH,
    "8011": TransactionCategory.HEALTH,
    "8021": TransactionCategory.HEALTH,
    "8031": TransactionCategory.HEALTH,
    "8041": TransactionCategory.HEALTH,
    "8042": TransactionCategory.HEALTH,
    "8043": TransactionCategory.HEALTH,
    "8049": TransactionCategory.HEALTH,
    "8050": TransactionCategory.HEALTH,
    "8062": TransactionCategory.HEALTH,
    "8071": TransactionCategory.HEALTH,
    
    "7832": TransactionCategory.ENTERTAINMENT,
    "7841": TransactionCategory.ENTERTAINMENT,
    "7922": TransactionCategory.ENTERTAINMENT,
    "7929": TransactionCategory.ENTERTAINMENT,
    "7932": TransactionCategory.ENTERTAINMENT,
    "7933": TransactionCategory.ENTERTAINMENT,
    "7991": TransactionCategory.ENTERTAINMENT,
    "7992": TransactionCategory.ENTERTAINMENT,
    "7993": TransactionCategory.ENTERTAINMENT,
    "7994": TransactionCategory.ENTERTAINMENT,
    "7995": TransactionCategory.ENTERTAINMENT,
    "7996": TransactionCategory.ENTERTAINMENT,
    "7999": TransactionCategory.ENTERTAINMENT,
    
    "3000": TransactionCategory.TRAVEL,
    "3001": TransactionCategory.TRAVEL,
    "3002": TransactionCategory.TRAVEL,
    "3003": TransactionCategory.TRAVEL,
    "3004": TransactionCategory.TRAVEL,
    "3005": TransactionCategory.TRAVEL,
    "3006": TransactionCategory.TRAVEL,
    "3007": TransactionCategory.TRAVEL,
    "3008": TransactionCategory.TRAVEL,
    "3009": TransactionCategory.TRAVEL,
    "3010": TransactionCategory.TRAVEL,
    "3011": TransactionCategory.TRAVEL,
    "4511": TransactionCategory.TRAVEL,
    "4722": TransactionCategory.TRAVEL,
    "7011": TransactionCategory.TRAVEL,
    "7012": TransactionCategory.TRAVEL,
    
    "5941": TransactionCategory.SPORTS,
    "5942": TransactionCategory.SPORTS,
    "5996": TransactionCategory.SPORTS,
    "7941": TransactionCategory.SPORTS,
    "7997": TransactionCategory.SPORTS,
    "7998": TransactionCategory.SPORTS,
    
    "5977": TransactionCategory.BEAUTY,
    "7230": TransactionCategory.BEAUTY,
    "7297": TransactionCategory.BEAUTY,
    "7298": TransactionCategory.BEAUTY,
    
    "4814": TransactionCategory.UTILITIES,
    "4899": TransactionCategory.UTILITIES,
    "4900": TransactionCategory.UTILITIES,
    
    "5942": TransactionCategory.CHILDREN,
    "5943": TransactionCategory.CHILDREN,
    "5944": TransactionCategory.CHILDREN,
    "5945": TransactionCategory.CHILDREN,
    
    "5200": TransactionCategory.HOME,
    "5211": TransactionCategory.HOME,
    "5231": TransactionCategory.HOME,
    "5251": TransactionCategory.HOME,
    "5261": TransactionCategory.HOME,
    "5712": TransactionCategory.HOME,
    "5713": TransactionCategory.HOME,
    "5714": TransactionCategory.HOME,
    "5718": TransactionCategory.HOME,
    
    "8211": TransactionCategory.EDUCATION,
    "8220": TransactionCategory.EDUCATION,
    "8241": TransactionCategory.EDUCATION,
    "8244": TransactionCategory.EDUCATION,
    "8249": TransactionCategory.EDUCATION,
    "8299": TransactionCategory.EDUCATION,
}

def categorize_transaction(mcc_code: str, description: str = "") -> TransactionCategory:
    """
    Категоризация транзакции на основе MCC кода.
    Если MCC не найден, пытаемся определить по описанию.
    """
    if mcc_code and mcc_code in MCC_TO_CATEGORY:
        return MCC_TO_CATEGORY[mcc_code]
    
    description_lower = description.lower()
    
    keywords_map = {
        TransactionCategory.GROCERIES: ["магазин", "магнит", "пятёрочка", "перекрёсток", "ашан", "лента", "дикси"],
        TransactionCategory.RESTAURANTS: ["ресторан", "кафе", "макдональдс", "kfc", "бургер", "пицца", "суши", "якитория", "starbucks"],
        TransactionCategory.TRANSPORT: ["метро", "такси", "uber", "яндекс.такси", "бензин", "азс", "парковка", "транспорт"],
        TransactionCategory.UTILITIES: ["жкх", "электричество", "газ", "вода", "интернет", "мобильная связь", "связь"],
        TransactionCategory.TRANSFERS: ["перевод", "transfer", "п2п", "p2p"],
    }
    
    for category, keywords in keywords_map.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    return TransactionCategory.OTHER

CATEGORY_NAMES_RU = {
    TransactionCategory.GROCERIES: "Продукты и супермаркеты",
    TransactionCategory.RESTAURANTS: "Рестораны и кафе",
    TransactionCategory.TRANSPORT: "Транспорт",
    TransactionCategory.CLOTHING: "Одежда и обувь",
    TransactionCategory.HEALTH: "Здоровье и аптеки",
    TransactionCategory.ENTERTAINMENT: "Развлечения",
    TransactionCategory.TRAVEL: "Путешествия и отели",
    TransactionCategory.SPORTS: "Спорт и фитнес",
    TransactionCategory.BEAUTY: "Красота и уход",
    TransactionCategory.UTILITIES: "ЖКХ и связь",
    TransactionCategory.EDUCATION: "Образование",
    TransactionCategory.CHILDREN: "Дети",
    TransactionCategory.HOME: "Дом и ремонт",
    TransactionCategory.TRANSFERS: "Переводы",
    TransactionCategory.OTHER: "Прочее",
}

