from alembic import op
import sqlalchemy as sa

revision='0007'
down_revision='0006'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('courier_locations',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('courier_id',sa.String(36),sa.ForeignKey('couriers.id',ondelete='CASCADE'),nullable=False),
        sa.Column('delivery_id',sa.String(36),sa.ForeignKey('deliveries.id',ondelete='SET NULL'),nullable=True),
        sa.Column('latitude',sa.Float(),nullable=False),
        sa.Column('longitude',sa.Float(),nullable=False),
        sa.Column('accuracy',sa.Float(),nullable=True),
        sa.Column('created_at',sa.DateTime(),nullable=False),
    )
    op.create_index('ix_courier_locations_courier_id','courier_locations',['courier_id'])
    op.create_index('ix_courier_locations_delivery_id','courier_locations',['delivery_id'])
    op.create_index('ix_courier_locations_created_at','courier_locations',['created_at'])
    op.create_table('notifications',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('order_id',sa.String(36),sa.ForeignKey('orders.id',ondelete='CASCADE'),nullable=True),
        sa.Column('kind',sa.String(60),nullable=False),
        sa.Column('title',sa.String(160),nullable=False),
        sa.Column('body',sa.Text(),nullable=False),
        sa.Column('read',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('created_at',sa.DateTime(),nullable=False),
    )
    op.create_index('ix_notifications_user_id','notifications',['user_id'])
    op.create_index('ix_notifications_order_id','notifications',['order_id'])
    op.create_index('ix_notifications_read','notifications',['read'])
    op.create_index('ix_notifications_created_at','notifications',['created_at'])

def downgrade():
    op.drop_table('notifications')
    op.drop_table('courier_locations')
