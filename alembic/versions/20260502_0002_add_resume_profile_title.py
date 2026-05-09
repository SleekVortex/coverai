from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260502_0002"
down_revision: str | None = "20260502_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "resume_profiles",
        sa.Column(
            "title",
            sa.String(length=255),
            server_default=sa.text("'Resume'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("resume_profiles", "title")
