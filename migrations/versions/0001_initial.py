from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

STATUSES = "'новая', 'в работе', 'на проверке', 'выполнена', 'отменена'"
PRIORITIES = "'низкий', 'средний', 'высокий'"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_topics"),
        sa.UniqueConstraint("name", name="uq_topics_name"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="новая", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="средний", nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"status IN ({STATUSES})", name="ck_tasks_status"),
        sa.CheckConstraint(f"priority IN ({PRIORITIES})", name="ck_tasks_priority"),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], name="fk_tasks_topic_id_topics", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"], ["users.id"], name="fk_tasks_assignee_id_users", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name="fk_tasks_author_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_topic_id", "tasks", ["topic_id"])
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_assignee_id", table_name="tasks")
    op.drop_index("ix_tasks_topic_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("topics")
    op.drop_table("users")
