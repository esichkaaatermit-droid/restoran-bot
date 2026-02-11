"""Добавление индексов для часто запрашиваемых полей

Revision ID: 003
Revises: 002
"""
from alembic import op


revision = '003'
down_revision = '002'


def upgrade():
    # Индексы для users
    op.create_index('ix_users_phone', 'users', ['phone'])
    op.create_index('ix_users_telegram_username', 'users', ['telegram_username'])
    op.create_index('ix_users_branch_role', 'users', ['branch', 'role'])

    # Индексы для menu_items
    op.create_index('ix_menu_items_branch_type_category', 'menu_items', ['branch', 'menu_type', 'category'])
    op.create_index('ix_menu_items_branch_status', 'menu_items', ['branch', 'status'])

    # Индексы для test_results
    op.create_index('ix_test_results_user_test', 'test_results', ['user_id', 'test_id'])

    # Индексы для training_progress
    op.create_index('ix_training_progress_user_material', 'training_progress', ['user_id', 'material_id'])

    # Индексы для checklist_items
    op.create_index('ix_checklist_items_branch_role', 'checklist_items', ['branch', 'role'])


def downgrade():
    op.drop_index('ix_checklist_items_branch_role')
    op.drop_index('ix_training_progress_user_material')
    op.drop_index('ix_test_results_user_test')
    op.drop_index('ix_menu_items_branch_status')
    op.drop_index('ix_menu_items_branch_type_category')
    op.drop_index('ix_users_branch_role')
    op.drop_index('ix_users_telegram_username')
    op.drop_index('ix_users_phone')
