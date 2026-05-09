from collections.abc import Sequence

from alembic import op

revision: str = "20260509_0004"
down_revision: str | None = "20260503_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

OLD_CREDIT_TRANSACTION_TYPES = "'top_up', 'promo', 'spend'"
NEW_CREDIT_TRANSACTION_TYPES = "'welcome_bonus', 'top_up', 'promo', 'spend'"


def upgrade() -> None:
    with op.batch_alter_table("credit_transactions") as batch:
        batch.drop_constraint("type", type_="check")
        batch.create_check_constraint(
            "type",
            f"type IN ({NEW_CREDIT_TRANSACTION_TYPES})",
        )


def downgrade() -> None:
    with op.batch_alter_table("credit_transactions") as batch:
        batch.drop_constraint("type", type_="check")
        batch.create_check_constraint(
            "type",
            f"type IN ({OLD_CREDIT_TRANSACTION_TYPES})",
        )
