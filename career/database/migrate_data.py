#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career Data Migration Script

Full regeneration migration with FK dependency ordering and integrity validation.
Usage:
    python migrate_data.py --dry-run          # Preview without execution
    python migrate_data.py --execute          # Execute migration
    python migrate_data.py --validate-only    # Run validation checks only
    python migrate_data.py --backup           # Backup before migration
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import execute_values

from migration_config import (
    DB_CONFIG, SCHEMA, TABLE_LEVELS,
    get_all_tables_in_order, get_truncate_order, TARGET_ROW_COUNTS
)
from data_generators import DataGenerator
from validators import DataValidator

# ============================================
# Logging Configuration
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# Migration Engine
# ============================================
class MigrationEngine:
    """Main migration engine with transaction safety."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.generator = None
        self.validator = None
        self.stats = {
            'truncated': [],
            'generated': {},
            'errors': [],
            'validation_results': {}
        }

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False  # Transaction mode
            self.cursor = self.conn.cursor()
            self.cursor.execute(f"SET search_path TO {SCHEMA}")
            logger.info(f"Connected to database: {DB_CONFIG['database']} (schema: {SCHEMA})")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def backup_schema(self) -> str:
        """Create backup of current schema data."""
        backup_file = f'backup_idino_career_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
        logger.info(f"Creating backup: {backup_file}")

        import subprocess
        cmd = [
            'pg_dump',
            '-h', DB_CONFIG['host'],
            '-p', str(DB_CONFIG['port']),
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['database'],
            '-n', SCHEMA,
            '-f', backup_file
        ]

        try:
            env = {'PGPASSWORD': DB_CONFIG['password']}
            subprocess.run(cmd, check=True, env=env, capture_output=True)
            logger.info(f"Backup created successfully: {backup_file}")
            return backup_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr.decode() if e.stderr else str(e)}")
            return ""

    def truncate_all_tables(self) -> bool:
        """Truncate all tables in reverse FK dependency order."""
        truncate_order = get_truncate_order()
        logger.info(f"Truncating {len(truncate_order)} tables in reverse FK order...")

        for table in truncate_order:
            try:
                if self.dry_run:
                    logger.info(f"  [DRY-RUN] Would truncate: {table}")
                else:
                    self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                    logger.info(f"  Truncated: {table}")
                self.stats['truncated'].append(table)
            except Exception as e:
                logger.error(f"  Failed to truncate {table}: {e}")
                self.stats['errors'].append(('truncate', table, str(e)))
                return False

        return True

    def generate_level(self, level: int, level_name: str, tables: List[str]) -> bool:
        """Generate data for all tables in a specific level."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating {level_name}: {len(tables)} tables")
        logger.info(f"{'='*60}")

        for table in tables:
            target_count = TARGET_ROW_COUNTS.get(table, 0)
            if target_count == 0:
                logger.warning(f"  Skipping {table}: No target count defined")
                continue

            try:
                # Get generator method
                method_name = f"gen_{table.replace('tb_', '')}"
                gen_method = getattr(self.generator, method_name, None)

                if gen_method is None:
                    logger.warning(f"  No generator for {table} ({method_name})")
                    continue

                # Generate data
                logger.info(f"  Generating {table} (target: {target_count:,})...")
                start_time = time.time()
                # Most generators don't take count param - they use config
                try:
                    rows = gen_method(target_count)
                except TypeError:
                    # Fallback for generators without count parameter
                    rows = gen_method()
                gen_time = time.time() - start_time

                if not rows:
                    logger.warning(f"    No data generated for {table}")
                    continue

                # Insert data
                if self.dry_run:
                    logger.info(f"    [DRY-RUN] Would insert {len(rows):,} rows ({gen_time:.2f}s)")
                    self.stats['generated'][table] = len(rows)
                else:
                    inserted = self._insert_rows(table, rows)
                    self.stats['generated'][table] = inserted
                    logger.info(f"    Inserted {inserted:,} rows ({gen_time:.2f}s)")

            except Exception as e:
                logger.error(f"  Error generating {table}: {e}")
                self.stats['errors'].append(('generate', table, str(e)))
                import traceback
                traceback.print_exc()
                return False

        return True

    def _insert_rows(self, table: str, rows: List[Dict]) -> int:
        """Insert rows into table using batch insert."""
        if not rows:
            return 0

        columns = list(rows[0].keys())
        col_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        # Batch insert (500 rows per batch)
        batch_size = 500
        total_inserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values = [tuple(row[col] for col in columns) for row in batch]

            try:
                sql = f"INSERT INTO {table} ({col_str}) VALUES %s"
                execute_values(self.cursor, sql, values, page_size=batch_size)
                total_inserted += len(batch)
            except Exception as e:
                logger.error(f"Batch insert error for {table}: {e}")
                raise

        return total_inserted

    def run_validation(self) -> Tuple[int, int]:
        """Run all validation checks."""
        logger.info("\n" + "="*60)
        logger.info("Running Data Integrity Validation")
        logger.info("="*60)

        if self.dry_run:
            logger.info("[DRY-RUN] Validation skipped in dry-run mode")
            return 0, 0

        results = self.validator.run_all_checks()

        passed = 0
        failed = 0

        for result in results:
            status = "PASS" if result.passed else "FAIL"

            if result.passed:
                passed += 1
                logger.info(f"  [PASS] {result.check_name}: {status}")
            else:
                failed += 1
                logger.error(f"  [FAIL] {result.check_name}: {status} - {result.message}")

        self.stats['validation_results'] = results
        return passed, failed

    def print_summary(self):
        """Print migration summary."""
        logger.info("\n" + "="*60)
        logger.info("Migration Summary")
        logger.info("="*60)

        mode = "[DRY-RUN]" if self.dry_run else "[EXECUTED]"
        logger.info(f"Mode: {mode}")

        logger.info(f"\nTables truncated: {len(self.stats['truncated'])}")

        total_rows = sum(self.stats['generated'].values())
        logger.info(f"\nData generated:")
        for level_name, tables in TABLE_LEVELS:
            level_rows = sum(self.stats['generated'].get(t, 0) for t in tables)
            if level_rows > 0:
                logger.info(f"  {level_name}: {level_rows:,} rows")
        logger.info(f"  Total: {total_rows:,} rows")

        if self.stats['errors']:
            logger.error(f"\nErrors: {len(self.stats['errors'])}")
            for err_type, table, msg in self.stats['errors']:
                logger.error(f"  [{err_type}] {table}: {msg}")

        if self.stats['validation_results']:
            passed = sum(1 for r in self.stats['validation_results'] if r.passed)
            total = len(self.stats['validation_results'])
            logger.info(f"\nValidation: {passed}/{total} checks passed")

    def execute(self) -> bool:
        """Execute full migration."""
        logger.info("="*60)
        logger.info("IDINO Career Data Migration")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'EXECUTE'}")
        logger.info(f"Started: {datetime.now().isoformat()}")
        logger.info("="*60)

        # Connect
        if not self.connect():
            return False

        # Initialize generator and validator
        self.generator = DataGenerator(self.conn)
        self.validator = DataValidator(self.conn)

        try:
            # Step 1: Truncate all tables
            if not self.truncate_all_tables():
                raise Exception("Truncation failed")

            # Step 2: Generate data level by level
            for i, (level_name, tables) in enumerate(TABLE_LEVELS, 1):
                if not self.generate_level(i, level_name, tables):
                    raise Exception(f"Generation failed at {level_name}")

            # Step 3: Run validation
            passed, failed = self.run_validation()

            if failed > 0 and not self.dry_run:
                raise Exception(f"Validation failed: {failed} checks did not pass")

            # Commit transaction
            if not self.dry_run:
                self.conn.commit()
                logger.info("\n[SUCCESS] Migration committed successfully!")
            else:
                logger.info("\n[SUCCESS] Dry-run completed successfully!")

            return True

        except Exception as e:
            logger.error(f"\n[FAILED] Migration failed: {e}")
            if self.conn and not self.dry_run:
                self.conn.rollback()
                logger.info("Transaction rolled back")
            return False

        finally:
            self.print_summary()
            self.disconnect()


