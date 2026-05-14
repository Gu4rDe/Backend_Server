"""make_embedding_nullable

Revision ID: 09e0b3952e0d
Revises: 001
Create Date: 2026-05-14 20:53:00.740714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09e0b3952e0d'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "employees",
        "embedding",
        existing_type=sa.LargeBinary(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "employees",
        "embedding",
        existing_type=sa.LargeBinary(),
        nullable=False,
    )
