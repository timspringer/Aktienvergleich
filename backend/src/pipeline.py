"""Main data pipeline orchestrator."""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config.indices import get_index_config
from .index_loader import IndexLoaderDispatcher
from .company_parser import CompanyParserDispatcher
from .calculations import calculate_cagr_for_metric, check_data_completeness
from .supabase_client import get_client

logger = logging.getLogger(__name__)


class DataPipeline:
    """Complete data pipeline orchestrating all scraping and processing steps."""

    def __init__(self):
        """Initialize pipeline."""
        self.db_client = get_client()
        self.index_loader = IndexLoaderDispatcher()
        self.company_parser = CompanyParserDispatcher()
        self.stats = {
            'indexes_processed': 0,
            'companies_loaded': 0,
            'estimates_parsed': 0,
            'metrics_calculated': 0,
            'errors': [],
        }

    def process_index(self, index_name: str) -> Tuple[int, int, int]:
        """
        Process a complete index through the pipeline.

        Args:
            index_name: Name of the index (e.g., 'DAX')

        Returns:
            Tuple of (companies_processed, estimates_parsed, metrics_stored)
        """
        logger.info(f'\n{"="*60}')
        logger.info(f'Processing Index: {index_name}')
        logger.info(f'{"="*60}')

        # Get index config
        config = get_index_config(index_name)
        if not config:
            logger.error(f'Index {index_name} not found in configuration')
            self.stats['errors'].append(f'Unknown index: {index_name}')
            return 0, 0, 0

        # Step 1: Load index members
        logger.info(f'\nStep 1: Loading index members...')
        companies = self.index_loader.load_index_members(index_name)
        if not companies:
            logger.error(f'Failed to load companies for {index_name}')
            self.stats['errors'].append(
                f'{index_name}: Failed to load index members'
            )
            return 0, 0, 0

        logger.info(f'✓ Loaded {len(companies)} companies')
        self.stats['companies_loaded'] += len(companies)

        # Get index record from database
        index_record = self.db_client.get_index(index_name)
        if not index_record:
            logger.error(f'Index {index_name} not found in database')
            return 0, 0, 0

        index_id = index_record['id']

        # Step 2: Process each company
        logger.info(f'\nStep 2: Parsing company estimates...')
        total_estimates = 0
        total_metrics = 0

        for idx, company in enumerate(companies, 1):
            logger.debug(
                f'[{idx}/{len(companies)}] Processing {company.get("title")}'
            )

            company_id = company.get('id')
            if not company_id:
                logger.warning(f'Company {company.get("title")} has no ID')
                continue

            try:
                # Parse estimates
                estimates = self.company_parser.parse_company_estimates(
                    company, index_name
                )

                if estimates:
                    # Store estimates
                    for fiscal_year, estimate_data in estimates.items():
                        success = self.db_client.upsert_estimate(
                            company_id, fiscal_year, estimate_data
                        )
                        if success:
                            total_estimates += 1

                    # Calculate and store metrics
                    stored_metrics = self._calculate_and_store_metrics(
                        company_id, estimates
                    )
                    if stored_metrics:
                        total_metrics += 1

                    # Update company status
                    self.db_client.update_company_status(
                        company_id, 'success'
                    )

                else:
                    # No estimates found
                    self.db_client.update_company_status(
                        company_id, 'partial', 'No estimates found'
                    )

            except Exception as e:
                logger.error(
                    f'Error processing {company.get("title")}: {e}'
                )
                self.db_client.update_company_status(
                    company_id, 'failed', str(e)
                )
                self.stats['errors'].append(
                    f'{company.get("title")}: {str(e)}'
                )

        # Update index record with member count
        try:
            self.db_client.client.table('indices').update(
                {
                    'member_count': len(companies),
                    'last_updated': datetime.utcnow().isoformat(),
                }
            ).eq('id', index_id).execute()
        except Exception as e:
            logger.warning(f'Failed to update index record: {e}')

        self.stats['estimates_parsed'] += total_estimates
        self.stats['metrics_calculated'] += total_metrics
        self.stats['indexes_processed'] += 1

        logger.info(f'✓ Parsed {total_estimates} estimates')
        logger.info(f'✓ Calculated {total_metrics} metric sets')

        return len(companies), total_estimates, total_metrics

    def _calculate_and_store_metrics(
        self, company_id: str, estimates: Dict[int, dict]
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

            # Extract metric names from first estimate
            if not estimates:
                return False

            first_estimate = next(iter(estimates.values()))
            metrics_to_calculate = [
                'revenue',
                'dividend',
                'dividend_yield',
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

    def process_all_indexes(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Process all configured indexes.

        Returns:
            Dictionary mapping index_name -> (companies, estimates, metrics)
        """
        from config.indices import get_all_index_names

        logger.info('Starting complete data pipeline')
        logger.info(f'Timestamp: {datetime.utcnow().isoformat()}')

        results = {}
        for index_name in get_all_index_names():
            try:
                companies, estimates, metrics = self.process_index(index_name)
                results[index_name] = (companies, estimates, metrics)
            except Exception as e:
                logger.error(f'Fatal error processing {index_name}: {e}')
                self.stats['errors'].append(f'{index_name}: {str(e)}')
                results[index_name] = (0, 0, 0)

        return results

    def process_indexes_by_region(self, region: str) -> Dict[str, Tuple[int, int, int]]:
        """
        Process all indexes in a region.

        Args:
            region: Region name ('Germany', 'Europe', 'USA')

        Returns:
            Dictionary mapping index_name -> (companies, estimates, metrics)
        """
        from config.indices import INDEX_CONFIG

        logger.info(f'Processing {region} indexes')

        results = {}
        for index_name, config in INDEX_CONFIG.items():
            if config.get('region') == region:
                try:
                    companies, estimates, metrics = self.process_index(
                        index_name
                    )
                    results[index_name] = (companies, estimates, metrics)
                except Exception as e:
                    logger.error(f'Error processing {index_name}: {e}')
                    self.stats['errors'].append(f'{index_name}: {str(e)}')
                    results[index_name] = (0, 0, 0)

        return results

    def get_stats(self) -> Dict:
        """Get pipeline execution statistics."""
        return self.stats

    def print_summary(self):
        """Print execution summary."""
        logger.info(f'\n{"="*60}')
        logger.info('Pipeline Summary')
        logger.info(f'{"="*60}')
        logger.info(f'Indexes processed: {self.stats["indexes_processed"]}')
        logger.info(f'Companies loaded: {self.stats["companies_loaded"]}')
        logger.info(f'Estimates parsed: {self.stats["estimates_parsed"]}')
        logger.info(f'Metrics calculated: {self.stats["metrics_calculated"]}')

        if self.stats['errors']:
            logger.info(f'\nErrors ({len(self.stats["errors"])}):')
            for error in self.stats['errors'][:10]:  # Show first 10
                logger.error(f'  - {error}')
            if len(self.stats['errors']) > 10:
                logger.error(f'  ... and {len(self.stats["errors"]) - 10} more')

        logger.info(f'{"="*60}')


def run_pipeline(
    indexes: Optional[List[str]] = None,
    region: Optional[str] = None,
    all_indexes: bool = False,
) -> Dict[str, Tuple[int, int, int]]:
    """
    Run the data pipeline.

    Args:
        indexes: List of index names to process
        region: Process all indexes in a region
        all_indexes: Process all configured indexes

    Returns:
        Dictionary of results
    """
    pipeline = DataPipeline()

    if all_indexes:
        results = pipeline.process_all_indexes()
    elif region:
        results = pipeline.process_indexes_by_region(region)
    elif indexes:
        results = {}
        for index_name in indexes:
            companies, estimates, metrics = pipeline.process_index(index_name)
            results[index_name] = (companies, estimates, metrics)
    else:
        logger.error('No indexes specified')
        return {}

    pipeline.print_summary()
    return results
