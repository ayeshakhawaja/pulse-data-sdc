# pylint: skip-file
"""next_recommended_assessment_date

Revision ID: 33780ebfa36c
Revises: ba901f6c370d
Create Date: 2021-08-04 09:41:45.048510

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "33780ebfa36c"
down_revision = "ba901f6c370d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "etl_clients",
        sa.Column("next_recommended_assessment_date", sa.Date(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("etl_clients", "next_recommended_assessment_date")
    # ### end Alembic commands ###