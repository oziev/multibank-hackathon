import logging
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from src.models.invitation import Invitation
from src.models.user import User
from src.models.group import GroupMember
from src.constants.constants import InvitationStatus

logger = logging.getLogger(__name__)

class InvitationService:

    @staticmethod
    def get_user_invitations(db: Session, user_email: str):
        invitations = (
            db.query(Invitation)
            .filter(Invitation.invitee_email == user_email)
            .order_by(Invitation.created_at.desc())
            .all()
        )

        return invitations

    @staticmethod
    def create_invitation(
        db: Session,
        group_id: int,
        inviter_id: int,
        invitee_email: str
    ) -> Tuple[Optional[Invitation], Optional[str]]:
        invitee = db.query(User).filter(User.email == invitee_email).first()
        if not invitee:
            return None, "Пользователь с таким email не найден"

        existing_member = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == invitee.id)
            .first()
        )
        if existing_member:
            return None, "Пользователь уже является членом группы"

        existing_invitation = (
            db.query(Invitation)
            .filter(
                Invitation.group_id == group_id,
                Invitation.invitee_email == invitee_email,
                Invitation.status == InvitationStatus.PENDING
            )
            .first()
        )
        if existing_invitation:
            return None, "Приглашение уже отправлено"

        invitation = Invitation(
            group_id=group_id,
            inviter_id=inviter_id,
            invitee_email=invitee_email,
            status=InvitationStatus.PENDING
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        logger.info(f"Создано приглашение {invitation.id} в группу {group_id}")
        return invitation, None

    @staticmethod
    def accept_invitation(
        db: Session,
        invitation_id: int,
        user_email: str
    ) -> Tuple[bool, Optional[str]]:
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()

        if not invitation:
            return False, "Приглашение не найдено"

        if invitation.invitee_email != user_email:
            return False, "Это приглашение не для вас"

        if invitation.status != InvitationStatus.PENDING:
            return False, "Приглашение уже обработано"

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return False, "Пользователь не найден"

        invitation.status = InvitationStatus.ACCEPTED

        member = GroupMember(group_id=invitation.group_id, user_id=user.id)
        db.add(member)

        db.commit()

        logger.info(f"Приглашение {invitation_id} принято пользователем {user.id}")
        return True, None

    @staticmethod
    def decline_invitation(
        db: Session,
        invitation_id: int,
        user_email: str
    ) -> Tuple[bool, Optional[str]]:
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()

        if not invitation:
            return False, "Приглашение не найдено"

        if invitation.invitee_email != user_email:
            return False, "Это приглашение не для вас"

        if invitation.status != InvitationStatus.PENDING:
            return False, "Приглашение уже обработано"

        invitation.status = InvitationStatus.DECLINED
        db.commit()

        logger.info(f"Приглашение {invitation_id} отклонено")
        return True, None
