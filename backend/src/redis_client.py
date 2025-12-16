import redis
from typing import Optional
from src.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    decode_responses=True
)

def get_redis() -> redis.Redis:
    return redis_client

def set_with_expiry(key: str, value: str, expiry_seconds: int) -> bool:
    return redis_client.setex(key, expiry_seconds, value)

def get_value(key: str) -> Optional[str]:
    return redis_client.get(key)

def delete_key(key: str) -> bool:
    return redis_client.delete(key) > 0
