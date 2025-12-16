import secrets
import logging
from typing import Optional
import redis

from src.config import settings

logger = logging.getLogger(__name__)

class SessionService:

    @staticmethod
    def create_session(redis_client: redis.Redis, user_id: int) -> str:
        session_id = secrets.token_urlsafe(32)
        session_key = f"session:{session_id}"

        ttl = settings.SESSION_EXPIRE_HOURS * 3600
        redis_client.setex(session_key, ttl, str(user_id))

        logger.info(f"Создана сессия для пользователя {user_id}")
        return session_id

    @staticmethod
    def get_user_id(redis_client: redis.Redis, session_id: str) -> Optional[int]:
        session_key = f"session:{session_id}"
        user_id_str = redis_client.get(session_key)

        if user_id_str:
            return int(user_id_str)
        return None

    @staticmethod
    def delete_session(redis_client: redis.Redis, session_id: str) -> bool:
        session_key = f"session:{session_id}"
        result = redis_client.delete(session_key)

        if result:
            logger.info(f"Сессия удалена: {session_id[:10]}...")
        return result > 0
