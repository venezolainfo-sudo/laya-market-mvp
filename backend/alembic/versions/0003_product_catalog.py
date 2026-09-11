"""product catalog
Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
revision='0003'; down_revision='0002'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('products',sa.Column('amount',sa.Numeric(10,3),nullable=False,server_default='1'))
    op.add_column('products',sa.Column('brand',sa.String(100),nullable=True))
    op.add_column('products',sa.Column('sku',sa.String(80),nullable=True))
    op.add_column('products',sa.Column('featured',sa.Boolean(),nullable=False,server_default=sa.false()))
    op.create_index('ix_products_sku','products',['sku'])
    op.create_table('product_images',sa.Column('id',sa.String(36),primary_key=True),sa.Column('product_id',sa.String(36),sa.ForeignKey('products.id',ondelete='CASCADE'),nullable=False),sa.Column('url',sa.String(500),nullable=False),sa.Column('public_id',sa.String(220),nullable=True),sa.Column('order_index',sa.Integer(),nullable=False,server_default='0'))
    op.create_index('ix_product_images_product_id','product_images',['product_id'])
    op.create_table('product_presentations',sa.Column('id',sa.String(36),primary_key=True),sa.Column('product_id',sa.String(36),sa.ForeignKey('products.id',ondelete='CASCADE'),nullable=False),sa.Column('label',sa.String(100),nullable=False),sa.Column('amount',sa.Numeric(10,3),nullable=False,server_default='1'),sa.Column('unit',sa.String(30),nullable=False,server_default='unidad'),sa.Column('price',sa.Numeric(12,2),nullable=False),sa.Column('stock',sa.Integer(),nullable=False,server_default='0'),sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()))
    op.create_index('ix_product_presentations_product_id','product_presentations',['product_id'])

def downgrade():
    op.drop_index('ix_product_presentations_product_id',table_name='product_presentations'); op.drop_table('product_presentations')
    op.drop_index('ix_product_images_product_id',table_name='product_images'); op.drop_table('product_images')
    op.drop_index('ix_products_sku',table_name='products'); op.drop_column('products','featured'); op.drop_column('products','sku'); op.drop_column('products','brand'); op.drop_column('products','amount')
