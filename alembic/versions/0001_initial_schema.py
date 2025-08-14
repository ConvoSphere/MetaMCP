"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2025-07-27 06:35:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create tools table
    op.create_table(
        "tools",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("endpoint", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("security_level", sa.Integer(), nullable=False),
        sa.Column("schema", sa.JSON(), nullable=True),
        sa.Column("tool_metadata", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tools_category"), "tools", ["category"], unique=False)
    op.create_index(op.f("ix_tools_name"), "tools", ["name"], unique=True)

    # Create execution_history table
    op.create_table(
        "execution_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tool_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tools.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_execution_history_status"),
        "execution_history",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_execution_history_tool_id"),
        "execution_history",
        ["tool_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_execution_history_user_id"),
        "execution_history",
        ["user_id"],
        unique=False,
    )

    # Create search_history table
    op.create_table(
        "search_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("search_type", sa.String(length=50), nullable=False),
        sa.Column("max_results", sa.Integer(), nullable=False),
        sa.Column("similarity_threshold", sa.Integer(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_search_history_search_type"),
        "search_history",
        ["search_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_history_status"), "search_history", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_search_history_user_id"), "search_history", ["user_id"], unique=False
    )

    # Create vector_embeddings table
    op.create_table(
        "vector_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tool_id", sa.String(length=36), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("embedding_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tools.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_vector_embeddings_tool_id"),
        "vector_embeddings",
        ["tool_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vector_embeddings_tool_id"), table_name="vector_embeddings")
    op.drop_table("vector_embeddings")
    op.drop_index(op.f("ix_search_history_user_id"), table_name="search_history")
    op.drop_index(op.f("ix_search_history_status"), table_name="search_history")
    op.drop_index(op.f("ix_search_history_search_type"), table_name="search_history")
    op.drop_table("search_history")
    op.drop_index(op.f("ix_execution_history_user_id"), table_name="execution_history")
    op.drop_index(op.f("ix_execution_history_tool_id"), table_name="execution_history")
    op.drop_index(op.f("ix_execution_history_status"), table_name="execution_history")
    op.drop_table("execution_history")
    op.drop_index(op.f("ix_tools_name"), table_name="tools")
    op.drop_index(op.f("ix_tools_category"), table_name="tools")
    op.drop_table("tools")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
