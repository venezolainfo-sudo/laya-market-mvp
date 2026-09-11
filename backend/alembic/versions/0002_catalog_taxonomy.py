"""catalog taxonomy
Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
revision='0002'; down_revision='0001'; branch_labels=None; depends_on=None

def upgrade():
    op.create_table('business_types',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('name',sa.String(100),nullable=False,unique=True),
        sa.Column('slug',sa.String(100),nullable=False,unique=True),
        sa.Column('icon',sa.String(20),nullable=False,server_default='🏪'),
        sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column('order_index',sa.Integer(),nullable=False,server_default='0'))
    op.create_index('ix_business_types_slug','business_types',['slug'])
    op.add_column('businesses',sa.Column('business_type_id',sa.String(36),nullable=True))
    op.create_foreign_key('fk_business_type','businesses','business_types',['business_type_id'],['id'])
    op.create_index('ix_businesses_business_type_id','businesses',['business_type_id'])
    op.add_column('categories',sa.Column('parent_id',sa.String(36),nullable=True))
    op.add_column('categories',sa.Column('business_type_id',sa.String(36),nullable=True))
    op.add_column('categories',sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column('categories',sa.Column('order_index',sa.Integer(),nullable=False,server_default='0'))
    op.create_foreign_key('fk_category_parent','categories','categories',['parent_id'],['id'])
    op.create_foreign_key('fk_category_business_type','categories','business_types',['business_type_id'],['id'])
    op.create_index('ix_categories_parent_id','categories',['parent_id'])
    op.create_index('ix_categories_business_type_id','categories',['business_type_id'])

def downgrade():
    op.drop_index('ix_categories_business_type_id',table_name='categories'); op.drop_index('ix_categories_parent_id',table_name='categories')
    op.drop_constraint('fk_category_business_type','categories',type_='foreignkey'); op.drop_constraint('fk_category_parent','categories',type_='foreignkey')
    op.drop_column('categories','order_index'); op.drop_column('categories','active'); op.drop_column('categories','business_type_id'); op.drop_column('categories','parent_id')
    op.drop_index('ix_businesses_business_type_id',table_name='businesses'); op.drop_constraint('fk_business_type','businesses',type_='foreignkey'); op.drop_column('businesses','business_type_id')
    op.drop_index('ix_business_types_slug',table_name='business_types'); op.drop_table('business_types')
