"""Parser for company estimates from Yahoo Finance."""

import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from urllib.parse import quote

from .base_parser import CompanyParser
from ..retry_utils import retry_with_backoff
from ..normalizer import (
    normalize_revenue,
    normalize_dividend,
    normalize_dividend_yield,
    normalize_eps,
    normalize_pe_ratio,
    normalize_price_target,
)

logger = logging.getLogger(__name__)


class YahooFinanceParser(CompanyParser):
    """Parser for company estimates from Yahoo Finance."""

    def __init__(self, company: dict, index_config: dict):
        """Initialize Yahoo Finance parser."""
        super().__init__(company, index_config)
        self.base_url = 'https://finance.yahoo.com'
        self.timeout = 30

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def fetch_company_page(self) -> Optional[str]:
        """Fetch company page from Yahoo Finance."""
        # Try to build URL from ISIN or ticker
        url = self._get_company_url()
        if not url:
            logger.warning(f'Could not determine URL for {self.company.get("title")}')
            return None

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text

        except requests.RequestException as e:
            logger.warning(f'Failed to fetch {url}: {e}')
            return None

    def _get_company_url(self) -> Optional[str]:
        """Get Yahoo Finance URL for company."""
        # Try ISIN first
        isin = self.company.get('isin')
        if isin:
            return f'{self.base_url}/quote/{isin}'

        # Try source_url if it's already a Yahoo Finance link
        source_url = self.company.get('source_url')
        if source_url and 'finance.yahoo.com' in source_url:
            return source_url

        return None

    def parse_estimates(self, html: str) -> Dict[int, dict]:
        """
        Parse estimate data from Yahoo Finance HTML.

        Yahoo Finance displays analysis data in a specific format.
        """
        estimates = {}

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Look for analyst estimates section
            # This is typically in a div with analysis/estimates info
            estimates_section = soup.find(
                'div',
                {'data-testid': 'analysis'} or {'id': 'pagesection-analysis'},
            )

            if not estimates_section:
                logger.debug('Could not find estimates section on Yahoo Finance')
                return self._extract_estimates_from_general_page(soup)

            # Parse estimates from section
            estimates = self._parse_estimates_section(estimates_section)

            return estimates

        except Exception as e:
            logger.error(f'Error parsing Yahoo Finance estimates: {e}')
            return {}

    def _extract_estimates_from_general_page(self, soup) -> Dict[int, dict]:
        """
        Fallback: Extract whatever estimate data is available from page.

        Yahoo Finance may not have detailed estimates for all companies.
        """
        estimates = {}

        try:
            # Look for key metrics in tables
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        # Extract current year estimates
                        if any(x in label for x in ['pe ratio', 'p/e', 'eps', 'dividend']):
                            normalized = self.normalize_estimate_field(label, value)
                            if normalized is not None:
                                # Use current year as placeholder
                                if 2024 not in estimates:
                                    estimates[2024] = {}

                                if 'pe' in label:
                                    estimates[2024]['pe_ratio'] = normalized
                                elif 'eps' in label:
                                    estimates[2024]['eps'] = normalized
                                elif 'dividend' in label:
                                    estimates[2024]['dividend'] = normalized

            return estimates

        except Exception as e:
            logger.debug(f'Error in fallback estimate extraction: {e}')
            return {}

    def _parse_estimates_section(self, section) -> Dict[int, dict]:
        """Parse the estimates section from Yahoo Finance."""
        estimates = {}

        try:
            # Yahoo Finance shows earnings and revenue estimates
            # Structure may vary, so we'll look for common patterns

            tables = section.find_all('table')
            for table in tables:
                # Try to identify what type of data this is
                estimate_type = None
                rows = table.find_all('tr')

                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    label = cells[0].get_text(strip=True).lower()

                    # Identify estimate type from label
                    if 'revenue' in label or 'sales' in label:
                        estimate_type = 'revenue'
                    elif 'eps' in label or 'earnings' in label:
                        estimate_type = 'eps'
                    elif 'dividend' in label:
                        estimate_type = 'dividend'
                    elif 'pe' in label:
                        estimate_type = 'pe_ratio'

                    if estimate_type and len(cells) > 1:
                        value = cells[1].get_text(strip=True)
                        normalized = self.normalize_estimate_field(
                            estimate_type, value
                        )

                        if normalized is not None:
                            # Use placeholder year
                            if 2024 not in estimates:
                                estimates[2024] = {}
                            estimates[2024][estimate_type] = normalized

            # Add currency
            for year in estimates:
                estimates[year]['revenue_currency'] = (
                    self.index_config.get('currency', 'USD')
                )

            return estimates

        except Exception as e:
            logger.debug(f'Error parsing estimates section: {e}')
            return {}
