"""Add indexes for currency fields performance

Revision ID: add_currency_indexes
Revises: 4f11710e1a1c
Create Date: 2025-09-19 21:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_currency_indexes'
down_revision = '4f11710e1a1c'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes for better query performance
    op.create_index('idx_payments_currency_original', 'payments', ['currency_original'])
    op.create_index('idx_payments_source_currency', 'payments', ['source', 'currency_original'])
    # For year/month queries, we'll use existing rdate index which is already there
    op.create_index('idx_payments_rdate_user', 'payments', ['rdate', 'user_id'])


def downgrade():
    op.drop_index('idx_payments_rdate_user', table_name='payments')
    op.drop_index('idx_payments_source_currency', table_name='payments')
    op.drop_index('idx_payments_currency_original', table_name='payments')