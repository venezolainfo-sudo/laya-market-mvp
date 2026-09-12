from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'whatsapp_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_id', sa.String(160), nullable=False),
        sa.Column('event_type', sa.String(40), nullable=False),
        sa.Column('phone_number_id', sa.String(80), nullable=True),
        sa.Column('from_number', sa.String(40), nullable=True),
        sa.Column('to_number', sa.String(40), nullable=True),
        sa.Column('status', sa.String(40), nullable=True),
        sa.Column('message_type', sa.String(40), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('raw_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('external_id', 'event_type', name='uq_whatsapp_event_external_type'),
    )
    op.create_index('ix_whatsapp_events_external_id', 'whatsapp_events', ['external_id'])
    op.create_index('ix_whatsapp_events_event_type', 'whatsapp_events', ['event_type'])
    op.create_index('ix_whatsapp_events_phone_number_id', 'whatsapp_events', ['phone_number_id'])
    op.create_index('ix_whatsapp_events_from_number', 'whatsapp_events', ['from_number'])
    op.create_index('ix_whatsapp_events_status', 'whatsapp_events', ['status'])
    op.create_index('ix_whatsapp_events_created_at', 'whatsapp_events', ['created_at'])


def downgrade():
    op.drop_index('ix_whatsapp_events_created_at', table_name='whatsapp_events')
    op.drop_index('ix_whatsapp_events_status', table_name='whatsapp_events')
    op.drop_index('ix_whatsapp_events_from_number', table_name='whatsapp_events')
    op.drop_index('ix_whatsapp_events_phone_number_id', table_name='whatsapp_events')
    op.drop_index('ix_whatsapp_events_event_type', table_name='whatsapp_events')
    op.drop_index('ix_whatsapp_events_external_id', table_name='whatsapp_events')
    op.drop_table('whatsapp_events')
