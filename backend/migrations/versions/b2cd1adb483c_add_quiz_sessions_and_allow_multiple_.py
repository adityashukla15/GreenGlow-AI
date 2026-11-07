"""Add quiz sessions and allow multiple quiz attempts."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2cd1adb483c"
down_revision: Union[str, Sequence[str], None] = "3f8d65b5079d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SESSION_FK = "fk_quiz_attempts_quiz_session_id_quiz_sessions"


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = sa.inspect(bind).get_table_names()

    if "quiz_sessions" not in existing_tables:
        op.create_table(
            "quiz_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("token", sa.String(length=36), nullable=False),
            sa.Column("question_ids", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "submitted_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.create_index(
            "ix_quiz_sessions_id",
            "quiz_sessions",
            ["id"],
            unique=False,
        )
        op.create_index(
            "ix_quiz_sessions_token",
            "quiz_sessions",
            ["token"],
            unique=True,
        )

    with op.batch_alter_table(
        "quiz_attempts",
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        },
    ) as batch_op:
        batch_op.add_column(
            sa.Column("quiz_session_id", sa.Integer(), nullable=True)
        )
        batch_op.drop_constraint(
            "uq_quiz_attempt_user",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_quiz_attempt_session",
            ["quiz_session_id"],
        )
        batch_op.create_foreign_key(
            SESSION_FK,
            "quiz_sessions",
            ["quiz_session_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()

    duplicate_users = bind.execute(
        sa.text(
            "SELECT user_id FROM quiz_attempts "
            "GROUP BY user_id HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()

    if duplicate_users:
        raise RuntimeError(
            "Cannot downgrade safely: multiple quiz attempts exist for "
            "at least one user. Resolve duplicates before downgrading."
        )

    with op.batch_alter_table(
        "quiz_attempts",
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        },
    ) as batch_op:
        batch_op.drop_constraint(SESSION_FK, type_="foreignkey")
        batch_op.drop_constraint(
            "uq_quiz_attempt_session",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_quiz_attempt_user",
            ["user_id"],
        )
        batch_op.drop_column("quiz_session_id")
