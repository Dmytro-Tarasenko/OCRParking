"""added_is_ban_column_to_messages

Revision ID: a91189dc6f54
Revises: 542fb9150889
Create Date: 2024-09-14 14:51:26.930877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a91189dc6f54'
down_revision: Union[str, None] = '542fb9150889'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('is_ban', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('messages', 'is_ban')
    # ### end Alembic commands ###
