# pylint: skip-file
"""delete_decision_on_response

Revision ID: 43acad0ef417
Revises: f309c2067b6c
Create Date: 2021-08-31 00:51:08.800491

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "43acad0ef417"
down_revision = "f309c2067b6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("state_supervision_violation_response", "decision_raw_text")
    op.drop_column("state_supervision_violation_response", "decision")
    op.drop_column("state_supervision_violation_response_history", "decision_raw_text")
    op.drop_column("state_supervision_violation_response_history", "decision")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "state_supervision_violation_response_history",
        sa.Column(
            "decision",
            postgresql.ENUM(
                "COMMUNITY_SERVICE",
                "CONTINUANCE",
                "DELAYED_ACTION",
                "EXTENSION",
                "INTERNAL_UNKNOWN",
                "NEW_CONDITIONS",
                "OTHER",
                "REVOCATION",
                "PRIVILEGES_REVOKED",
                "SERVICE_TERMINATION",
                "SPECIALIZED_COURT",
                "SHOCK_INCARCERATION",
                "SUSPENSION",
                "TREATMENT_IN_PRISON",
                "TREATMENT_IN_FIELD",
                "WARNING",
                "WARRANT_ISSUED",
                name="state_supervision_violation_response_decision",
            ),
            autoincrement=False,
            nullable=True,
            comment="DEPRECATED. See #2668.",
        ),
    )
    op.add_column(
        "state_supervision_violation_response_history",
        sa.Column(
            "decision_raw_text",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
            comment="DEPRECATED. See #2668.",
        ),
    )
    op.add_column(
        "state_supervision_violation_response",
        sa.Column(
            "decision",
            postgresql.ENUM(
                "COMMUNITY_SERVICE",
                "CONTINUANCE",
                "DELAYED_ACTION",
                "EXTENSION",
                "INTERNAL_UNKNOWN",
                "NEW_CONDITIONS",
                "OTHER",
                "REVOCATION",
                "PRIVILEGES_REVOKED",
                "SERVICE_TERMINATION",
                "SPECIALIZED_COURT",
                "SHOCK_INCARCERATION",
                "SUSPENSION",
                "TREATMENT_IN_PRISON",
                "TREATMENT_IN_FIELD",
                "WARNING",
                "WARRANT_ISSUED",
                name="state_supervision_violation_response_decision",
            ),
            autoincrement=False,
            nullable=True,
            comment="DEPRECATED. See #2668.",
        ),
    )
    op.add_column(
        "state_supervision_violation_response",
        sa.Column(
            "decision_raw_text",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
            comment="DEPRECATED. See #2668.",
        ),
    )
    # ### end Alembic commands ###