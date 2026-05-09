from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260502_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

PLAN_CHECK = "plan IN ('free', 'standard', 'pro')"
TONE_CHECK = "tone IN ('formal', 'confident', 'concise')"
GENERATION_STATUS_CHECK = "status IN ('pending', 'succeeded', 'failed')"
SUBSCRIPTION_STATUS_CHECK = "status IN ('active', 'expired')"


def timestamp_columns() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "plan",
            sa.String(length=20),
            server_default=sa.text("'free'"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(PLAN_CHECK, name="ck_users_plan"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )

    op.create_table(
        "employers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hh_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("cached_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_employers"),
        sa.UniqueConstraint("hh_id", name="uq_employers_hh_id"),
    )

    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hh_id", sa.BigInteger(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("cached_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employers.id"],
            name="fk_vacancies_employer_id_employers",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_vacancies"),
        sa.UniqueConstraint("hh_id", name="uq_vacancies_hh_id"),
    )

    op.create_table(
        "resume_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("resume_text", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_resume_profiles_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_resume_profiles"),
        sa.UniqueConstraint("user_id", name="uq_resume_profiles_user_id"),
    )

    op.create_table(
        "generation_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("tone", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            GENERATION_STATUS_CHECK,
            name="ck_generation_requests_status",
        ),
        sa.CheckConstraint(TONE_CHECK, name="ck_generation_requests_tone"),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["resume_profiles.id"],
            name="fk_generation_requests_profile_id_resume_profiles",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_generation_requests_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name="fk_generation_requests_vacancy_id_vacancies",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_generation_requests"),
    )
    op.create_index(
        "ix_generation_requests_user_id_status_created_at",
        "generation_requests",
        ["user_id", "status", "created_at"],
    )

    op.create_table(
        "cover_letters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("generation_request_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_title", sa.String(length=512), nullable=False),
        sa.Column("employer_name", sa.String(length=512), nullable=False),
        sa.Column("tone", sa.String(length=20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("prompt_context", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("generation_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(TONE_CHECK, name="ck_cover_letters_tone"),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employers.id"],
            name="fk_cover_letters_employer_id_employers",
        ),
        sa.ForeignKeyConstraint(
            ["generation_request_id"],
            ["generation_requests.id"],
            name="fk_cover_letters_generation_request_id_generation_requests",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["resume_profiles.id"],
            name="fk_cover_letters_profile_id_resume_profiles",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_cover_letters_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
            name="fk_cover_letters_vacancy_id_vacancies",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cover_letters"),
    )
    op.create_index(
        "ix_cover_letters_user_id_created_at",
        "cover_letters",
        ["user_id", "created_at"],
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(PLAN_CHECK, name="ck_subscriptions_plan"),
        sa.CheckConstraint(
            SUBSCRIPTION_STATUS_CHECK,
            name="ck_subscriptions_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_subscriptions_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
    )
    op.create_index(
        "ix_subscriptions_user_id_status_expires_at",
        "subscriptions",
        ["user_id", "status", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subscriptions_user_id_status_expires_at",
        table_name="subscriptions",
    )
    op.drop_table("subscriptions")
    op.drop_index("ix_cover_letters_user_id_created_at", table_name="cover_letters")
    op.drop_table("cover_letters")
    op.drop_index(
        "ix_generation_requests_user_id_status_created_at",
        table_name="generation_requests",
    )
    op.drop_table("generation_requests")
    op.drop_table("resume_profiles")
    op.drop_table("vacancies")
    op.drop_table("employers")
    op.drop_table("users")
