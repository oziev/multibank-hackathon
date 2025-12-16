import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any

from src.models.group import Group, GroupMember
from src.models.user import User
from src.models.account import BankAccount
from src.constants.constants import AccountType, ACCOUNT_LIMITS, GroupRole

logger = logging.getLogger(__name__)

class GroupService:

    @staticmethod
    def create_group(
        db: Session,
        name: str,
        owner_id: int,
        account_type: AccountType
    ) -> Tuple[Optional[Group], Optional[str]]:
        existing_groups_count = db.query(Group).filter(Group.owner_id == owner_id).count()
        max_groups = ACCOUNT_LIMITS[account_type]["max_groups"]

        if existing_groups_count >= max_groups:
            return None, f"Достигнут лимит групп ({max_groups}) для вашего типа аккаунта"

        group = Group(name=name, owner_id=owner_id)
        db.add(group)
        db.flush()

        member = GroupMember(group_id=group.id, user_id=owner_id, role=GroupRole.OWNER)
        db.add(member)

        db.commit()
        db.refresh(group)

        logger.info(f"Создана группа {group.id} для пользователя {owner_id}")
        return group, None

    @staticmethod
    def get_user_groups(db: Session, user_id: int) -> List[Group]:
        memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
        group_ids = [m.group_id for m in memberships]

        groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
        return groups

    @staticmethod
    def delete_group(
        db: Session,
        group_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        from src.models.invitation import Invitation
        
        group = db.query(Group).filter(Group.id == group_id).first()

        if not group:
            return False, "Группа не найдена"

        if group.owner_id != user_id:
            return False, "Только владелец может удалить группу"

        db.query(Invitation).filter(Invitation.group_id == group_id).delete()
        db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()

        db.delete(group)
        db.commit()

        logger.info(f"Группа {group_id} удалена пользователем {user_id}")
        return True, None

    @staticmethod
    def exit_group(
        db: Session,
        group_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        group = db.query(Group).filter(Group.id == group_id).first()

        if not group:
            return False, "Группа не найдена"

        if group.owner_id == user_id:
            return False, "Владелец не может выйти из группы. Удалите группу."

        membership = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )

        if not membership:
            return False, "Вы не являетесь членом этой группы"

        db.delete(membership)
        db.commit()

        logger.info(f"Пользователь {user_id} вышел из группы {group_id}")
        return True, None

    @staticmethod
    def get_group_members(db: Session, group_id: int) -> List[User]:
        memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
        user_ids = [m.user_id for m in memberships]

        users = db.query(User).filter(User.id.in_(user_ids)).all()
        return users

    @staticmethod
    def add_member(
        db: Session,
        group_id: int,
        user_email: str,
        account_type: AccountType
    ) -> Tuple[bool, Optional[str]]:
        current_members = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
        max_members = ACCOUNT_LIMITS[account_type]["max_members"]

        if current_members >= max_members:
            return False, f"Достигнут лимит членов группы ({max_members})"

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return False, "Пользователь с таким email не найден"

        existing = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user.id)
            .first()
        )

        if existing:
            return False, "Пользователь уже является членом группы"

        member = GroupMember(group_id=group_id, user_id=user.id, role=GroupRole.MEMBER)
        db.add(member)
        db.commit()

        logger.info(f"Пользователь {user.id} добавлен в группу {group_id}")
        return True, None

    @staticmethod
    def get_group_accounts(db: Session, group_id: int) -> List[Dict[str, Any]]:
        members = GroupService.get_group_members(db, group_id)

        result = []
        for member in members:
            accounts = db.query(BankAccount).filter(BankAccount.user_id == member.id).all()

            for acc in accounts:
                result.append({
                    "owner": {
                        "name": member.name
                    },
                    "clientId": str(acc.bank_id),
                    "clientName": GroupService._get_bank_name(acc.bank_id),
                    "accountId": acc.account_id,
                    "accountName": acc.account_name
                })

        return result

    @staticmethod
    def can_add_member(
        db: Session,
        group_id: int,
        account_type: AccountType
    ) -> Tuple[bool, Optional[str]]:
        current_members = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
        max_members = ACCOUNT_LIMITS[account_type]["max_members"]

        if current_members >= max_members:
            return False, f"Достигнут лимит членов группы ({max_members})"

        return True, None

    @staticmethod
    def is_user_member(db: Session, group_id: int, user_id: int) -> bool:
        membership = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )
        return membership is not None

    @staticmethod
    def is_user_owner(db: Session, group_id: int, user_id: int) -> bool:
        group = db.query(Group).filter(Group.id == group_id).first()
        return group and group.owner_id == user_id

    @staticmethod
    def _get_bank_name(bank_id: int) -> str:
        bank_names = {1: "vbank", 2: "sbank", 3: "abank"}
        return bank_names.get(bank_id, f"bank{bank_id}")
    
    @staticmethod
    def get_member_role(db: Session, group_id: int, user_id: int) -> Optional[GroupRole]:
        """
        Получить роль пользователя в группе
        """
        membership = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )
        return membership.role if membership else None
    
    @staticmethod
    def update_member_role(
        db: Session,
        group_id: int,
        target_user_id: int,
        new_role: GroupRole,
        requester_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Обновить роль участника группы
        """
        requester_role = GroupService.get_member_role(db, group_id, requester_user_id)
        
        if requester_role != GroupRole.OWNER and requester_role != GroupRole.ADMIN:
            return False, "Недостаточно прав для изменения ролей"
        
        if requester_role == GroupRole.ADMIN and new_role in [GroupRole.OWNER, GroupRole.ADMIN]:
            return False, "Администратор не может назначать владельцев и администраторов"
        
        membership = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == target_user_id)
            .first()
        )
        
        if not membership:
            return False, "Пользователь не является членом группы"
        
        if membership.role == GroupRole.OWNER:
            return False, "Нельзя изменить роль владельца"
        
        membership.role = new_role
        db.commit()
        
        logger.info(f"Роль пользователя {target_user_id} в группе {group_id} изменена на {new_role}")
        return True, None
