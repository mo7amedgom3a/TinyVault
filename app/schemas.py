from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List
from datetime import datetime


# Base schemas
class UserBase(BaseModel):
    telegram_user_id: int


class ItemBase(BaseModel):
    kind: str
    content: str
    
    @validator('kind')
    def validate_kind(cls, v):
        if v not in ['url', 'note']:
            raise ValueError('kind must be either "url" or "note"')
        return v
    
    @validator('content')
    def validate_content(cls, v, values):
        if values.get('kind') == 'note' and len(v) > 300:
            raise ValueError('Note content must be 300 characters or less')
        return v


# Request schemas
class SaveItemRequest(BaseModel):
    content: str
    
    @validator('content')
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
    from_user: dict
    chat: dict
    text: Optional[str] = None
    date: int
    
    class Config:
        fields = {
            'from_user': 'from',
            'chat': 'chat',
            'text': 'text',
            'date': 'date'
        }


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None 