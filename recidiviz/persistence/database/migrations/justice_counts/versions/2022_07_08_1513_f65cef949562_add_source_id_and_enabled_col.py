# pylint: skip-file
"""add source_id and enabled col

Revision ID: f65cef949562
Revises: 124c1081c77c
Create Date: 2022-07-08 15:13:53.187655

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f65cef949562"
down_revision = "124c1081c77c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("datapoint", sa.Column("source_id", sa.Integer(), nullable=True))
    op.add_column("datapoint", sa.Column("enabled", sa.BOOLEAN(), nullable=True))
    op.alter_column("datapoint", "report_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("datapoint", "start_date", existing_type=sa.DATE(), nullable=True)
    op.alter_column("datapoint", "end_date", existing_type=sa.DATE(), nullable=True)
    op.drop_constraint(
        "datapoint_report_id_start_date_end_date_dimension_identifie_key",
        "datapoint",
        type_="unique",
    )
    op.create_unique_constraint(
        "unique_datapoint",
        "datapoint",
        [
            "report_id",
            "start_date",
            "end_date",
            "dimension_identifier_to_member",
            "context_key",
            "metric_definition_key",
            "source_id",
        ],
    )
    op.create_foreign_key(
        "source_foreign_key_constraint", "datapoint", "source", ["source_id"], ["id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("source_foreign_key_constraint", "datapoint", type_="foreignkey")
    op.drop_constraint("unique_datapoint", "datapoint", type_="unique")
    op.create_unique_constraint(
        "datapoint_report_id_start_date_end_date_dimension_identifie_key",
        "datapoint",
        [
            "report_id",
            "start_date",
            "end_date",
            "dimension_identifier_to_member",
            "context_key",
            "metric_definition_key",
        ],
    )
    op.alter_column("datapoint", "end_date", existing_type=sa.DATE(), nullable=False)
    op.alter_column("datapoint", "start_date", existing_type=sa.DATE(), nullable=False)
    op.alter_column(
        "datapoint", "report_id", existing_type=sa.INTEGER(), nullable=False
    )
    op.drop_column("datapoint", "enabled")
    op.drop_column("datapoint", "source_id")
    # ### end Alembic commands ###