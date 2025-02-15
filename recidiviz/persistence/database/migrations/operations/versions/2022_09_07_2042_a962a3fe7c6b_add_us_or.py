# pylint: skip-file
"""add_us_or

Revision ID: a962a3fe7c6b
Revises: e9ebdb3b43b3
Create Date: 2022-09-07 20:42:09.088108

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a962a3fe7c6b"
down_revision = "e9ebdb3b43b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
                INSERT INTO direct_ingest_instance_pause_status (region_code, instance, is_paused) VALUES
                ('US_OR', 'PRIMARY', TRUE),
                ('US_OR', 'SECONDARY', TRUE);
            """
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
