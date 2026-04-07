#!/usr/bin/env python3
"""
Aktienvergleich - Stock Index Data Collector
Main entry point for the scraper.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
from src.logging_config import setup_logging

logger = setup_logging('aktienvergleich')

from src.index_loader import load_single_index, load_all_indexes
from src.supabase_client import get_client
from config.indices import INDEX_CONFIG, get_all_index_names


def setup_environment():
    """Setup and validate environment."""
    # Load .env if exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)

    # Validate required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f'Missing required environment variables: {", ".join(missing)}')
        logger.error('Please create a .env file with these variables:')
        logger.error('  SUPABASE_URL=https://your-project.supabase.co')
        logger.error('  SUPABASE_KEY=your-anon-key-here')
        return False

    return True


def test_database_connection():
    """Test connection to Supabase."""
    logger.info('Testing Supabase connection...')
    try:
        client = get_client()
        if client.health_check():
            logger.info('✓ Supabase connection successful')
            return True
        else:
            logger.error('✗ Supabase health check failed')
            return False
    except Exception as e:
        logger.error(f'✗ Supabase connection error: {e}')
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Aktienvergleich - Stock Index Data Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Load single index
  python main.py --index DAX

  # Load multiple indexes
  python main.py --indexes DAX,MDAX,SPX

  # Load all indexes
  python main.py --all

  # Load with limit (for testing)
  python main.py --index DAX --limit 5

  # Verbose output
  python main.py --index DAX -v
        ''',
    )

    parser.add_argument(
        '--index',
        type=str,
        help='Load a single index (e.g., DAX, SPX, STOXX50)',
    )
    parser.add_argument(
        '--indexes',
        type=str,
        help='Load multiple indexes (comma-separated, e.g., DAX,MDAX,SPX)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Load all configured indexes',
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of companies per index (for testing)',
    )
    parser.add_argument(
        '--region',
        type=str,
        choices=['Germany', 'Europe', 'USA'],
        help='Load all indexes in a region',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test without database writes',
    )

    args = parser.parse_args()

    # Setup logging verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info('=' * 60)
    logger.info('Aktienvergleich - Stock Index Data Collector')
    logger.info(f'Started at: {datetime.now().isoformat()}')
    logger.info('=' * 60)

    # Setup environment
    if not setup_environment():
        return 1

    # Test database connection
    if not args.dry_run:
        if not test_database_connection():
            return 1

    # Determine which indexes to load
    indexes_to_load = []

    if args.index:
        indexes_to_load = [args.index]
    elif args.indexes:
        indexes_to_load = [idx.strip() for idx in args.indexes.split(',')]
    elif args.region:
        indexes_to_load = [
            name for name, config in INDEX_CONFIG.items()
            if config.get('region') == args.region
        ]
    elif args.all:
        indexes_to_load = get_all_index_names()
    else:
        parser.print_help()
        return 0

    # Validate indexes
    valid_indexes = []
    for idx in indexes_to_load:
        if idx not in INDEX_CONFIG:
            logger.warning(f'Unknown index: {idx}')
        else:
            valid_indexes.append(idx)

    if not valid_indexes:
        logger.error('No valid indexes to load')
        return 1

    logger.info(f'Loading {len(valid_indexes)} index(es): {", ".join(valid_indexes)}')

    # Load indexes
    results = {}
    total_loaded = 0

    for index_name in valid_indexes:
        logger.info(f'\n--- Loading {index_name} ---')
        try:
            companies = load_single_index(index_name)

            # Apply limit if specified
            if args.limit:
                companies = companies[: args.limit]

            results[index_name] = len(companies)
            total_loaded += len(companies)

            logger.info(f'✓ {index_name}: {len(companies)} companies')

        except Exception as e:
            logger.error(f'✗ {index_name}: {e}')
            results[index_name] = 0

    # Summary
    logger.info('\n' + '=' * 60)
    logger.info('Summary')
    logger.info('=' * 60)
    for index_name, count in results.items():
        status = '✓' if count > 0 else '✗'
        logger.info(f'{status} {index_name}: {count} companies')
    logger.info(f'\nTotal companies loaded: {total_loaded}')
    logger.info(f'Completed at: {datetime.now().isoformat()}')
    logger.info('=' * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
