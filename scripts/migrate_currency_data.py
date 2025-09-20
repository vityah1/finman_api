#!/usr/bin/env python
"""
Script to migrate existing payment data to populate new currency tracking fields.
This script analyzes existing payments and sets appropriate values for:
- amount_original
- currency_original
- exchange_rate
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from models.models import Payment
from app.config import SQLALCHEMY_DATABASE_URI
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Currency code mapping (ISO 4217)
CURRENCY_CODE_MAP = {
    978: 'EUR',
    840: 'USD',
    980: 'UAH',
    348: 'HUF',
    191: 'HRK',
    826: 'GBP',
    203: 'CZK',
    643: 'RUB',
    985: 'PLN',
    941: 'RSD',
    807: 'MKD',
    8: 'ALL'
}

def get_session():
    """Create database session"""
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def migrate_payments():
    """Migrate payment data to populate new currency fields"""
    session = get_session()

    try:
        # Count total payments
        total_count = session.query(Payment).count()
        logger.info(f"Total payments to process: {total_count}")

        # Process payments in batches
        batch_size = 1000
        offset = 0
        updated_count = 0

        while offset < total_count:
            # Get batch of payments
            payments = session.query(Payment).limit(batch_size).offset(offset).all()

            for payment in payments:
                # Skip if already migrated
                if payment.currency_original is not None and payment.currency_original != 'UAH':
                    continue

                # Determine original currency and amount based on source
                if payment.source == 'mono':
                    # MonoBank transactions
                    if payment.currencyCode and payment.currencyCode != 980:
                        # Foreign currency transaction - MonoBank already converted to UAH
                        payment.currency_original = CURRENCY_CODE_MAP.get(payment.currencyCode, 'UAH')
                        payment.amount_original = payment.amount  # Already in UAH
                        payment.exchange_rate = 1.0  # MonoBank pre-converts
                    else:
                        # UAH transaction
                        payment.currency_original = 'UAH'
                        payment.amount_original = payment.amount
                        payment.exchange_rate = 1.0

                elif payment.source == 'pwa':
                    # Manual entries - already have correct currency data
                    if payment.currency and payment.currency != 'UAH':
                        payment.currency_original = payment.currency
                        payment.amount_original = payment.currency_amount
                        if payment.currency_amount and payment.currency_amount != 0:
                            payment.exchange_rate = float(payment.amount) / float(payment.currency_amount)
                        else:
                            payment.exchange_rate = 1.0
                    else:
                        payment.currency_original = 'UAH'
                        payment.amount_original = payment.amount
                        payment.exchange_rate = 1.0

                elif payment.source == 'erste':
                    # Erste Bank - EUR transactions with calculated rate
                    if payment.currency == 'EUR':
                        payment.currency_original = 'EUR'
                        payment.amount_original = payment.currency_amount
                        if payment.currency_amount and payment.currency_amount != 0:
                            payment.exchange_rate = float(payment.amount) / float(payment.currency_amount)
                        else:
                            payment.exchange_rate = 1.0
                    else:
                        payment.currency_original = 'UAH'
                        payment.amount_original = payment.amount
                        payment.exchange_rate = 1.0

                elif payment.source in ('p24', 'pumb', 'revolut', 'wise'):
                    # Other sources
                    if payment.currency and payment.currency != 'UAH':
                        payment.currency_original = payment.currency
                        payment.amount_original = payment.currency_amount if payment.currency_amount else payment.amount
                        if payment.currency_amount and payment.currency_amount != 0:
                            payment.exchange_rate = float(payment.amount) / float(payment.currency_amount)
                        else:
                            payment.exchange_rate = 1.0
                    else:
                        payment.currency_original = 'UAH'
                        payment.amount_original = payment.amount
                        payment.exchange_rate = 1.0

                else:
                    # Default for unknown sources or null source
                    if payment.currencyCode and payment.currencyCode != 980:
                        payment.currency_original = CURRENCY_CODE_MAP.get(payment.currencyCode, 'UAH')
                    else:
                        payment.currency_original = payment.currency if payment.currency else 'UAH'
                    payment.amount_original = payment.currency_amount if payment.currency_amount else payment.amount
                    payment.exchange_rate = 1.0

                updated_count += 1

            # Commit batch
            session.commit()
            logger.info(f"Processed {min(offset + batch_size, total_count)}/{total_count} payments")

            offset += batch_size

        logger.info(f"Migration complete! Updated {updated_count} payments")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def verify_migration():
    """Verify migration results"""
    session = get_session()

    try:
        # Check for NULL values in new fields
        null_original = session.query(Payment).filter(Payment.currency_original.is_(None)).count()
        null_amount = session.query(Payment).filter(Payment.amount_original.is_(None)).count()
        null_rate = session.query(Payment).filter(Payment.exchange_rate.is_(None)).count()

        logger.info(f"Payments with NULL currency_original: {null_original}")
        logger.info(f"Payments with NULL amount_original: {null_amount}")
        logger.info(f"Payments with NULL exchange_rate: {null_rate}")

        # Sample some records by source
        for source in ['mono', 'pwa', 'erste', 'p24']:
            sample = session.query(Payment).filter(
                Payment.source == source,
                Payment.currency_original != 'UAH'
            ).limit(3).all()

            if sample:
                logger.info(f"\nSample {source} payments with foreign currency:")
                for p in sample:
                    logger.info(f"  ID:{p.id} {p.currency_original} {p.amount_original:.2f} -> UAH {p.amount:.2f} (rate: {p.exchange_rate:.4f})")

    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting currency data migration...")
    migrate_payments()
    logger.info("\nVerifying migration...")
    verify_migration()
    logger.info("\nMigration script completed!")