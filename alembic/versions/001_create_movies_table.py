"""Create movies table.

Revision ID: 001
Revises: 
Create Date: 2025-11-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the movies table."""
    op.create_table(
        'movies',
        sa.Column('movie_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('genres', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('movie_id')
    )
    op.create_index(op.f('ix_movies_title'), 'movies', ['title'], unique=False)


def downgrade() -> None:
    """Drop the movies table."""
    op.drop_index(op.f('ix_movies_title'), table_name='movies')
    op.drop_table('movies')
