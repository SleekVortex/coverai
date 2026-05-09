from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260510_0005"
down_revision: str | None = "20260509_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

OLD_CREDIT_TRANSACTION_TYPES = "'welcome_bonus', 'top_up', 'promo', 'spend'"
NEW_CREDIT_TRANSACTION_TYPES = (
    "'welcome_bonus', 'top_up', 'promo', 'spend', 'adjustment', 'refund'"
)
OLD_PAYMENT_STATUSES = "'pending', 'succeeded', 'failed'"
NEW_PAYMENT_STATUSES = (
    "'pending', 'succeeded', 'failed', 'canceled', 'refunded', "
    "'refund_manual_review'"
)
PLAN_VALUES = "'free', 'standard', 'pro'"


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "pending_top_up_discount_valid_until",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        batch.add_column(
            sa.Column(
                "pending_top_up_discount_promo_code_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        batch.create_foreign_key(
            "fk_users_pending_top_up_discount_promo_code_id_promo_codes",
            "promo_codes",
            ["pending_top_up_discount_promo_code_id"],
            ["id"],
        )

    with op.batch_alter_table("generation_requests") as batch:
        batch.add_column(sa.Column("snapshot_profile_text", sa.Text(), nullable=True))
        batch.add_column(sa.Column("snapshot_vacancy_text", sa.Text(), nullable=True))
        batch.add_column(sa.Column("snapshot_tone", sa.String(20), nullable=True))

    with op.batch_alter_table("credit_transactions") as batch:
        batch.drop_constraint("type", type_="check")
        batch.create_check_constraint(
            "type",
            f"type IN ({NEW_CREDIT_TRANSACTION_TYPES})",
        )

    with op.batch_alter_table("payment_intents") as batch:
        batch.drop_constraint("status", type_="check")
        batch.create_check_constraint(
            "status",
            f"status IN ({NEW_PAYMENT_STATUSES})",
        )

    op.create_table(
        "subscription_payment_intents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"plan IN ({PLAN_VALUES})",
            name="ck_subscription_payment_intents_plan",
        ),
        sa.CheckConstraint(
            f"status IN ({NEW_PAYMENT_STATUSES})",
            name="ck_subscription_payment_intents_status",
        ),
        sa.CheckConstraint(
            "amount_rub >= 0",
            name="ck_subscription_payment_intents_subscription_amount_rub_non_negative",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_subscription_payment_intents_user_id_status",
        "subscription_payment_intents",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subscription_payment_intents_user_id_status",
        table_name="subscription_payment_intents",
    )
    op.drop_table("subscription_payment_intents")

    with op.batch_alter_table("payment_intents") as batch:
        batch.drop_constraint("status", type_="check")
        batch.create_check_constraint(
            "status",
            f"status IN ({OLD_PAYMENT_STATUSES})",
        )

    with op.batch_alter_table("credit_transactions") as batch:
        batch.drop_constraint("type", type_="check")
        batch.create_check_constraint(
            "type",
            f"type IN ({OLD_CREDIT_TRANSACTION_TYPES})",
        )

    with op.batch_alter_table("generation_requests") as batch:
        batch.drop_column("snapshot_tone")
        batch.drop_column("snapshot_vacancy_text")
        batch.drop_column("snapshot_profile_text")

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint(
            "fk_users_pending_top_up_discount_promo_code_id_promo_codes",
            type_="foreignkey",
        )
        batch.drop_column("pending_top_up_discount_promo_code_id")
        batch.drop_column("pending_top_up_discount_valid_until")
