from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class GroupCreateRequest(BaseModel):
    name: str

class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    owner_id: int = Field(..., serialization_alias='ownerId')
    created_at: datetime = Field(..., serialization_alias='createdAt')

class GroupListResponse(BaseModel):
    groups: List[GroupResponse]

class GroupSettingsResponse(BaseModel):
    free: dict
    premium: dict

class InviteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_id: int = Field(..., alias='groupId')
    email: EmailStr

class InviteActionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: int = Field(..., alias='requestId')

class GroupMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    user_id: int = Field(..., serialization_alias='userId')
    name: str
    email: str
    joined_at: datetime = Field(..., serialization_alias='joinedAt')

class GroupAccountOwnerResponse(BaseModel):
    name: str

class GroupAccountResponse(BaseModel):
    owner: GroupAccountOwnerResponse
    client_id: str = Field(..., serialization_alias='clientId')
    client_name: str = Field(..., serialization_alias='clientName')

class GroupExitRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_id: int = Field(..., alias='groupId')

class GroupDeleteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_id: int = Field(..., alias='groupId')
