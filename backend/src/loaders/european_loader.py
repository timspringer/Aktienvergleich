"""Loader for European indexes with multiple source support."""

import logging
from typing import List, Optional

from .base_loader import IndexLoader
from .yahoo_finance_loader import YahooFinanceLoader

logger = logging.getLogger(__name__)


class EuropeanLoader(IndexLoader):
    """Loader for European stock indexes."""

    def __init__(self, index_name: str, index_config: dict):
        """Initialize European loader."""
        super().__init__(index_name, index_config)
        self.fallback_loader = YahooFinanceLoader(index_name, index_config)

    def load_members(self) -> List[dict]:
        """
        Load European index members.

        Tries multiple sources:
        1. Yahoo Finance (primary)
        2. Alternative sources (future enhancement)
        """
        logger.info(f'Loading {self.index_name} members from European sources')

        # Currently relies on Yahoo Finance fallback
        # In future, this could try:
        # - European stock exchange APIs
        # - Specialized financial data providers
        # - Bloomberg alternative sources

        companies = self.fallback_loader.load_members()
        self.companies = companies

        logger.info(f'Loaded {len(companies)} members for {self.index_name}')
        return companies

    def get_company_estimate_url(self, company: dict) -> Optional[str]:
        """Get URL for European company estimate page."""
        return self.fallback_loader.get_company_estimate_url(company)
