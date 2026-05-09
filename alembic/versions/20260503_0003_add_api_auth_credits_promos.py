from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260503_0003"
down_revision: str | None = "20260502_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


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
    with op.batch_alter_table("users") as batch:
        batch.alter_column("telegram_id", existing_type=sa.BigInteger(), nullable=True)
        batch.add_column(sa.Column("email", sa.String(length=320), nullable=True))
        batch.add_column(
            sa.Column("password_hash", sa.String(length=255), nullable=True),
        )
        batch.add_column(
            sa.Column(
                "role",
                sa.String(length=20),
                server_default=sa.text("'user'"),
                nullable=False,
            ),
        )
        batch.add_column(
            sa.Column(
                "credits",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
        )
        batch.add_column(
            sa.Column(
                "pending_top_up_discount_percent",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
        )
        batch.create_unique_constraint("uq_users_email", ["email"])
        batch.create_check_constraint("ck_users_role", "role IN ('user', 'admin')")
        batch.create_check_constraint("ck_users_credits_non_negative", "credits >= 0")
        batch.create_check_constraint(
            "ck_users_pending_top_up_discount_percent_range",
            "pending_top_up_discount_percent >= 0 "
            "AND pending_top_up_discount_percent <= 100",
        )

    op.create_table(
        "payment_intents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("credits_amount", sa.Integer(), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column(
            "discount_percent",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="status",
        ),
        sa.CheckConstraint("credits_amount > 0", name="credits_amount_positive"),
        sa.CheckConstraint("amount_rub >= 0", name="amount_rub_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_intents_user_id_status",
        "payment_intents",
        ["user_id", "status"],
    )

    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_activations", sa.Integer(), nullable=False),
        sa.Column(
            "activations_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        *timestamp_columns(),
        sa.CheckConstraint(
            "type IN ('fixed_credits', 'top_up_discount')",
            name="type",
        ),
        sa.CheckConstraint("value > 0", name="value_positive"),
        sa.CheckConstraint("max_activations > 0", name="max_activations_positive"),
        sa.CheckConstraint("activations_count >= 0", name="activations_count_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_promo_codes_code"),
    )

    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("generation_request_id", sa.Integer(), nullable=True),
        sa.Column("payment_intent_id", sa.Integer(), nullable=True),
        sa.Column("promo_code_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("type IN ('top_up', 'promo', 'spend')", name="type"),
        sa.ForeignKeyConstraint(["generation_request_id"], ["generation_requests.id"]),
        sa.ForeignKeyConstraint(["payment_intent_id"], ["payment_intents.id"]),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_credit_transactions_user_id_created_at",
        "credit_transactions",
        ["user_id", "created_at"],
    )

    op.create_table(
        "promo_redemptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("promo_code_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "promo_code_id",
            "user_id",
            name="uq_promo_redemptions_code_user",
        ),
    )
    op.create_index(
        "ix_promo_redemptions_user_id_created_at",
        "promo_redemptions",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_promo_redemptions_user_id_created_at",
        table_name="promo_redemptions",
    )
    op.drop_table("promo_redemptions")
    op.drop_index(
        "ix_credit_transactions_user_id_created_at",
        table_name="credit_transactions",
    )
    op.drop_table("credit_transactions")
    op.drop_table("promo_codes")
    op.drop_index("ix_payment_intents_user_id_status", table_name="payment_intents")
    op.drop_table("payment_intents")

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint(
            "ck_users_pending_top_up_discount_percent_range",
            type_="check",
        )
        batch.drop_constraint("ck_users_credits_non_negative", type_="check")
        batch.drop_constraint("ck_users_role", type_="check")
        batch.drop_constraint("uq_users_email", type_="unique")
        batch.drop_column("pending_top_up_discount_percent")
        batch.drop_column("credits")
        batch.drop_column("role")
        batch.drop_column("password_hash")
        batch.drop_column("email")
        batch.alter_column("telegram_id", existing_type=sa.BigInteger(), nullable=False)
