from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
from src.constants.constants import InvitationStatus

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_email = Column(String(255), nullable=False, index=True)
    status = Column(
        Enum(InvitationStatus),
        default=InvitationStatus.PENDING,
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="sent_invitations")

    def __repr__(self):
        return f"<Invitation(id={self.id}, group_id={self.group_id}, status={self.status})>"
