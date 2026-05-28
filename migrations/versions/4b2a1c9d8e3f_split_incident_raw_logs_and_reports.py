"""split incident raw logs and reports

Revision ID: 4b2a1c9d8e3f
Revises: e7fc6e9c12f9
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b2a1c9d8e3f"
down_revision: Union[str, Sequence[str], None] = "e7fc6e9c12f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "incident_raw_logs",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("incident_idx", sa.Integer(), nullable=False),
        sa.Column("evidence_logs", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["incident_idx"], ["incidents.idx"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("idx"),
    )
    op.create_index(op.f("ix_incident_raw_logs_idx"), "incident_raw_logs", ["idx"], unique=False)
    op.create_index(
        op.f("ix_incident_raw_logs_incident_idx"),
        "incident_raw_logs",
        ["incident_idx"],
        unique=False,
    )

    op.create_table(
        "incident_reports",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("incident_idx", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("attack_type", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("attacker_ip", sa.String(length=45), nullable=True),
        sa.Column("analysis_summary", sa.Text(), nullable=True),
        sa.Column("analysis_result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["incident_idx"], ["incidents.idx"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("idx"),
    )
    op.create_index(op.f("ix_incident_reports_idx"), "incident_reports", ["idx"], unique=False)
    op.create_index(
        op.f("ix_incident_reports_incident_idx"),
        "incident_reports",
        ["incident_idx"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_reports_thread_id"),
        "incident_reports",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_reports_attack_type"),
        "incident_reports",
        ["attack_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_reports_attacker_ip"),
        "incident_reports",
        ["attacker_ip"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO incident_raw_logs (incident_idx, evidence_logs, raw_payload, created_at)
        SELECT idx, COALESCE(evidence_logs, ''), raw_payload, created_at
        FROM incidents
        WHERE evidence_logs IS NOT NULL OR raw_payload IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO incident_reports (
            incident_idx,
            thread_id,
            attack_type,
            confidence_score,
            attacker_ip,
            analysis_summary,
            analysis_result,
            created_at
        )
        SELECT
            idx,
            thread_id,
            attack_type,
            confidence_score,
            attacker_ip,
            analysis_summary,
            analysis_result,
            modified_at
        FROM incidents
        WHERE analysis_result IS NOT NULL
        """
    )

    op.drop_index(op.f("ix_incidents_attack_type"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_attacker_ip"), table_name="incidents")
    op.drop_column("incidents", "thread_id")
    op.drop_column("incidents", "evidence_logs")
    op.drop_column("incidents", "raw_payload")
    op.drop_column("incidents", "analysis_result")
    op.drop_column("incidents", "analysis_summary")
    op.drop_column("incidents", "attack_type")
    op.drop_column("incidents", "confidence_score")
    op.drop_column("incidents", "attacker_ip")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("incidents", sa.Column("attacker_ip", sa.String(length=45), nullable=True))
    op.add_column("incidents", sa.Column("confidence_score", sa.Float(), nullable=True))
    op.add_column("incidents", sa.Column("attack_type", sa.String(length=100), nullable=True))
    op.add_column("incidents", sa.Column("analysis_summary", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("analysis_result", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("raw_payload", sa.JSON(), nullable=True))
    op.add_column("incidents", sa.Column("evidence_logs", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("thread_id", sa.String(length=255), nullable=True))

    op.execute(
        """
        UPDATE incidents
        SET
            evidence_logs = latest_raw.evidence_logs,
            raw_payload = latest_raw.raw_payload
        FROM (
            SELECT DISTINCT ON (incident_idx)
                incident_idx,
                evidence_logs,
                raw_payload
            FROM incident_raw_logs
            ORDER BY incident_idx, created_at DESC, idx DESC
        ) AS latest_raw
        WHERE latest_raw.incident_idx = incidents.idx
        """
    )
    op.execute(
        """
        UPDATE incidents
        SET
            thread_id = latest_report.thread_id,
            attack_type = latest_report.attack_type,
            confidence_score = latest_report.confidence_score,
            attacker_ip = latest_report.attacker_ip,
            analysis_summary = latest_report.analysis_summary,
            analysis_result = latest_report.analysis_result
        FROM (
            SELECT DISTINCT ON (incident_idx)
                incident_idx,
                thread_id,
                attack_type,
                confidence_score,
                attacker_ip,
                analysis_summary,
                analysis_result
            FROM incident_reports
            ORDER BY incident_idx, created_at DESC, idx DESC
        ) AS latest_report
        WHERE latest_report.incident_idx = incidents.idx
        """
    )

    op.create_index(op.f("ix_incidents_attacker_ip"), "incidents", ["attacker_ip"], unique=False)
    op.create_index(op.f("ix_incidents_attack_type"), "incidents", ["attack_type"], unique=False)

    op.drop_index(op.f("ix_incident_reports_attacker_ip"), table_name="incident_reports")
    op.drop_index(op.f("ix_incident_reports_attack_type"), table_name="incident_reports")
    op.drop_index(op.f("ix_incident_reports_thread_id"), table_name="incident_reports")
    op.drop_index(op.f("ix_incident_reports_incident_idx"), table_name="incident_reports")
    op.drop_index(op.f("ix_incident_reports_idx"), table_name="incident_reports")
    op.drop_table("incident_reports")

    op.drop_index(op.f("ix_incident_raw_logs_incident_idx"), table_name="incident_raw_logs")
    op.drop_index(op.f("ix_incident_raw_logs_idx"), table_name="incident_raw_logs")
    op.drop_table("incident_raw_logs")
