"""Add checklist_items table

Revision ID: 001_checklist
Revises:
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_checklist"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "role",
            sa.Enum("hostess", "waiter", "bartender", "manager", name="userrole", create_type=False),
            nullable=False,
        ),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("order_num", sa.Integer(), server_default="0"),
        sa.Column(
            "branch",
            sa.String(255),
            nullable=False,
            server_default='Бистро "ГАВРОШ" (Пушкинская 36/69)',
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("checklist_items")
