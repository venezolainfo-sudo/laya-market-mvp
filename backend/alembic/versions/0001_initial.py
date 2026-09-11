"""initial
Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision='0001'; down_revision=None; branch_labels=None; depends_on=None

role=sa.Enum('CUSTOMER','MERCHANT','MERCHANT_STAFF','COURIER','ADMIN','SUPERADMIN',name='role')
businessstatus=sa.Enum('PENDING','APPROVED','SUSPENDED','REJECTED',name='businessstatus')
orderstatus=sa.Enum('NEW','ACCEPTED','PREPARING','READY','COURIER_REQUESTED','ON_THE_WAY','DELIVERED','CANCELLED',name='orderstatus')
paymentstatus=sa.Enum('PENDING','APPROVED','REJECTED','REFUNDED',name='paymentstatus')

def upgrade():
    op.create_table('users',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('email',sa.String(180),nullable=False),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('name',sa.String(120),nullable=False),sa.Column('phone',sa.String(40),nullable=True),sa.Column('role',role,nullable=False),sa.Column('country',sa.String(2),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_index('ix_users_email','users',['email'],unique=True)
    op.create_table('addresses',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('label',sa.String(50),nullable=False),sa.Column('line1',sa.String(220),nullable=False),sa.Column('city',sa.String(120),nullable=False),sa.Column('province',sa.String(120),nullable=False),sa.Column('country',sa.String(2),nullable=False),sa.Column('postal_code',sa.String(20),nullable=True))
    op.create_table('businesses',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('owner_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('name',sa.String(140),nullable=False),sa.Column('description',sa.Text(),nullable=True),sa.Column('logo_url',sa.String(500),nullable=True),sa.Column('country',sa.String(2),nullable=False),sa.Column('city',sa.String(120),nullable=False),sa.Column('address',sa.String(220),nullable=False),sa.Column('status',businessstatus,nullable=False),sa.Column('own_delivery',sa.Boolean(),nullable=False),sa.Column('courier_enabled',sa.Boolean(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_index('ix_businesses_owner_id','businesses',['owner_id'])
    op.create_table('categories',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(100),nullable=False),sa.Column('slug',sa.String(100),nullable=False,unique=True),sa.Column('icon',sa.String(20),nullable=False))
    op.create_index('ix_categories_slug','categories',['slug'],unique=True)
    op.create_table('products',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('business_id',sa.String(36),sa.ForeignKey('businesses.id'),nullable=False),sa.Column('category_id',sa.String(36),sa.ForeignKey('categories.id'),nullable=False),sa.Column('name',sa.String(160),nullable=False),sa.Column('description',sa.Text(),nullable=True),sa.Column('image_url',sa.String(500),nullable=True),sa.Column('price',sa.Numeric(12,2),nullable=False),sa.Column('currency',sa.String(3),nullable=False),sa.Column('stock',sa.Integer(),nullable=False),sa.Column('unit',sa.String(40),nullable=False),sa.Column('active',sa.Boolean(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_index('ix_products_business_id','products',['business_id']);op.create_index('ix_products_category_id','products',['category_id'])
    op.create_table('orders',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('customer_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('business_id',sa.String(36),sa.ForeignKey('businesses.id'),nullable=False),sa.Column('status',orderstatus,nullable=False),sa.Column('currency',sa.String(3),nullable=False),sa.Column('subtotal',sa.Numeric(12,2),nullable=False),sa.Column('delivery_fee',sa.Numeric(12,2),nullable=False),sa.Column('total',sa.Numeric(12,2),nullable=False),sa.Column('delivery_method',sa.String(30),nullable=False),sa.Column('delivery_address',sa.String(350),nullable=False),sa.Column('payment_method',sa.String(40),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_index('ix_orders_business_id','orders',['business_id'])
    op.create_table('order_items',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('order_id',sa.String(36),sa.ForeignKey('orders.id',ondelete='CASCADE'),nullable=False),sa.Column('product_id',sa.String(36),sa.ForeignKey('products.id'),nullable=False),sa.Column('name',sa.String(160),nullable=False),sa.Column('quantity',sa.Integer(),nullable=False),sa.Column('unit_price',sa.Numeric(12,2),nullable=False),sa.Column('subtotal',sa.Numeric(12,2),nullable=False))
    op.create_table('payments',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('order_id',sa.String(36),sa.ForeignKey('orders.id'),nullable=False),sa.Column('provider',sa.String(40),nullable=False),sa.Column('status',paymentstatus,nullable=False),sa.Column('amount',sa.Numeric(12,2),nullable=False),sa.Column('currency',sa.String(3),nullable=False),sa.Column('external_reference',sa.String(160),nullable=True),sa.Column('created_at',sa.DateTime(),nullable=False))
    op.create_table('couriers',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=True),sa.Column('name',sa.String(120),nullable=False),sa.Column('phone',sa.String(40),nullable=False),sa.Column('country',sa.String(2),nullable=False),sa.Column('city',sa.String(120),nullable=False),sa.Column('available',sa.Boolean(),nullable=False))
    op.create_table('deliveries',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('order_id',sa.String(36),sa.ForeignKey('orders.id'),nullable=False,unique=True),sa.Column('courier_id',sa.String(36),sa.ForeignKey('couriers.id'),nullable=True),sa.Column('status',sa.String(30),nullable=False),sa.Column('fee',sa.Numeric(12,2),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False))

def downgrade():
    op.drop_table('deliveries');op.drop_table('couriers');op.drop_table('payments');op.drop_table('order_items');op.drop_index('ix_orders_business_id',table_name='orders');op.drop_table('orders');op.drop_index('ix_products_category_id',table_name='products');op.drop_index('ix_products_business_id',table_name='products');op.drop_table('products');op.drop_index('ix_categories_slug',table_name='categories');op.drop_table('categories');op.drop_index('ix_businesses_owner_id',table_name='businesses');op.drop_table('businesses');op.drop_table('addresses');op.drop_index('ix_users_email',table_name='users');op.drop_table('users')
    paymentstatus.drop(op.get_bind(),checkfirst=True);orderstatus.drop(op.get_bind(),checkfirst=True);businessstatus.drop(op.get_bind(),checkfirst=True);role.drop(op.get_bind(),checkfirst=True)
