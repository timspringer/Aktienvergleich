"""Parser for European company estimates."""

import logging
from typing import Optional, Dict

from .base_parser import CompanyParser
from .yahoo_finance_parser import YahooFinanceParser

logger = logging.getLogger(__name__)


class EuropeanParser(CompanyParser):
    """Parser for European company estimates."""

    def __init__(self, company: dict, index_config: dict):
        """Initialize European parser."""
        super().__init__(company, index_config)
        # Use Yahoo Finance as primary source
        self.fallback_parser = YahooFinanceParser(company, index_config)

    def fetch_company_page(self) -> Optional[str]:
        """Fetch European company page."""
        logger.debug(
            f'Fetching European company page for {self.company.get("title")}'
        )
        # Currently relies on Yahoo Finance
        return self.fallback_parser.fetch_company_page()

    def parse_estimates(self, page_content: str) -> Dict[int, dict]:
        """
        Parse European company estimates.

        Tries multiple sources:
        1. Yahoo Finance (primary)
        2. Alternative sources (future)
        """
        # Use Yahoo Finance parser
        return self.fallback_parser.parse_estimates(page_content)
