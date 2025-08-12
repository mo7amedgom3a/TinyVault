"""baseline existing schema

Revision ID: 001
Revises: 
Create Date: 2025-08-12 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline migration - no changes needed as tables already exist."""
    # This is a baseline migration for the existing database schema
    # No changes are needed as the tables already exist
    pass


def downgrade() -> None:
    """Baseline migration - no changes to revert."""
    # This is a baseline migration for the existing database schema
    # No changes to revert
    pass 