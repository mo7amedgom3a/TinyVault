from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utilities.database import Base


class User(Base):
    """User model representing Telegram users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_seen_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    last_seen_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationship
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_user_id={self.telegram_user_id})>"


class Item(Base):
    """Item model representing URLs and notes."""
    
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    short_code = Column(String, unique=True, nullable=False, index=True)
    kind = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("kind IN ('url', 'note')", name="check_kind_valid"),
    )
    
    # Relationships
    owner = relationship("User", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, short_code={self.short_code}, kind={self.kind})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if item is soft deleted."""
        return self.deleted_at is not None 