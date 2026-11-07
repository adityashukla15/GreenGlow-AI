"""Add persistent Eco Sort game sessions.

Revision ID: 8c2f4d91a6b0
Revises: 2618a6ad1363
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c2f4d91a6b0"
down_revision: Union[str, Sequence[str], None] = "2618a6ad1363"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eco_sort_game_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_ids", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "awarded_score",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_eco_sort_game_sessions_user_id_users",
        ),
        sa.UniqueConstraint(
            "token",
            name="uq_eco_sort_game_session_token",
        ),
    )
    op.create_index(
        "ix_eco_sort_game_sessions_user_id",
        "eco_sort_game_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_eco_sort_game_sessions_user_id",
        table_name="eco_sort_game_sessions",
    )
    op.drop_table("eco_sort_game_sessions")
