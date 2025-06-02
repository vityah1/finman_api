"""Розширення унікального індексу для підтримки кількох тарифів

Revision ID: utility_tariff_support
Revises: b29d05e24af7
Create Date: 2025-06-02 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'utility_tariff_support'
down_revision = 'b29d05e24af7'
branch_labels = None
depends_on = None

def upgrade():
    # Видаляємо старий унікальний індекс
    op.drop_index('ix_utility_readings_user_id', table_name='utility_readings')
    
    # Створюємо новий унікальний індекс з tariff_id
    op.create_index(
        'ix_utility_readings_user_period_tariff', 
        'utility_readings', 
        ['user_id', 'address_id', 'service_id', 'period', 'tariff_id'], 
        unique=True
    )

def downgrade():
    # Видаляємо новий індекс
    op.drop_index('ix_utility_readings_user_period_tariff', table_name='utility_readings')
    
    # Відновлюємо старий індекс
    op.create_index(
        'ix_utility_readings_user_id', 
        'utility_readings', 
        ['user_id', 'address_id', 'service_id', 'period'], 
        unique=True
    )
