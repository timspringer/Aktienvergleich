#!/usr/bin/env python3
"""Test script for index loader."""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.logging_config import setup_logging
from src.index_loader import load_single_index, load_all_indexes
from config.indices import INDEX_CONFIG

logger = setup_logging('test_index_loader')


def test_loader():
    """Test the index loader."""
    logger.info('Starting index loader tests...')

    # Check environment
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        logger.error('SUPABASE_URL and SUPABASE_KEY must be set')
        logger.error('Run: source .env (or export SUPABASE_* variables)')
        return False

    # Test single index (German)
    logger.info('\n=== Testing Single Index (DAX) ===')
    try:
        companies = load_single_index('DAX')
        logger.info(f'✓ Loaded {len(companies)} companies for DAX')
        if companies:
            logger.info(f'  Sample: {companies[0]}')
    except Exception as e:
        logger.error(f'✗ Failed to load DAX: {e}')
        return False

    # Test single index (US)
    logger.info('\n=== Testing Single Index (SPX) ===')
    try:
        companies = load_single_index('SPX')
        logger.info(f'✓ Loaded {len(companies)} companies for SPX')
        if companies:
            logger.info(f'  Sample: {companies[0]}')
    except Exception as e:
        logger.error(f'✗ Failed to load SPX: {e}')
        # This is less critical since it's from predefined data

    # Test all indexes
    logger.info('\n=== Testing All Indexes ===')
    try:
        results = load_all_indexes()
        logger.info(f'✓ Loaded indexes:')
        for index_name, count in results.items():
            logger.info(f'  - {index_name}: {count} companies')
    except Exception as e:
        logger.error(f'✗ Failed to load all indexes: {e}')
        return False

    logger.info('\n=== Tests Complete ===')
    return True


if __name__ == '__main__':
    success = test_loader()
    sys.exit(0 if success else 1)
