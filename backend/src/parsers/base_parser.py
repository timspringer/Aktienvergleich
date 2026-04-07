"""Base parser class for extracting company estimate data."""

from abc import ABC, abstractmethod
import logging
from typing import Optional, Dict, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class CompanyParser(ABC):
    """Abstract base class for company estimate parsers."""

    def __init__(self, company: dict, index_config: dict):
        """
        Initialize parser.

        Args:
            company: Company dictionary with title, wkn, isin, source_url
            index_config: Index configuration dictionary
        """
        self.company = company
        self.index_config = index_config
        self.estimates: Dict[int, dict] = {}  # fiscal_year -> estimate data

    @abstractmethod
    def fetch_company_page(self) -> Optional[str]:
        """
        Fetch company estimate page.

        Returns:
            HTML content or API response as string, or None if failed
        """
        pass

    @abstractmethod
    def parse_estimates(self, page_content: str) -> Dict[int, dict]:
        """
        Parse estimate data from page content.

        Args:
            page_content: HTML or text content from company page

        Returns:
            Dictionary mapping fiscal_year -> estimate_data
            Example:
            {
                2024: {
                    'revenue': 5000.0,
                    'revenue_currency': 'EUR',
                    'dividend': 2.5,
                    'dividend_yield': 1.2,
                    'eps': 7.5,
                    'pe_ratio': 25.0,
                    'price_target': 187.5
                },
                2025: {...}
            }
        """
        pass

    def get_estimates(self) -> Dict[int, dict]:
        """
        Fetch and parse company estimates.

        Returns:
            Dictionary of fiscal_year -> estimate_data
        """
        try:
            page_content = self.fetch_company_page()
            if not page_content:
                logger.warning(
                    f'Failed to fetch page for {self.company.get("title")}'
                )
                return {}

            self.estimates = self.parse_estimates(page_content)
            logger.info(
                f'Parsed {len(self.estimates)} years for {self.company.get("title")}'
            )
            return self.estimates

        except Exception as e:
            logger.error(
                f'Error parsing estimates for {self.company.get("title")}: {e}'
            )
            return {}

    @staticmethod
    def normalize_estimate_field(field_name: str, value: str) -> Optional[float]:
        """
        Normalize an estimate field value.

        Handles German/English number formats, percentages, etc.
        """
        from ..normalizer import normalize_estimate_field

        return normalize_estimate_field(field_name, value)

    def validate_estimate(self, fiscal_year: int, estimate: dict) -> bool:
        """
        Validate an estimate record.

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(fiscal_year, int):
            return False

        if not isinstance(estimate, dict):
            return False

        # Check that at least one metric is present
        metrics = ['revenue', 'dividend', 'eps', 'pe_ratio', 'price_target']
        has_data = any(estimate.get(metric) is not None for metric in metrics)

        return has_data

    def filter_valid_estimates(self) -> Dict[int, dict]:
        """
        Filter estimates to only include valid ones.

        Returns:
            Validated estimates
        """
        valid = {}
        for fiscal_year, estimate in self.estimates.items():
            if self.validate_estimate(fiscal_year, estimate):
                valid[fiscal_year] = estimate
            else:
                logger.debug(
                    f'Invalid estimate for {self.company.get("title")} {fiscal_year}'
                )

        return valid
