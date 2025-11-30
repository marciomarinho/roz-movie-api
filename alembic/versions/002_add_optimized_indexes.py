"""Add optimized indexes for filtering and search performance.

Revision ID: 003
Revises: 002
Create Date: 2025-11-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for filtering operations."""
    # Index on year for year-based filtering
    op.create_index('ix_movies_year', 'movies', ['year'], unique=False)
    
    # GIN index on genres array for efficient array contains queries
    op.create_index(
        'ix_movies_genres_gin',
        'movies',
        ['genres'],
        unique=False,
        postgresql_using='gin'
    )
    
    # Composite index on year and title for combined filtering
    op.create_index(
        'ix_movies_year_title',
        'movies',
        ['year', 'title'],
        unique=False
    )
    
    # Index on title for ILIKE queries (case-insensitive search)
    op.create_index(
        'ix_movies_title_ilike',
        'movies',
        ['title'],
        unique=False,
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove optimized indexes."""
    op.drop_index('ix_movies_title_ilike', table_name='movies')
    op.drop_index('ix_movies_year_title', table_name='movies')
    op.drop_index('ix_movies_genres_gin', table_name='movies')
    op.drop_index('ix_movies_year', table_name='movies')
