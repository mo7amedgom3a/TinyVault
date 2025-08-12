from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, List
from datetime import datetime


# Base schemas
class UserBase(BaseModel):
    telegram_user_id: int


# Minimal user schemas for service imports
class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    telegram_user_id: Optional[int] = None


class ItemBase(BaseModel):
    kind: str
    content: str
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        if v not in ['url', 'note']:
            raise ValueError('kind must be either "url" or "note"')
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v, info):
        if info.data.get('kind') == 'note' and len(v) > 300:
            raise ValueError('Note content must be 300 characters or less')
        return v


# Request schemas
class SaveItemRequest(BaseModel):
    content: str
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class TelegramWebhookRequest(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None


# Response schemas
class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    item_count: int
    
    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    id: int
    short_code: str
    kind: str
    content: str
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SaveItemResponse(BaseModel):
    short_code: str
    message: str


class ListItemsResponse(BaseModel):
    items: List[ItemResponse]
    total: int


class AdminUsersResponse(BaseModel):
    users: List[UserResponse]
    total: int


class AdminItemsResponse(BaseModel):
    items: List[ItemResponse]
    total: int
    offset: int
    limit: int


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Telegram message schemas
class TelegramMessage(BaseModel):
    message_id: int
    from_user: dict = Field(alias='from')
    chat: dict
    text: Optional[str] = None
    date: int
    
    class Config:
        from_attributes = True
        populate_by_name = True


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None 