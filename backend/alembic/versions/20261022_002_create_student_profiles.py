"""Create student profiles and reusable skills.

Revision ID: 20261022_002
Revises: 20260930_001
Create Date: 2026-10-22 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20261022_002"
down_revision = "20260930_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("college", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=128), nullable=True),
        sa.Column("branch", sa.String(length=128), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("cgpa", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("tenth_percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("diploma_percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("portfolio_url", sa.String(length=2048), nullable=True),
        sa.Column("github_url", sa.String(length=2048), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_student_profiles_id"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_skills_id"),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_table(
        "student_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["student_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_student_skills_id"),
        sa.UniqueConstraint(
            "profile_id", "skill_id", name="uq_student_skills_profile_skill"
        ),
    )
    op.create_index(
        op.f("ix_student_skills_skill_id"),
        "student_skills",
        ["skill_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_student_skills_skill_id"), table_name="student_skills")
    op.drop_table("student_skills")
    op.drop_table("skills")
    op.drop_table("student_profiles")