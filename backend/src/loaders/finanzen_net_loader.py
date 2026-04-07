"""Loader for German indexes from finanzen.net."""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Optional

from .base_loader import IndexLoader
from ..retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class FinanzenNetLoader(IndexLoader):
    """Loader for German stock indexes from finanzen.net."""

    def __init__(self, index_name: str, index_config: dict):
        """Initialize finanzen.net loader."""
        super().__init__(index_name, index_config)
        self.base_url = 'https://www.finanzen.net'
        self.timeout = 30

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page from finanzen.net."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def load_members(self) -> List[dict]:
        """
        Load index members from finanzen.net.

        Scrapes the index page to extract company links and basic info.
        """
        index_url = self.index_config.get('url')
        if not index_url:
            logger.error(f'No URL configured for {self.index_name}')
            return []

        try:
            html = self._fetch_page(index_url)
            if not html:
                logger.error(f'Failed to fetch index page for {self.index_name}')
                return []

            companies = self._parse_index_page(html, index_url)
            self.companies = companies

            logger.info(
                f'Loaded {len(companies)} members for {self.index_name} from finanzen.net'
            )
            return companies

        except Exception as e:
            logger.error(f'Error loading {self.index_name} members: {e}')
            return []

    def _parse_index_page(self, html: str, base_url: str) -> List[dict]:
        """
        Parse index page HTML to extract company information.

        finanzen.net typically uses tables to display index members.
        """
        companies = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Look for table with index members
            # finanzen.net usually has a table with class containing 'index' or 'table'
            table = soup.find('table', class_=lambda x: x and 'table' in x)

            if not table:
                logger.warning(f'Could not find index table in {base_url}')
                return companies

            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue

                    # Extract company link
                    link = row.find('a', href=True)
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get('href', '')

                    if not title:
                        continue

                    # Build full URL if relative
                    estimate_url = href
                    if href.startswith('/'):
                        estimate_url = self.base_url + href
                    elif not href.startswith('http'):
                        estimate_url = self.base_url + '/' + href

                    # Try to extract WKN/ISIN from page
                    company = {
                        'title': title,
                        'wkn': None,
                        'isin': None,
                        'source_url': estimate_url,
                    }

                    companies.append(company)

                except Exception as e:
                    logger.debug(f'Error parsing row: {e}')
                    continue

            return companies

        except Exception as e:
            logger.error(f'Error parsing index page: {e}')
            return []

    def get_company_estimate_url(self, company: dict) -> Optional[str]:
        """
        Get the URL for a company's estimate page.

        For finanzen.net, we've already captured this during index loading.
        """
        source_url = company.get('source_url')
        if source_url:
            # Ensure it's an estimates page
            if '/schaetzungen/' not in source_url:
                # Try to convert to estimates page
                if source_url.endswith('/'):
                    return source_url + 'schaetzungen/'
                else:
                    return source_url + '/schaetzungen/'
            return source_url
        return None

    @retry_with_backoff(max_retries=2, initial_delay=0.5)
    def _fetch_company_details(self, company_url: str) -> Optional[dict]:
        """
        Fetch additional company details (WKN, ISIN) from company page.

        This requires parsing the company page HTML.
        """
        try:
            html = self._fetch_page(company_url)
            if not html:
                return None

            soup = BeautifulSoup(html, 'html.parser')

            # Look for WKN and ISIN in page
            wkn = None
            isin = None

            # Common patterns in finanzen.net
            for text_elem in soup.find_all(['span', 'td', 'dd']):
                text = text_elem.get_text(strip=True)
                if 'WKN:' in text or 'WKN ' in text:
                    parts = text.split(':')
                    if len(parts) > 1:
                        wkn = parts[1].strip()
                elif 'ISIN:' in text or 'ISIN ' in text:
                    parts = text.split(':')
                    if len(parts) > 1:
                        isin = parts[1].strip()

            return {'wkn': wkn, 'isin': isin}

        except Exception as e:
            logger.debug(f'Error fetching company details from {company_url}: {e}')
            return None
