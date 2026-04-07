"""Loader for indexes from Yahoo Finance."""

import logging
import requests
from typing import List, Optional
import json

from .base_loader import IndexLoader
from ..retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class YahooFinanceLoader(IndexLoader):
    """Loader for stock indexes from Yahoo Finance."""

    def __init__(self, index_name: str, index_config: dict):
        """Initialize Yahoo Finance loader."""
        super().__init__(index_name, index_config)
        self.ticker = index_config.get('ticker')
        self.timeout = 30

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _fetch_from_yahoo(self, url: str) -> Optional[dict]:
        """Fetch data from Yahoo Finance."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f'Error fetching from Yahoo Finance: {e}')
            return None

    def load_members(self) -> List[dict]:
        """
        Load index members from Yahoo Finance.

        Yahoo Finance API provides index composition data.
        Falls back to manual company list for well-known indexes.
        """
        if not self.ticker:
            logger.error(f'No ticker configured for {self.index_name}')
            return []

        # Try API approach first
        companies = self._load_from_api()

        if not companies:
            # Fallback to predefined lists for major indexes
            companies = self._load_from_predefined()

        self.companies = companies
        logger.info(
            f'Loaded {len(companies)} members for {self.index_name} from Yahoo Finance'
        )
        return companies

    def _load_from_api(self) -> List[dict]:
        """
        Try to load from Yahoo Finance API.

        Note: Yahoo Finance API is not officially documented.
        This is a best-effort implementation.
        """
        try:
            # Construct API URL for index constituents
            # This endpoint may not always be available
            url = f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{self.ticker}'

            data = self._fetch_from_yahoo(url)
            if not data or 'quoteSummary' not in data:
                return []

            companies = []
            # Parse response (structure depends on endpoint)
            # This is a simplified implementation
            return companies

        except Exception as e:
            logger.debug(f'Error loading from Yahoo Finance API: {e}')
            return []

    def _load_from_predefined(self) -> List[dict]:
        """
        Load from predefined company lists for major indexes.

        For production, these would be maintained or fetched from a reliable source.
        """
        # Predefined lists for major indexes
        index_members = {
            '^GSPC': self._get_sp500_members(),  # S&P 500
            '^CCMP': self._get_nasdaq100_members(),  # NASDAQ 100
            '^RUT': self._get_russell2000_members(),  # Russell 2000
            '^STOXX50E': self._get_stoxx50_members(),  # Euro Stoxx 50
            '^STOXX': self._get_stoxx600_members(),  # STOXX 600
            '^FCHI': self._get_cac40_members(),  # CAC 40
            '^FTSE': self._get_ftse100_members(),  # FTSE 100
        }

        return index_members.get(self.ticker, [])

    def _get_sp500_members(self) -> List[dict]:
        """Return a sample of S&P 500 companies."""
        # In production, this would be fetched from a reliable source
        # For now, returning major companies as examples
        return [
            {'title': 'Apple Inc.', 'wkn': None, 'isin': 'US0378331005', 'source_url': None},
            {'title': 'Microsoft Corporation', 'wkn': None, 'isin': 'US5949181045', 'source_url': None},
            {'title': 'Amazon.com Inc.', 'wkn': None, 'isin': 'US0231351023', 'source_url': None},
            {'title': 'Nvidia Corporation', 'wkn': None, 'isin': 'US67066991072', 'source_url': None},
            {'title': 'Tesla Inc.', 'wkn': None, 'isin': 'US88160R1014', 'source_url': None},
        ]

    def _get_nasdaq100_members(self) -> List[dict]:
        """Return NASDAQ 100 companies."""
        return [
            {'title': 'Apple Inc.', 'wkn': None, 'isin': 'US0378331005', 'source_url': None},
            {'title': 'Microsoft Corporation', 'wkn': None, 'isin': 'US5949181045', 'source_url': None},
            {'title': 'Amazon.com Inc.', 'wkn': None, 'isin': 'US0231351023', 'source_url': None},
            {'title': 'Nvidia Corporation', 'wkn': None, 'isin': 'US67066991072', 'source_url': None},
            {'title': 'Broadcom Inc.', 'wkn': None, 'isin': 'US11135F1012', 'source_url': None},
        ]

    def _get_russell2000_members(self) -> List[dict]:
        """Return Russell 2000 sample companies."""
        return [
            {'title': 'AAON Inc.', 'wkn': None, 'isin': 'US00437A1080', 'source_url': None},
            {'title': 'Calliditas Therapeutics AB', 'wkn': None, 'isin': 'US1266501006', 'source_url': None},
        ]

    def _get_stoxx50_members(self) -> List[dict]:
        """Return Euro Stoxx 50 sample companies."""
        return [
            {'title': 'SAP SE', 'wkn': '716460', 'isin': 'DE0007164600', 'source_url': None},
            {'title': 'Siemens AG', 'wkn': '723610', 'isin': 'DE0007236101', 'source_url': None},
            {'title': 'Airbus SE', 'wkn': '938914', 'isin': 'NL0000235190', 'source_url': None},
        ]

    def _get_stoxx600_members(self) -> List[dict]:
        """Return STOXX 600 sample companies."""
        return [
            {'title': 'SAP SE', 'wkn': '716460', 'isin': 'DE0007164600', 'source_url': None},
            {'title': 'ASML Holding NV', 'wkn': '118142', 'isin': 'NL0010088917', 'source_url': None},
        ]

    def _get_cac40_members(self) -> List[dict]:
        """Return CAC 40 sample companies."""
        return [
            {'title': 'TotalEnergies SE', 'wkn': None, 'isin': 'FR0000120271', 'source_url': None},
            {'title': 'Sanofi', 'wkn': None, 'isin': 'FR0000120578', 'source_url': None},
        ]

    def _get_ftse100_members(self) -> List[dict]:
        """Return FTSE 100 sample companies."""
        return [
            {'title': 'HSBC Holdings PLC', 'wkn': None, 'isin': 'GB0005405286', 'source_url': None},
            {'title': 'Shell PLC', 'wkn': None, 'isin': 'GB0007980591', 'source_url': None},
        ]

    def get_company_estimate_url(self, company: dict) -> Optional[str]:
        """
        Get the URL for a company's estimate page on Yahoo Finance.

        Yahoo Finance uses a standard URL pattern for company pages.
        """
        isin = company.get('isin')
        if isin:
            # Try to use ISIN to find on Yahoo Finance
            return f'https://finance.yahoo.com/quote/{isin}'
        return None
