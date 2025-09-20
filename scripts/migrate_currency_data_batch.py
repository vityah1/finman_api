#!/usr/bin/env python
"""
Optimized script to migrate existing payment data using batch updates.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
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

def migrate_with_sql():
    """Migrate using direct SQL updates for better performance"""
    engine = create_engine(SQLALCHEMY_DATABASE_URI)

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Update MonoBank transactions with foreign currency codes
            logger.info("Updating MonoBank foreign currency transactions...")
            for code, currency in CURRENCY_CODE_MAP.items():
                if code != 980:  # Skip UAH
                    result = conn.execute(text("""
                        UPDATE payments
                        SET currency_original = :currency,
                            amount_original = amount,
                            exchange_rate = 1.0
                        WHERE source = 'mono'
                        AND currencyCode = :code
                        AND (currency_original IS NULL OR currency_original = 'UAH')
                    """), {'currency': currency, 'code': code})
                    if result.rowcount > 0:
                        logger.info(f"  Updated {result.rowcount} MonoBank {currency} transactions")

            # Update MonoBank UAH transactions
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = 'UAH',
                    amount_original = amount,
                    exchange_rate = 1.0
                WHERE source = 'mono'
                AND (currencyCode = 980 OR currencyCode IS NULL)
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} MonoBank UAH transactions")

            # Update PWA transactions with foreign currency
            logger.info("Updating PWA foreign currency transactions...")
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = currency,
                    amount_original = currency_amount,
                    exchange_rate = CASE
                        WHEN currency_amount IS NOT NULL AND currency_amount != 0
                        THEN amount / currency_amount
                        ELSE 1.0
                    END
                WHERE source = 'pwa'
                AND currency != 'UAH'
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} PWA foreign currency transactions")

            # Update PWA UAH transactions
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = 'UAH',
                    amount_original = amount,
                    exchange_rate = 1.0
                WHERE source = 'pwa'
                AND (currency = 'UAH' OR currency IS NULL)
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} PWA UAH transactions")

            # Update Erste transactions
            logger.info("Updating Erste transactions...")
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = currency,
                    amount_original = currency_amount,
                    exchange_rate = CASE
                        WHEN currency_amount IS NOT NULL AND currency_amount != 0
                        THEN amount / currency_amount
                        ELSE 1.0
                    END
                WHERE source = 'erste'
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} Erste transactions")

            # Update P24 transactions
            logger.info("Updating P24 transactions...")
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = COALESCE(currency, 'UAH'),
                    amount_original = COALESCE(currency_amount, amount),
                    exchange_rate = CASE
                        WHEN currency != 'UAH' AND currency_amount IS NOT NULL AND currency_amount != 0
                        THEN amount / currency_amount
                        ELSE 1.0
                    END
                WHERE source = 'p24'
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} P24 transactions")

            # Update PUMB transactions
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = 'UAH',
                    amount_original = amount,
                    exchange_rate = 1.0
                WHERE source = 'pumb'
                AND currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} PUMB transactions")

            # Update remaining transactions (null source or other sources)
            logger.info("Updating remaining transactions...")
            result = conn.execute(text("""
                UPDATE payments
                SET currency_original = CASE
                        WHEN currencyCode = 978 THEN 'EUR'
                        WHEN currencyCode = 840 THEN 'USD'
                        WHEN currencyCode = 348 THEN 'HUF'
                        WHEN currencyCode = 191 THEN 'HRK'
                        WHEN currencyCode = 826 THEN 'GBP'
                        WHEN currencyCode = 203 THEN 'CZK'
                        WHEN currency IS NOT NULL THEN currency
                        ELSE 'UAH'
                    END,
                    amount_original = COALESCE(currency_amount, amount),
                    exchange_rate = CASE
                        WHEN currency != 'UAH' AND currency_amount IS NOT NULL AND currency_amount != 0
                        THEN amount / currency_amount
                        ELSE 1.0
                    END
                WHERE currency_original IS NULL
            """))
            logger.info(f"Updated {result.rowcount} remaining transactions")

            # Commit transaction
            trans.commit()
            logger.info("Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            logger.error(f"Error during migration: {e}")
            raise

def verify_migration():
    """Verify migration results"""
    engine = create_engine(SQLALCHEMY_DATABASE_URI)

    with engine.connect() as conn:
        # Check for NULL values in new fields
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN currency_original IS NULL THEN 1 ELSE 0 END) as null_currency,
                SUM(CASE WHEN amount_original IS NULL THEN 1 ELSE 0 END) as null_amount,
                SUM(CASE WHEN exchange_rate IS NULL THEN 1 ELSE 0 END) as null_rate
            FROM payments
        """)).fetchone()

        logger.info(f"Total payments: {result[0]}")
        logger.info(f"Payments with NULL currency_original: {result[1]}")
        logger.info(f"Payments with NULL amount_original: {result[2]}")
        logger.info(f"Payments with NULL exchange_rate: {result[3]}")

        # Sample by source and currency
        logger.info("\nSample foreign currency transactions by source:")

        for source in ['mono', 'pwa', 'erste', 'p24']:
            result = conn.execute(text("""
                SELECT id, rdate, mydesc, amount, currency_original, amount_original, exchange_rate
                FROM payments
                WHERE source = :source
                AND currency_original != 'UAH'
                ORDER BY rdate DESC
                LIMIT 3
            """), {'source': source}).fetchall()

            if result:
                logger.info(f"\n{source.upper()}:")
                for row in result:
                    logger.info(f"  ID:{row[0]} {row[1].strftime('%Y-%m-%d') if row[1] else 'N/A'} "
                              f"{row[4]} {row[5]:.2f if row[5] else 0} -> UAH {row[3]:.2f if row[3] else 0} "
                              f"(rate: {row[6]:.4f if row[6] else 0})")

if __name__ == "__main__":
    logger.info("Starting optimized currency data migration...")
    migrate_with_sql()
    logger.info("\nVerifying migration...")
    verify_migration()
    logger.info("\nMigration completed!")