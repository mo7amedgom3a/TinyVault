import re
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Tuple
from datetime import datetime
from urllib.parse import urlparse
from app.repositories.item_repository import ItemRepository
from app.repositories.user_repository import UserRepository
from app.models import Item


class ItemService:
    """Service layer for item business logic."""
    
    def __init__(self, item_repository: ItemRepository, user_repository: UserRepository):
        self.item_repository = item_repository
        self.user_repository = user_repository
    
    async def create_item(self, owner_user_id: int, content: str, kind: str = None) -> Item:
        """Create a new item with automatic kind detection and short code generation."""
        # Auto-detect kind if not specified
        if kind is None:
            kind = self._detect_content_kind(content)
        
        # Generate unique short code
        short_code = await self._generate_unique_short_code()
        
        # Create the item
        return await self.item_repository.create_item(
            owner_user_id=owner_user_id,
            short_code=short_code,
            kind=kind,
            content=content
        )
    
    async def get_item_by_short_code(self, short_code: str) -> Optional[Item]:
        """Get item by short code."""
        return await self.item_repository.get_by_short_code(short_code)
    
    async def get_user_items(self, owner_user_id: int, limit: int = 10) -> List[Item]:
        """Get items for a specific user."""
        return await self.item_repository.get_by_owner_id(owner_user_id, limit)
    
    async def delete_item(self, short_code: str, owner_user_id: int) -> bool:
        """Soft delete an item."""
        return await self.item_repository.soft_delete(short_code, owner_user_id)
    
    async def hard_delete_item(self, short_code: str) -> bool:
        """Hard delete an item (admin only)."""
        return await self.item_repository.hard_delete(short_code)
    
    async def get_items_by_kind(self, owner_user_id: int, kind: str) -> List[Item]:
        """Get items by kind for a specific user."""
        return await self.item_repository.get_items_by_kind(owner_user_id, kind)
    
    async def search_items(self, owner_user_id: int, query: str) -> List[Item]:
        """Search items by content for a specific user."""
        return await self.item_repository.search_items(owner_user_id, query)
    
    async def get_item_stats(self, owner_user_id: int) -> dict:
        """Get item statistics for a user."""
        return await self.item_repository.get_item_stats(owner_user_id)
    
    async def get_all_items(self, limit: int = 100, offset: int = 0) -> List[Item]:
        """Get all items with pagination (admin only)."""
        items = await self.item_repository.get_all()
        return items[offset:offset + limit]
    
    def _detect_content_kind(self, content: str) -> str:
        """Detect if content is a URL or note."""
        # Simple URL detection
        url_patterns = [
            r'^https?://',  # HTTP/HTTPS URLs
            r'^www\.',      # WWW URLs
            r'^[a-zA-Z0-9-]+\.(com|org|net|io|co|me|dev)$',  # Domain names
        ]
        
        for pattern in url_patterns:
            if re.match(pattern, content.strip()):
                return 'url'
        
        return 'note'
    
    async def _generate_unique_short_code(self, length: int = 6) -> str:
        """Generate a unique short code."""
        import random
        import string
        
        while True:
            # Generate random short code
            short_code = ''.join(
                random.choices(string.ascii_letters + string.digits, k=length)
        )
            
            # Check if it's available
            if await self.item_repository.is_short_code_available(short_code):
                return short_code
    
    async def validate_item_content(self, content: str, kind: str | None) -> dict:
        """Validate item content based on kind."""
        errors = []
        
        if not content or not content.strip():
            errors.append("Content cannot be empty")
        
        if kind == 'url':
            # URL validation
            if not self._is_valid_url(content):
                errors.append("Invalid URL format")
        
        if len(content) > 10000:  # 10KB limit
            errors.append("Content too long (max 10KB)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    async def get_item_with_owner(self, short_code: str) -> Optional[tuple[Item, str]]:
        """Get item with owner information."""
        item = await self.get_item_by_short_code(short_code)
        if not item:
            return None
        
        # Get owner telegram ID for reference
        owner = await self.user_repository.get_by_id(item.owner_user_id)
        owner_telegram_id = owner.telegram_user_id if owner else "Unknown"
        
        return item, str(owner_telegram_id) 