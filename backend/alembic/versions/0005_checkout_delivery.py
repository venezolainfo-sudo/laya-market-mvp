"""checkout delivery
Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa
revision='0005'; down_revision='0004'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('businesses',sa.Column('delivery_base_fee',sa.Numeric(12,2),nullable=False,server_default='0'))
    op.add_column('businesses',sa.Column('delivery_per_km',sa.Numeric(12,2),nullable=False,server_default='0'))
    op.add_column('businesses',sa.Column('delivery_min_fee',sa.Numeric(12,2),nullable=False,server_default='0'))
    op.add_column('businesses',sa.Column('pickup_enabled',sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column('orders',sa.Column('address_id',sa.String(36),nullable=True))
    op.create_foreign_key('fk_orders_address','orders','addresses',['address_id'],['id'])
    op.add_column('orders',sa.Column('delivery_latitude',sa.Float(),nullable=True))
    op.add_column('orders',sa.Column('delivery_longitude',sa.Float(),nullable=True))
    op.add_column('orders',sa.Column('distance_km',sa.Float(),nullable=True))
    op.add_column('orders',sa.Column('customer_name',sa.String(120),nullable=True))
    op.add_column('orders',sa.Column('customer_phone',sa.String(40),nullable=True))
    op.add_column('orders',sa.Column('notes',sa.String(500),nullable=True))
    op.add_column('order_items',sa.Column('presentation_id',sa.String(36),nullable=True))
    op.create_foreign_key('fk_order_items_presentation','order_items','product_presentations',['presentation_id'],['id'])
    op.add_column('order_items',sa.Column('presentation_label',sa.String(100),nullable=True))

def downgrade():
    op.drop_column('order_items','presentation_label')
    op.drop_constraint('fk_order_items_presentation','order_items',type_='foreignkey')
    op.drop_column('order_items','presentation_id')
    op.drop_column('orders','notes'); op.drop_column('orders','customer_phone'); op.drop_column('orders','customer_name'); op.drop_column('orders','distance_km'); op.drop_column('orders','delivery_longitude'); op.drop_column('orders','delivery_latitude')
    op.drop_constraint('fk_orders_address','orders',type_='foreignkey'); op.drop_column('orders','address_id')
    op.drop_column('businesses','pickup_enabled'); op.drop_column('businesses','delivery_min_fee'); op.drop_column('businesses','delivery_per_km'); op.drop_column('businesses','delivery_base_fee')
