# pylint: skip-file
"""create_metric_metadata

Revision ID: 329e92e5f6de
Revises: 
Create Date: 2022-08-09 15:35:37.564604

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "329e92e5f6de"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "metric_metadata",
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("last_updated", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("metric"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("metric_metadata")
    # ### end Alembic commands ###