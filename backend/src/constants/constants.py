from enum import Enum

class AccountType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"

class BankId(int, Enum):
    VBANK = 1
    SBANK = 2
    ABANK = 3

class BankName(str, Enum):
    VBANK = "vbank"
    SBANK = "sbank"
    ABANK = "abank"

class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class GroupRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    CHILD = "child"

class TransactionCategory(str, Enum):
    GROCERIES = "groceries"
    RESTAURANTS = "restaurants"
    TRANSPORT = "transport"
    CLOTHING = "clothing"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    SPORTS = "sports"
    BEAUTY = "beauty"
    UTILITIES = "utilities"
    EDUCATION = "education"
    CHILDREN = "children"
    HOME = "home"
    TRANSFERS = "transfers"
    OTHER = "other"

class ConsentType(str, Enum):
    ACCOUNTS = "accounts"
    BALANCES = "balances"
    TRANSACTIONS = "transactions"

ACCOUNT_LIMITS = {
    "free": {
        "maxGroups": 1,
        "maxMembers": 2
    },
    "premium": {
        "maxGroups": 5,
        "maxMembers": 20
    },
    AccountType.FREE: {
        "max_groups": 1,
        "max_members": 2
    },
    AccountType.PREMIUM: {
        "max_groups": 5,
        "max_members": 20
    }
}

BANK_ID_TO_NAME = {
    BankId.VBANK: BankName.VBANK,
    BankId.SBANK: BankName.SBANK,
    BankId.ABANK: BankName.ABANK,
}

BANK_NAME_TO_ID = {
    BankName.VBANK: BankId.VBANK,
    BankName.SBANK: BankId.SBANK,
    BankName.ABANK: BankId.ABANK,
}
