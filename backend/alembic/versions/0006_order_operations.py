"""order operations

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'ASSIGNED'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'PICKED_UP'")
    op.add_column('orders', sa.Column('cancellation_reason', sa.String(length=500), nullable=True))
    op.add_column('orders', sa.Column('cancelled_by', sa.String(length=40), nullable=True))
    op.add_column('orders', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.execute("UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL")

def downgrade():
    op.drop_column('orders','updated_at')
    op.drop_column('orders','cancelled_by')
    op.drop_column('orders','cancellation_reason')
