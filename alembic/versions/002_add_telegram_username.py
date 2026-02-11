"""Добавление поля telegram_username в users

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001_checklist'


def upgrade():
    op.add_column('users', sa.Column('telegram_username', sa.String(100), nullable=True))
    # Убираем unique и not null с phone (теперь может быть пустым)
    op.alter_column('users', 'phone', existing_type=sa.String(20), nullable=True)


def downgrade():
    op.alter_column('users', 'phone', existing_type=sa.String(20), nullable=False)
    op.drop_column('users', 'telegram_username')
