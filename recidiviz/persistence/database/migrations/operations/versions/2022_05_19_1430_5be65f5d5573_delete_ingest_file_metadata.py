# pylint: skip-file
"""delete_ingest_file_metadata

Revision ID: 5be65f5d5573
Revises: ad544da7c305
Create Date: 2022-05-19 14:30:30.711695

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5be65f5d5573"
down_revision = "ad544da7c305"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "ix_direct_ingest_ingest_file_metadata_file_tag",
        table_name="direct_ingest_ingest_file_metadata",
    )
    op.drop_index(
        "ix_direct_ingest_ingest_file_metadata_normalized_file_name",
        table_name="direct_ingest_ingest_file_metadata",
    )
    op.drop_index(
        "ix_direct_ingest_ingest_file_metadata_region_code",
        table_name="direct_ingest_ingest_file_metadata",
    )
    op.drop_table("direct_ingest_ingest_file_metadata")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "direct_ingest_ingest_file_metadata",
        sa.Column("file_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "region_code", sa.VARCHAR(length=255), autoincrement=False, nullable=False
        ),
        sa.Column(
            "file_tag", sa.VARCHAR(length=255), autoincrement=False, nullable=False
        ),
        sa.Column(
            "normalized_file_name",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "discovery_time", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "processed_time", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column("is_invalidated", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column(
            "job_creation_time",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "datetimes_contained_lower_bound_exclusive",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "datetimes_contained_upper_bound_inclusive",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "export_time", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column("is_file_split", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column(
            "ingest_database_name", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.CheckConstraint(
            "(NOT is_file_split) OR (normalized_file_name IS NOT NULL)",
            name="split_files_created_with_file_name",
        ),
        sa.CheckConstraint(
            "(datetimes_contained_lower_bound_exclusive IS NULL) OR (datetimes_contained_lower_bound_exclusive < datetimes_contained_upper_bound_inclusive)",
            name="datetimes_contained_ordering",
        ),
        sa.CheckConstraint(
            "(discovery_time IS NULL) OR (export_time IS NOT NULL)",
            name="discovery_after_export",
        ),
        sa.CheckConstraint(
            "(export_time IS NULL) OR (normalized_file_name IS NOT NULL)",
            name="export_after_normalized_file_name_set",
        ),
        sa.CheckConstraint(
            "(processed_time IS NULL) OR (discovery_time IS NOT NULL)",
            name="processed_after_discovery",
        ),
        sa.PrimaryKeyConstraint(
            "file_id", name="direct_ingest_ingest_file_metadata_pkey"
        ),
    )
    op.create_index(
        "ix_direct_ingest_ingest_file_metadata_region_code",
        "direct_ingest_ingest_file_metadata",
        ["region_code"],
        unique=False,
    )
    op.create_index(
        "ix_direct_ingest_ingest_file_metadata_normalized_file_name",
        "direct_ingest_ingest_file_metadata",
        ["normalized_file_name"],
        unique=False,
    )
    op.create_index(
        "ix_direct_ingest_ingest_file_metadata_file_tag",
        "direct_ingest_ingest_file_metadata",
        ["file_tag"],
        unique=False,
    )
    # ### end Alembic commands ###