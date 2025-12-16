import logging
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
import redis

from src.database import get_db
from src.redis_client import get_redis
from src.dependencies import get_current_verified_user
from src.schemas.group import (
    GroupCreateRequest,
    GroupResponse,
    GroupSettingsResponse,
    InviteRequest,
    InviteActionRequest,
    GroupDeleteRequest,
    GroupExitRequest
)
from src.schemas.profile import RoleUpdateRequest
from src.constants.constants import GroupRole
from src.models.user import User
from src.models.group import GroupMember
from src.services.group_service import GroupService
from src.services.invitation_service import InvitationService
from src.services.account_service import AccountService
from src.utils.responses import success_response, error_response
from src.constants.constants import ACCOUNT_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["Groups"])

@router.post("")
async def create_group(
    request: GroupCreateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    group, error = GroupService.create_group(
        db,
        request.name,
        current_user.id,
        current_user.account_type
    )

    if error:
        return error_response(error, 400)

    return success_response({
        "id": group.id,
        "name": group.name,
        "ownerId": group.owner_id,
        "createdAt": str(group.created_at)
    }, 201)

@router.get("")
async def get_groups(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    groups = GroupService.get_user_groups(db, current_user.id)

    result = []
    for group in groups:
        result.append({
            "id": group.id,
            "name": group.name,
            "ownerId": group.owner_id,
            "createdAt": str(group.created_at)
        })

    return success_response(result)

@router.get("/settings")
async def get_group_settings():
    settings_data = {
        "free": {
            "maxGroups": 1,
            "maxMembers": 2
        },
        "premium": {
            "maxGroups": 5,
            "maxMembers": 20
        }
    }

    return success_response(settings_data)

@router.delete("")
async def delete_group(
    request: GroupDeleteRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    success, error = GroupService.delete_group(db, request.group_id, current_user.id)

    if not success:
        return error_response(error, 400)

    return success_response({
        "message": "Группа успешно удалена"
    })

@router.post("/exit")
async def exit_group(
    request: GroupExitRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    success, error = GroupService.exit_group(db, request.group_id, current_user.id)

    if not success:
        return error_response(error, 400)

    return success_response({
        "message": "Вы успешно вышли из группы"
    })

@router.get("/{group_id}/accounts")
async def get_group_accounts(
    group_id: int = Path(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)

    accounts = GroupService.get_group_accounts(db, group_id)

    return success_response(accounts)

@router.get("/{group_id}/accounts/balances")
async def get_group_balances(
    group_id: int = Path(...),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)

    members = GroupService.get_group_members(db, group_id)

    redis_client = get_redis()
    account_service = AccountService(db, redis_client)

    balances = []

    for member in members:
        member_accounts = account_service.get_user_accounts(member.id, client_id)

        for acc in member_accounts:
            try:
                balance = account_service.get_account_balance(
                    member.id,
                    acc["accountId"],
                    acc["clientId"]
                )

                balances.append({
                    "clientId": str(acc["clientId"]),
                    "name": acc["clientName"],
                    "accountName": acc["accountName"],
                    "owner": {"name": member.name},
                    "balance": balance
                })
            except Exception as e:
                logger.error(f"Ошибка получения баланса: {e}")
                continue

    return success_response(balances)

@router.get("/{group_id}/accounts/transactions")
async def get_group_transactions(
    group_id: int = Path(...),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)

    members = GroupService.get_group_members(db, group_id)

    redis_client = get_redis()
    account_service = AccountService(db, redis_client)

    all_transactions = []

    for member in members:
        member_accounts = account_service.get_user_accounts(member.id, client_id)

        for acc in member_accounts:
            try:
                transactions = account_service.get_account_transactions(
                    member.id,
                    acc["accountId"],
                    acc["clientId"]
                )

                for txn in transactions:
                    txn["owner"] = {"name": member.name}
                    txn["accountName"] = acc["accountName"]

                all_transactions.extend(transactions)
            except Exception as e:
                logger.error(f"Ошибка получения транзакций: {e}")
                continue

    all_transactions.sort(key=lambda x: x.get("date", ""), reverse=True)

    return success_response(all_transactions)

@router.get("/{group_id}/accounts/{client_id}")
async def get_group_account_details(
    group_id: int = Path(...),
    client_id: str = Path(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)

    accounts = GroupService.get_group_accounts(db, group_id)

    for account in accounts:
        if account["clientId"] == client_id:
            return success_response(account)

    return error_response("Счёт не найден", 404)

@router.get("/invites")
async def get_my_invitations(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    invitations = InvitationService.get_user_invitations(db, current_user.email)

    result = []
    for inv in invitations:
        result.append({
            "id": inv.id,
            "groupId": inv.group_id,
            "inviterEmail": inv.inviter.email if inv.inviter else None,
            "inviterName": inv.inviter.name if inv.inviter else None,
            "status": inv.status.value,
            "createdAt": str(inv.created_at)
        })

    return success_response(result)

@router.post("/invite")
async def invite_to_group(
    request: InviteRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, request.group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)

    can_add, error = GroupService.can_add_member(
        db,
        request.group_id,
        current_user.account_type
    )

    if not can_add:
        return error_response(error, 400)

    invitation, error = InvitationService.create_invitation(
        db,
        request.group_id,
        current_user.id,
        request.email
    )

    if error:
        return error_response(error, 400)

    return success_response({
        "message": "Приглашение успешно отправлено",
        "requestId": invitation.id
    }, 201)

@router.post("/invite/accept")
async def accept_invitation(
    request: InviteActionRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    success, error = InvitationService.accept_invitation(
        db,
        request.request_id,
        current_user.email
    )

    if not success:
        return error_response(error, 400)

    return success_response({
        "message": "Приглашение принято успешно"
    })

@router.post("/invite/decline")
async def decline_invitation(
    request: InviteActionRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    success, error = InvitationService.decline_invitation(
        db,
        request.request_id,
        current_user.email
    )

    if not success:
        return error_response(error, 400)

    return success_response({
        "message": "Приглашение отклонено"
    })

@router.put("/{group_id}/members/{user_id}/role")
async def update_member_role(
    group_id: int,
    user_id: int,
    request: RoleUpdateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    try:
        new_role = GroupRole(request.role)
    except ValueError:
        return error_response(f"Неверная роль. Доступны: owner, admin, member, child", 400)
    
    success, error = GroupService.update_member_role(
        db,
        group_id,
        user_id,
        new_role,
        current_user.id
    )
    
    if not success:
        return error_response(error, 400)
    
    return success_response({
        "message": "Роль успешно обновлена",
        "userId": user_id,
        "newRole": new_role.value
    })

@router.get("/{group_id}/members")
async def get_group_members_with_roles(
    group_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not GroupService.is_user_member(db, group_id, current_user.id):
        return error_response("Вы не являетесь членом этой группы", 403)
    
    memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    result = []
    for membership in memberships:
        user = membership.user
        result.append({
            "userId": user.id,
            "name": user.name,
            "email": user.email,
            "avatarUrl": user.avatar_url,
            "role": membership.role.value,
            "joinedAt": str(membership.joined_at)
        })
    
    return success_response(result)
