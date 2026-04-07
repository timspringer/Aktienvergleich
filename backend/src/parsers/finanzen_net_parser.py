"""Parser for German company estimates from finanzen.net."""

import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

from .base_parser import CompanyParser
from ..retry_utils import retry_with_backoff
from ..normalizer import (
    normalize_revenue,
    normalize_dividend,
    normalize_dividend_yield,
    normalize_eps,
    normalize_pe_ratio,
    normalize_price_target,
    is_valid_value,
)

logger = logging.getLogger(__name__)


class FinanzenNetParser(CompanyParser):
    """Parser for German company estimates from finanzen.net."""

    def __init__(self, company: dict, index_config: dict):
        """Initialize finanzen.net parser."""
        super().__init__(company, index_config)
        self.base_url = 'https://www.finanzen.net'
        self.timeout = 30

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def fetch_company_page(self) -> Optional[str]:
        """Fetch company estimate page from finanzen.net."""
        url = self.company.get('source_url')
        if not url:
            logger.warning(f'No URL for {self.company.get("title")}')
            return None

        # Ensure we're on the estimates page
        if '/schaetzungen/' not in url:
            if url.endswith('/'):
                url = url + 'schaetzungen/'
            else:
                url = url + '/schaetzungen/'

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

    def parse_estimates(self, html: str) -> Dict[int, dict]:
        """
        Parse estimate table from finanzen.net HTML.

        finanzen.net displays estimates in a table format.
        """
        estimates = {}

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find estimate tables
            tables = soup.find_all('table', class_=lambda x: x and 'table' in x)

            for table in tables:
                fiscal_years = self._extract_fiscal_years_from_header(table)
                if not fiscal_years:
                    continue

                # Parse each row for estimates
                estimates.update(
                    self._parse_estimate_rows(table, fiscal_years)
                )

            return estimates

        except Exception as e:
            logger.error(f'Error parsing estimates HTML: {e}')
            return {}

    def _extract_fiscal_years_from_header(self, table) -> list:
        """Extract fiscal years from table header."""
        years = []
        try:
            header_row = table.find('tr')
            if not header_row:
                return []

            for th in header_row.find_all(['th', 'td']):
                text = th.get_text(strip=True)
                # Look for year patterns (e.g., "2024e", "2024", "2024E")
                match = re.search(r'(\d{4})', text)
                if match:
                    year = int(match.group(1))
                    if 1900 < year < 3000:
                        years.append(year)

            return sorted(years)

        except Exception as e:
            logger.debug(f'Error extracting fiscal years: {e}')
            return []

    def _parse_estimate_rows(self, table, fiscal_years: list) -> Dict[int, dict]:
        """Parse estimate rows from table."""
        estimates = {}

        try:
            rows = table.find_all('tr')[1:]  # Skip header

            # Common metric names we look for
            metric_patterns = {
                'revenue': ['umsatz', 'revenue', 'sales'],
                'dividend': ['dividend', 'ausschüttung'],
                'dividend_yield': ['dividendenrendite', 'dividend yield'],
                'eps': ['gewinn je aktie', 'eps', 'earnings per share'],
                'pe_ratio': ['kgv', 'p/e', 'price-earnings'],
                'price_target': ['kursziel', 'price target', 'target price'],
            }

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # First column is usually the metric name
                metric_name = cells[0].get_text(strip=True).lower()

                # Find which metric this row represents
                detected_metric = None
                for metric, patterns in metric_patterns.items():
                    if any(pattern in metric_name for pattern in patterns):
                        detected_metric = metric
                        break

                if not detected_metric:
                    continue

                # Extract values for each fiscal year
                for year_idx, year in enumerate(fiscal_years):
                    cell_idx = year_idx + 1
                    if cell_idx >= len(cells):
                        continue

                    value_text = cells[cell_idx].get_text(strip=True)

                    # Normalize the value
                    normalized_value = self.normalize_estimate_field(
                        detected_metric, value_text
                    )

                    if normalized_value is not None:
                        if year not in estimates:
                            estimates[year] = {}
                        estimates[year][detected_metric] = normalized_value

            # Add currency info
            for year in estimates:
                estimates[year]['revenue_currency'] = (
                    self.index_config.get('currency', 'EUR')
                )

            return estimates

        except Exception as e:
            logger.error(f'Error parsing estimate rows: {e}')
            return {}

    def _extract_wkn_isin(self, html: str):
        """Extract WKN and ISIN from company page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            for elem in soup.find_all(['span', 'td', 'dd', 'div']):
                text = elem.get_text()
                if 'WKN' in text:
                    match = re.search(r'WKN[:\s]+([A-Z0-9]{6})', text)
                    if match:
                        self.company['wkn'] = match.group(1)

                if 'ISIN' in text:
                    match = re.search(
                        r'ISIN[:\s]+([A-Z]{2}[A-Z0-9]{9}[0-9])', text
                    )
                    if match:
                        self.company['isin'] = match.group(1)

        except Exception as e:
            logger.debug(f'Error extracting WKN/ISIN: {e}')
