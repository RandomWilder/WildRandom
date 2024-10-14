"""Update raffle and ticket models

Revision ID: 16a55c8516e5
Revises: 0569db87349a
Create Date: 2024-10-13 23:20:00.505108

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '16a55c8516e5'
down_revision = '0569db87349a'
branch_labels = None
depends_on = None

def upgrade():
    # Get the current table structure
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('ticket')]

    # Check if ticket_number column exists
    if 'ticket_number' not in columns:
        # Add ticket_number column if it doesn't exist
        op.add_column('ticket', sa.Column('ticket_number', sa.Integer(), nullable=True))
        
        # Copy data from ticket_serial_number to ticket_number
        op.execute('UPDATE ticket SET ticket_number = ticket_serial_number')
        
        # Make ticket_number not nullable
        op.alter_column('ticket', 'ticket_number', nullable=False)

    # Check if ticket_serial_number column exists
    if 'ticket_serial_number' in columns:
        # Drop ticket_serial_number column if it exists
        op.drop_column('ticket', 'ticket_serial_number')

def downgrade():
    # Get the current table structure
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('ticket')]

    # Check if ticket_serial_number column doesn't exist
    if 'ticket_serial_number' not in columns:
        # Add ticket_serial_number column if it doesn't exist
        op.add_column('ticket', sa.Column('ticket_serial_number', sa.Integer(), nullable=True))
        
        # Copy data from ticket_number to ticket_serial_number
        op.execute('UPDATE ticket SET ticket_serial_number = ticket_number')
        
        # Make ticket_serial_number not nullable
        op.alter_column('ticket', 'ticket_serial_number', nullable=False)

    # Check if ticket_number column exists
    if 'ticket_number' in columns:
        # Drop ticket_number column if it exists
        op.drop_column('ticket', 'ticket_number')