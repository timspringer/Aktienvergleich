"""
Import financial estimates from CSV for German DAX stocks.
Allows progressive loading of data extracted by ChatGPT.

Usage:
  python -m src.import_estimates --file data.csv --index DAX
  python -m src.import_estimates --file data.csv --index DAX --skip-validation
"""

import sys
import os
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging_config import setup_logging
from src.supabase_client import get_client
from src.calculations import calculate_cagr_for_metric, check_data_completeness
from config.indices import get_index_config

logger = setup_logging('import_estimates')


class EstimatesImporter:
    """Import financial estimates from CSV into Supabase."""

    def __init__(self):
        """Initialize importer."""
        self.db_client = get_client()
        self.stats = {
            'companies_created': 0,
            'companies_updated': 0,
            'estimates_inserted': 0,
            'metrics_calculated': 0,
            'errors': [],
        }

    def validate_csv_row(self, row: Dict, index_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate CSV row has required fields.

        Args:
            row: Dictionary from CSV
            index_name: Name of index being imported

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['isin', 'title', 'fiscal_year']

        for field in required_fields:
            if field not in row or not row[field]:
                return False, f'Missing required field: {field}'

        # Validate fiscal_year is integer
        try:
            int(row['fiscal_year'])
        except (ValueError, TypeError):
            return False, f'fiscal_year must be integer, got: {row["fiscal_year"]}'

        return True, None

    def normalize_numeric_value(self, value: str) -> Optional[float]:
        """
        Normalize numeric values from various formats.

        Handles:
        - German format: "1.234,56" → 1234.56
        - US format: "1,234.56" → 1234.56
        - Returns None for "NV", empty, or invalid values

        Args:
            value: String value from CSV

        Returns:
            Float value or None if invalid/NV
        """
        if not value or value.strip().upper() == 'NV':
            return None

        value = value.strip()

        # Count dots and commas
        dot_count = value.count('.')
        comma_count = value.count(',')

        try:
            # German format: 1.234,56 (last comma is decimal)
            if comma_count == 1 and dot_count >= 1:
                value = value.replace('.', '').replace(',', '.')
            # US format or variations
            elif comma_count == 1 and dot_count == 0:
                # Could be 1,234 or 1,234 (need context)
                # Default to comma as thousands separator
                value = value.replace(',', '')
            elif dot_count == 1 and comma_count == 0:
                # US format 1,234.56 already correct
                pass
            elif dot_count >= 1 and comma_count >= 1:
                # Mixed format - use last separator as decimal
                if value.rfind(',') > value.rfind('.'):
                    value = value.replace('.', '').replace(',', '.')
                else:
                    value = value.replace(',', '')

            return float(value)
        except (ValueError, AttributeError):
            return None

    def get_or_create_company(
        self,
        index_id: str,
        isin: str,
        title: str,
        source_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Get existing company or create new one.

        Args:
            index_id: Index UUID
            isin: Company ISIN
            title: Company title
            source_url: Optional source URL

        Returns:
            Company ID or None if error
        """
        # Check if company exists
        existing = self.db_client.get_company_by_isin(isin)
        if existing:
            logger.info(f'Found existing company: {title} (ISIN: {isin})')
            return existing['id']

        # Create new company
        try:
            company_data = {
                'index_id': index_id,
                'isin': isin,
                'title': title,
                'source_url': source_url or 'manual_import',
                'last_scrape_status': 'manual_import',
                'last_updated': datetime.utcnow().isoformat(),
            }

            response = self.db_client.client.table('companies').insert(
                company_data
            ).execute()

            if response.data:
                company_id = response.data[0]['id']
                logger.info(f'Created company: {title} (ISIN: {isin})')
                self.stats['companies_created'] += 1
                return company_id
            else:
                logger.error(f'Failed to create company {title}')
                return None

        except Exception as e:
            logger.error(f'Error creating company {title}: {e}')
            self.stats['errors'].append(f'Create company {title}: {str(e)}')
            return None

    def import_csv_file(
        self,
        csv_file: Path,
        index_name: str,
        skip_validation: bool = False
    ) -> bool:
        """
        Import estimates from CSV file.

        Expected CSV columns:
        - isin (required)
        - title (required)
        - fiscal_year (required)
        - revenue
        - dividend
        - dividend_yield_percent
        - eps
        - pe_ratio
        - avg_price_target
        - currency (optional, defaults to EUR)
        - source_url (optional)

        Args:
            csv_file: Path to CSV file
            index_name: Index name (e.g., 'DAX')
            skip_validation: Skip initial validation checks

        Returns:
            True if successful
        """
        logger.info('=' * 70)
        logger.info(f'Importing estimates from: {csv_file}')
        logger.info(f'Index: {index_name}')
        logger.info('=' * 70)

        # Validate index
        index_config = get_index_config(index_name)
        if not index_config:
            logger.error(f'Unknown index: {index_name}')
            return False

        # Get or validate index record
        index_record = self.db_client.get_index(index_name)
        if not index_record:
            logger.error(f'Index {index_name} not found in database')
            logger.info('Ensure index exists in database before importing')
            return False

        index_id = index_record['id']
        logger.info(f'Using index ID: {index_id}')

        # Read CSV file
        if not csv_file.exists():
            logger.error(f'CSV file not found: {csv_file}')
            return False

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                logger.error('CSV file is empty')
                return False

            logger.info(f'Read {len(rows)} rows from CSV')

        except Exception as e:
            logger.error(f'Error reading CSV file: {e}')
            return False

        # Group estimates by company
        companies_data: Dict[str, Dict] = {}

        for row_idx, row in enumerate(rows, 2):  # Start at 2 (headers are row 1)
            try:
                # Validate row
                is_valid, error_msg = self.validate_csv_row(row, index_name)
                if not is_valid:
                    logger.warning(f'Row {row_idx}: {error_msg}')
                    self.stats['errors'].append(f'Row {row_idx}: {error_msg}')
                    continue

                isin = row['isin'].strip().upper()
                title = row['title'].strip()
                fiscal_year = int(row['fiscal_year'])

                # Initialize company entry if needed
                if isin not in companies_data:
                    companies_data[isin] = {
                        'title': title,
                        'estimates': {}
                    }

                # Parse numeric fields
                estimate_data = {
                    'fiscal_year': fiscal_year,
                    'revenue_currency': row.get('currency', 'EUR').upper(),
                }

                # Optional numeric fields
                numeric_fields = [
                    'revenue_amount',
                    'dividend',
                    'dividend_yield_percent',
                    'eps',
                    'pe_ratio',
                    'avg_price_target',
                ]

                for field in numeric_fields:
                    if field in row and row[field]:
                        value = self.normalize_numeric_value(row[field])
                        if value is not None:
                            estimate_data[field] = value

                # Add source URL if provided
                if 'source_url' in row and row['source_url']:
                    estimate_data['source_url'] = row['source_url']

                companies_data[isin]['estimates'][fiscal_year] = estimate_data

            except Exception as e:
                logger.warning(f'Row {row_idx}: Error processing row: {e}')
                self.stats['errors'].append(f'Row {row_idx}: {str(e)}')
                continue

        if not companies_data:
            logger.error('No valid company data found in CSV')
            return False

        logger.info(f'Parsed {len(companies_data)} unique companies')

        # Import each company and its estimates
        for isin, company_info in companies_data.items():
            try:
                title = company_info['title']
                estimates = company_info['estimates']

                logger.info(f'\nProcessing: {title} (ISIN: {isin})')
                logger.info(f'  Fiscal years: {sorted(estimates.keys())}')

                # Get or create company
                company_id = self.get_or_create_company(index_id, isin, title)
                if not company_id:
                    continue

                # Insert estimates
                for fiscal_year, estimate_data in estimates.items():
                    success = self.db_client.upsert_estimate(
                        company_id, fiscal_year, estimate_data
                    )
                    if success:
                        self.stats['estimates_inserted'] += 1

                # Calculate and store metrics
                stored_metrics = self._calculate_and_store_metrics(
                    company_id, estimates
                )
                if stored_metrics:
                    self.stats['metrics_calculated'] += 1

                # Update company status
                self.db_client.update_company_status(company_id, 'success')

            except Exception as e:
                logger.error(f'Error processing {title}: {e}')
                self.stats['errors'].append(f'{title}: {str(e)}')

        self.print_summary()
        return True

    def _calculate_and_store_metrics(
        self,
        company_id: str,
        estimates: Dict[int, dict]
    ) -> bool:
        """
        Calculate metrics from estimates and store to database.

        Args:
            company_id: Company UUID
            estimates: Dictionary of fiscal_year -> estimate_data

        Returns:
            True if metrics stored successfully
        """
        try:
            metrics_data = {}

            if not estimates:
                return False

            metrics_to_calculate = [
                'revenue_amount',
                'dividend',
                'dividend_yield_percent',
                'eps',
                'pe_ratio',
            ]

            # Build values_by_year for each metric
            data_completeness = {}

            for metric in metrics_to_calculate:
                values_by_year = {
                    year: est.get(metric)
                    for year, est in estimates.items()
                }

                # Calculate CAGR
                cagr = calculate_cagr_for_metric(values_by_year)
                if cagr and cagr != 'NV':
                    metrics_data[f'{metric}_cagr_percent'] = float(cagr)
                else:
                    metrics_data[f'{metric}_cagr_percent'] = None

                # Check completeness
                is_complete, _, _ = check_data_completeness(values_by_year)
                data_completeness[metric] = is_complete

            # Get fiscal year range
            fiscal_years = sorted(estimates.keys())
            metrics_data['first_estimate_year'] = fiscal_years[0]
            metrics_data['last_estimate_year'] = fiscal_years[-1]
            metrics_data['estimate_count'] = len(fiscal_years)
            metrics_data['data_completeness'] = data_completeness

            # Store metrics
            return self.db_client.insert_metrics(company_id, metrics_data)

        except Exception as e:
            logger.error(f'Error calculating metrics for {company_id}: {e}')
            return False

    def print_summary(self):
        """Print import summary."""
        logger.info('\n' + '=' * 70)
        logger.info('Import Summary')
        logger.info('=' * 70)
        logger.info(f'Companies created: {self.stats["companies_created"]}')
        logger.info(f'Companies updated: {self.stats["companies_updated"]}')
        logger.info(f'Estimates inserted: {self.stats["estimates_inserted"]}')
        logger.info(f'Metrics calculated: {self.stats["metrics_calculated"]}')

        if self.stats['errors']:
            logger.info(f'\nWarnings/Errors ({len(self.stats["errors"])}):')
            for error in self.stats['errors'][:10]:
                logger.warning(f'  - {error}')
            if len(self.stats['errors']) > 10:
                logger.warning(
                    f'  ... and {len(self.stats["errors"]) - 10} more'
                )

        logger.info('=' * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Import financial estimates from CSV into Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Import DAX data
  python -m src.import_estimates --file dax_estimates.csv --index DAX

  # Import with custom source URL
  python -m src.import_estimates --file dax_data.csv --index DAX

CSV Format:
  isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent,eps,pe_ratio,currency,source_url
  DE0005140008,Deutsche Telekom,2024,120000,0.70,2.5,2.50,15.5,EUR,https://...
  DE0008469008,DAX Company,2024,50000,0.50,1.2,1.80,20.0,EUR,https://...
        ''',
    )

    parser.add_argument(
        '--file',
        type=Path,
        required=True,
        help='Path to CSV file',
    )
    parser.add_argument(
        '--index',
        type=str,
        required=True,
        help='Index name (e.g., DAX, MDAX)',
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation checks',
    )

    args = parser.parse_args()

    logger.info('=' * 70)
    logger.info('Financial Estimates Importer')
    logger.info(f'Started at: {datetime.now().isoformat()}')
    logger.info('=' * 70)

    # Setup environment
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass

    # Validate environment
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f'Missing environment variables: {", ".join(missing)}')
        return 1

    # Run import
    importer = EstimatesImporter()
    success = importer.import_csv_file(
        args.file,
        args.index,
        skip_validation=args.skip_validation
    )

    logger.info(f'Completed at: {datetime.now().isoformat()}')

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
