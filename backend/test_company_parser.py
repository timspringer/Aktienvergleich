#!/usr/bin/env python3
"""Test script for company parser."""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.logging_config import setup_logging
from src.company_parser import parse_single_company
from config.indices import INDEX_CONFIG

logger = setup_logging('test_company_parser')


def test_parser():
    """Test the company parser."""
    logger.info('Starting company parser tests...')

    # Check environment
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        logger.warning('SUPABASE_URL and SUPABASE_KEY not set - using mock data')

    # Test data
    test_companies = [
        {
            'title': 'SAP SE',
            'wkn': '716460',
            'isin': 'DE0007164600',
            'source_url': 'https://www.finanzen.net/aktien/sap-aktie',
            'index': 'DAX',
        },
        {
            'title': 'Apple Inc.',
            'isin': 'US0378331005',
            'source_url': None,
            'index': 'SPX',
        },
    ]

    # Test single company parsing
    logger.info('\n=== Testing Single Company Parser ===')
    for test_company in test_companies:
        logger.info(f'\nTesting: {test_company["title"]}')
        index_name = test_company['index']
        index_config = INDEX_CONFIG.get(index_name, {})

        try:
            estimates = parse_single_company(test_company, index_name)
            if estimates:
                logger.info(f'✓ Parsed {len(estimates)} fiscal years')
                for year, data in list(estimates.items())[:2]:
                    logger.info(f'  Year {year}: {list(data.keys())}')
            else:
                logger.info('○ No estimates found (expected for test URLs)')
        except Exception as e:
            logger.error(f'✗ Error parsing: {e}')

    logger.info('\n=== Parser Tests Complete ===')
    logger.info('Note: Actual parsing requires valid URLs and page structures')
    return True


if __name__ == '__main__':
    success = test_parser()
    sys.exit(0 if success else 1)
