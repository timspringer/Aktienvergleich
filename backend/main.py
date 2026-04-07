#!/usr/bin/env python3
"""
Aktienvergleich - Stock Index Data Collector
Main entry point for the scraper.

Complete pipeline: Index Loading → Company Parsing → CAGR Calculation → Database Storage
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

from src.pipeline import run_pipeline
from src.supabase_client import get_client
from config.indices import INDEX_CONFIG, get_all_index_names


def setup_environment():
    """Setup and validate environment."""
    # Load .env if exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass

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
        description='Aktienvergleich - Stock Index Data Collector (Complete Pipeline)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Full pipeline for single index
  python main.py --index DAX

  # Full pipeline for multiple indexes
  python main.py --indexes DAX,MDAX,SPX

  # Process all indexes
  python main.py --all

  # Process by region
  python main.py --region Germany

  # Test with limit (fewer companies)
  python main.py --index DAX --limit 5

  # Verbose output
  python main.py --index DAX -v

Pipeline Stages:
  1. Load index members from data source
  2. Parse company estimate pages
  3. Extract financial metrics
  4. Normalize data formats
  5. Calculate CAGR values
  6. Validate data quality
  7. Store to Supabase database
        ''',
    )

    parser.add_argument(
        '--index',
        type=str,
        help='Process single index (e.g., DAX, SPX, STOXX50)',
    )
    parser.add_argument(
        '--indexes',
        type=str,
        help='Process multiple indexes (comma-separated, e.g., DAX,MDAX,SPX)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all configured indexes',
    )
    parser.add_argument(
        '--region',
        type=str,
        choices=['Germany', 'Europe', 'USA'],
        help='Process all indexes in a region',
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of companies per index (for testing)',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output (debug logging)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test without database writes (not fully implemented)',
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip initial validation checks',
    )

    args = parser.parse_args()

    # Setup logging verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info('=' * 70)
    logger.info('Aktienvergleich - Stock Index Data Collector')
    logger.info('Complete Data Pipeline')
    logger.info(f'Started at: {datetime.now().isoformat()}')
    logger.info('=' * 70)

    # Setup environment
    if not setup_environment():
        return 1

    # Test database connection
    if not args.skip_validation:
        if not test_database_connection():
            return 1

    # Determine which indexes to process
    indexes_to_process = []

    if args.index:
        indexes_to_process = [args.index]
    elif args.indexes:
        indexes_to_process = [idx.strip() for idx in args.indexes.split(',')]
    elif args.region:
        indexes_to_process = [
            name for name, config in INDEX_CONFIG.items()
            if config.get('region') == args.region
        ]
    elif args.all:
        indexes_to_process = get_all_index_names()
    else:
        # If no arguments provided, process all indexes automatically
        logger.info('No specific indexes specified, processing all configured indexes...')
        indexes_to_process = get_all_index_names()

    # Validate indexes
    valid_indexes = []
    for idx in indexes_to_process:
        if idx not in INDEX_CONFIG:
            logger.warning(f'Unknown index: {idx}')
        else:
            valid_indexes.append(idx)

    if not valid_indexes:
        logger.error('No valid indexes to process')
        return 1

    logger.info(f'Processing {len(valid_indexes)} index(es): {", ".join(valid_indexes)}')
    logger.info('Pipeline will:')
    logger.info('  1. Load index members')
    logger.info('  2. Parse company estimates')
    logger.info('  3. Extract financial metrics')
    logger.info('  4. Calculate CAGR values')
    logger.info('  5. Store to database')

    # Run the pipeline
    logger.info('\n' + '=' * 70)
    logger.info('Starting Data Pipeline')
    logger.info('=' * 70)

    try:
        results = run_pipeline(indexes=valid_indexes)

        # Print results
        logger.info('\n' + '=' * 70)
        logger.info('Pipeline Results')
        logger.info('=' * 70)

        total_companies = 0
        total_estimates = 0
        total_metrics = 0

        for index_name, (companies, estimates, metrics) in results.items():
            logger.info(
                f'{index_name}: {companies} companies, {estimates} estimates, {metrics} metrics'
            )
            total_companies += companies
            total_estimates += estimates
            total_metrics += metrics

        logger.info('-' * 70)
        logger.info(f'Total: {total_companies} companies, {total_estimates} estimates, {total_metrics} metrics')
        logger.info('=' * 70)

        logger.info(f'Completed at: {datetime.now().isoformat()}')

        return 0

    except KeyboardInterrupt:
        logger.info('\nPipeline interrupted by user')
        return 130
    except Exception as e:
        logger.error(f'Pipeline failed: {e}', exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
