# pylint: skip-file
"""add_status_to_early_dishcarge_reqs

Revision ID: 0002e286d896
Revises: 6affa2223dd1
Create Date: 2020-10-09 11:14:04.874206

"""
import sqlalchemy as sa
from alembic import op

from recidiviz.utils.string import StrictStringFormatter

# revision identifiers, used by Alembic.
revision = "0002e286d896"
down_revision = "6affa2223dd1"
branch_labels = None
depends_on = None

PENDING_EARLY_DISCHARGES_IDS_QUERY = """
    SELECT early_discharge_id 
    FROM state_early_discharge 
    WHERE state_code = 'US_ID' AND decision IS NULL
"""

DECIDED_EARLY_DISCHARGES_IDS_QUERY = """
    SELECT early_discharge_id 
    FROM state_early_discharge 
    WHERE state_code = 'US_ID' AND decision IS NOT NULL
"""


UPDATE_QUERY = """
    UPDATE {table_name}
    SET decision_status = '{decision_status}', decision_status_raw_text = '{decision_status_raw_text}'
    WHERE early_discharge_id IN ({ids_query});
"""

early_discharge_decision_status_values = ["PENDING", "DECIDED", "INVALID"]


def upgrade() -> None:
    # Create the new enum type first
    sa.Enum(
        *early_discharge_decision_status_values,
        name="state_early_discharge_decision_status"
    ).create(bind=op.get_bind())

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "state_early_discharge",
        sa.Column(
            "decision_status",
            sa.Enum(
                *early_discharge_decision_status_values,
                name="state_early_discharge_decision_status"
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "state_early_discharge",
        sa.Column("decision_status_raw_text", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "state_early_discharge_history",
        sa.Column(
            "decision_status",
            sa.Enum(
                *early_discharge_decision_status_values,
                name="state_early_discharge_decision_status"
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "state_early_discharge_history",
        sa.Column("decision_status_raw_text", sa.String(length=255), nullable=True),
    )

    connection = op.get_bind()
    # Update state tables with default values
    pending_state_table_query = StrictStringFormatter().format(
        UPDATE_QUERY,
        table_name="state_early_discharge",
        decision_status="PENDING",
        decision_status_raw_text="PENDING",
        ids_query=PENDING_EARLY_DISCHARGES_IDS_QUERY,
    )
    decided_state_table_query = StrictStringFormatter().format(
        UPDATE_QUERY,
        table_name="state_early_discharge",
        decision_status="DECIDED",
        decision_status_raw_text="DECIDED",
        ids_query=DECIDED_EARLY_DISCHARGES_IDS_QUERY,
    )

    connection.execute(pending_state_table_query)
    connection.execute(decided_state_table_query)

    # Update history tables with default values
    pending_history_table_query = StrictStringFormatter().format(
        UPDATE_QUERY,
        table_name="state_early_discharge_history",
        decision_status="PENDING",
        decision_status_raw_text="PENDING",
        ids_query=PENDING_EARLY_DISCHARGES_IDS_QUERY,
    )
    decided_history_table_query = StrictStringFormatter().format(
        UPDATE_QUERY,
        table_name="state_early_discharge_history",
        decision_status="DECIDED",
        decision_status_raw_text="DECIDED",
        ids_query=DECIDED_EARLY_DISCHARGES_IDS_QUERY,
    )
    connection.execute(pending_history_table_query)
    connection.execute(decided_history_table_query)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("state_early_discharge_history", "decision_status_raw_text")
    op.drop_column("state_early_discharge_history", "decision_status")
    op.drop_column("state_early_discharge", "decision_status_raw_text")
    op.drop_column("state_early_discharge", "decision_status")

    op.execute("DROP TYPE state_early_discharge_decision_status;")
    # ### end Alembic commands ###