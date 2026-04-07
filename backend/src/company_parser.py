"""Main company parser dispatcher."""

import logging
from typing import List, Optional, Dict

from config.indices import get_index_config
from .parsers.base_parser import CompanyParser
from .parsers.finanzen_net_parser import FinanzenNetParser
from .parsers.yahoo_finance_parser import YahooFinanceParser
from .parsers.european_parser import EuropeanParser
from .supabase_client import get_client

logger = logging.getLogger(__name__)


class CompanyParserDispatcher:
    """Dispatcher for parsing company estimates from appropriate sources."""

    def __init__(self):
        """Initialize dispatcher."""
        self.db_client = get_client()
        self.parsers: Dict[str, CompanyParser] = {}

    def get_parser(
        self, company: dict, index_name: str
    ) -> Optional[CompanyParser]:
        """
        Get or create a parser for the company.

        Args:
            company: Company dictionary
            index_name: Name of the index

        Returns:
            Appropriate parser instance or None
        """
        config = get_index_config(index_name)
        if not config:
            logger.error(f'Index {index_name} not found')
            return None

        data_source = config.get('data_source', '')

        # Select appropriate parser based on data source
        if data_source == 'finanzen_net':
            return FinanzenNetParser(company, config)
        elif data_source == 'yahoo_finance':
            region = config.get('region', '')
            if region == 'Europe':
                return EuropeanParser(company, config)
            else:
                return YahooFinanceParser(company, config)
        else:
            logger.warning(f'Unknown data source {data_source} for {index_name}')
            return None

    def parse_company_estimates(
        self, company: dict, index_name: str
    ) -> Dict[int, dict]:
        """
        Parse all estimates for a company.

        Args:
            company: Company dictionary
            index_name: Name of the index

        Returns:
            Dictionary of fiscal_year -> estimate_data
        """
        parser = self.get_parser(company, index_name)
        if not parser:
            logger.error(
                f'Could not create parser for {company.get("title")} in {index_name}'
            )
            return {}

        try:
            estimates = parser.get_estimates()
            valid_estimates = parser.filter_valid_estimates()

            if valid_estimates:
                logger.info(
                    f'Parsed {len(valid_estimates)} fiscal years for {company.get("title")}'
                )
            else:
                logger.warning(
                    f'No valid estimates for {company.get("title")}'
                )

            return valid_estimates

        except Exception as e:
            logger.error(
                f'Error parsing estimates for {company.get("title")}: {e}'
            )
            return {}

    def parse_company_and_store(
        self, company: dict, index_name: str, company_id: str
    ) -> int:
        """
        Parse company estimates and store in database.

        Args:
            company: Company dictionary
            index_name: Name of the index
            company_id: UUID of the company from database

        Returns:
            Number of estimates stored
        """
        logger.debug(f'Parsing estimates for {company.get("title")}')

        # Parse estimates
        estimates = self.parse_company_estimates(company, index_name)

        if not estimates:
            logger.warning(
                f'No estimates found for {company.get("title")}'
            )
            self.db_client.update_company_status(
                company_id, 'partial', 'No estimates found'
            )
            return 0

        # Store each estimate in database
        stored = 0
        for fiscal_year, estimate_data in estimates.items():
            success = self.db_client.upsert_estimate(
                company_id, fiscal_year, estimate_data
            )
            if success:
                stored += 1
            else:
                logger.warning(
                    f'Failed to store estimate for {company.get("title")} {fiscal_year}'
                )

        # Update company status
        if stored == len(estimates):
            status = 'success'
        elif stored > 0:
            status = 'partial'
        else:
            status = 'failed'

        self.db_client.update_company_status(company_id, status)

        logger.info(
            f'Stored {stored}/{len(estimates)} estimates for {company.get("title")}'
        )
        return stored

    def parse_and_store_index_companies(
        self, index_id: str, index_name: str
    ) -> tuple[int, int]:
        """
        Parse and store estimates for all companies in an index.

        Args:
            index_id: UUID of the index
            index_name: Name of the index

        Returns:
            Tuple of (total_estimates_stored, total_companies)
        """
        logger.info(f'Parsing and storing estimates for {index_name}')

        # Get all companies in the index
        companies = self.db_client.get_companies_by_index(index_id)

        if not companies:
            logger.warning(f'No companies found for {index_name}')
            return 0, 0

        logger.info(f'Parsing {len(companies)} companies in {index_name}')

        total_stored = 0
        for company in companies:
            try:
                stored = self.parse_company_and_store(
                    company, index_name, company['id']
                )
                total_stored += stored
            except Exception as e:
                logger.error(
                    f'Error processing {company.get("title")}: {e}'
                )
                self.db_client.update_company_status(
                    company['id'], 'failed', str(e)
                )

        logger.info(
            f'Stored {total_stored} total estimates for {len(companies)} companies in {index_name}'
        )
        return total_stored, len(companies)


def parse_single_company(
    company: dict, index_name: str
) -> Dict[int, dict]:
    """
    Convenience function to parse a single company.

    Args:
        company: Company dictionary
        index_name: Name of the index

    Returns:
        Dictionary of fiscal_year -> estimate_data
    """
    dispatcher = CompanyParserDispatcher()
    return dispatcher.parse_company_estimates(company, index_name)


def parse_index_companies(index_id: str, index_name: str) -> tuple[int, int]:
    """
    Convenience function to parse all companies in an index.

    Args:
        index_id: UUID of the index
        index_name: Name of the index

    Returns:
        Tuple of (estimates_stored, companies_processed)
    """
    dispatcher = CompanyParserDispatcher()
    return dispatcher.parse_and_store_index_companies(index_id, index_name)