# ============================================
# Validation-Only Mode
# ============================================
def run_validation_only():
    """Run validation checks on existing data."""
    logger.info("="*60)
    logger.info("IDINO Career Data Validation")
    logger.info("="*60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {SCHEMA}")

        validator = DataValidator(conn)
        results = validator.run_all_checks()

        passed = 0
        failed = 0

        logger.info("\nValidation Results:")
        for result in results:
            status = "PASS" if result.passed else "FAIL"

            if result.passed:
                passed += 1
                logger.info(f"  [PASS] {result.check_name}: {status}")
            else:
                failed += 1
                logger.error(f"  [FAIL] {result.check_name}: {status}")
                if result.message:
                    logger.error(f"      {result.message}")

        logger.info(f"\nSummary: {passed} passed, {failed} failed")

        conn.close()
        return failed == 0

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


# ============================================
# Row Count Check
# ============================================
def check_row_counts():
    """Check current row counts vs target."""
    logger.info("="*60)
    logger.info("IDINO Career Row Count Check")
    logger.info("="*60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {SCHEMA}")

        total_current = 0
        total_target = 0

        for level_name, tables in TABLE_LEVELS:
            logger.info(f"\n{level_name}:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                current = cursor.fetchone()[0]
                target = TARGET_ROW_COUNTS.get(table, 0)

                total_current += current
                total_target += target

                if current >= target:
                    status = "[OK]"
                elif current > 0:
                    status = "[PARTIAL]"
                else:
                    status = "[EMPTY]"
                logger.info(f"  {status} {table}: {current:,} / {target:,}")

        logger.info(f"\n{'='*60}")
        logger.info(f"Total: {total_current:,} / {total_target:,} rows")

        conn.close()

    except Exception as e:
        logger.error(f"Row count check error: {e}")


# ============================================
# Main Entry Point
# ============================================
def main():
    parser = argparse.ArgumentParser(
        description='IDINO Career Data Migration Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_data.py --dry-run          Preview migration
  python migrate_data.py --execute          Execute migration
  python migrate_data.py --validate-only    Validate existing data
  python migrate_data.py --count            Check row counts
  python migrate_data.py --backup --execute Backup then execute
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                       help='Preview migration without executing')
    group.add_argument('--execute', action='store_true',
                       help='Execute migration (will modify database)')
    group.add_argument('--validate-only', action='store_true',
                       help='Run validation checks only')
    group.add_argument('--count', action='store_true',
                       help='Check current row counts')

    parser.add_argument('--backup', action='store_true',
                        help='Create backup before migration')
    parser.add_argument('--skip-validation', action='store_true',
                        help='Skip post-migration validation')

    args = parser.parse_args()

    # Validation-only mode
    if args.validate_only:
        success = run_validation_only()
        sys.exit(0 if success else 1)

    # Row count check
    if args.count:
        check_row_counts()
        sys.exit(0)

    # Migration mode
    engine = MigrationEngine(dry_run=args.dry_run)

    # Backup if requested
    if args.backup and args.execute:
        backup_file = engine.backup_schema()
        if not backup_file:
            logger.error("Backup failed, aborting migration")
            sys.exit(1)

    # Execute migration
    success = engine.execute()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
