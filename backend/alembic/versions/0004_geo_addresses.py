"""geolocation and addresses
Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
revision='0004'; down_revision='0003'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('addresses',sa.Column('reference',sa.String(250),nullable=True))
    op.add_column('addresses',sa.Column('latitude',sa.Float(),nullable=True))
    op.add_column('addresses',sa.Column('longitude',sa.Float(),nullable=True))
    op.add_column('addresses',sa.Column('is_default',sa.Boolean(),nullable=False,server_default=sa.false()))
    op.create_index('ix_addresses_user_id','addresses',['user_id'])
    op.add_column('businesses',sa.Column('latitude',sa.Float(),nullable=True))
    op.add_column('businesses',sa.Column('longitude',sa.Float(),nullable=True))
    op.add_column('businesses',sa.Column('delivery_radius_km',sa.Float(),nullable=False,server_default='8'))

def downgrade():
    op.drop_column('businesses','delivery_radius_km'); op.drop_column('businesses','longitude'); op.drop_column('businesses','latitude')
    op.drop_index('ix_addresses_user_id',table_name='addresses'); op.drop_column('addresses','is_default'); op.drop_column('addresses','longitude'); op.drop_column('addresses','latitude'); op.drop_column('addresses','reference')
