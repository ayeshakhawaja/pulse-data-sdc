# pylint: skip-file
"""create_auth_tables

Revision ID: 7670e37f7497
Revises: f8294df87fa7
Create Date: 2022-07-20 13:04:30.695399

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7670e37f7497"
down_revision = "f8294df87fa7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "permissions_override",
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("can_access_leadership_dashboard", sa.Boolean(), nullable=True),
        sa.Column("can_access_case_triage", sa.Boolean(), nullable=True),
        sa.Column("should_see_beta_charts", sa.Boolean(), nullable=True),
        sa.Column("routes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("user_email"),
    )
    op.create_table(
        "roster",
        sa.Column("state_code", sa.String(length=255), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("email_address"),
    )
    op.create_table(
        "state_role_permissions",
        sa.Column("state_code", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("can_access_leadership_dashboard", sa.Boolean(), nullable=True),
        sa.Column("can_access_case_triage", sa.Boolean(), nullable=True),
        sa.Column("should_see_beta_charts", sa.Boolean(), nullable=True),
        sa.Column("routes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("state_code", "role"),
    )
    op.create_table(
        "user_override",
        sa.Column("state_code", sa.String(length=255), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("email_address"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_override")
    op.drop_table("state_role_permissions")
    op.drop_table("roster")
    op.drop_table("permissions_override")
    # ### end Alembic commands ###