from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from src.database import Base

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def is_expired(self) -> bool:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            expires_aware = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_aware = self.expires_at
        return now > expires_aware

    def is_valid(self, code: str) -> bool:
        return (
            self.code == code and
            not self.is_used and
            not self.is_expired()
        )

    @staticmethod
    def create_expiry_time() -> datetime:
        from datetime import timezone
        return datetime.now(timezone.utc) + timedelta(minutes=10)

    def __repr__(self):
        return f"<OTPCode(email={self.email}, expired={self.is_expired()})>"
