"""Base loader class for index member loading."""

from abc import ABC, abstractmethod
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class IndexLoader(ABC):
    """Abstract base class for index loaders."""

    def __init__(self, index_name: str, index_config: dict):
        """
        Initialize loader.

        Args:
            index_name: Name of the index (e.g., 'DAX')
            index_config: Configuration dictionary for the index
        """
        self.index_name = index_name
        self.index_config = index_config
        self.companies: List[dict] = []

    @abstractmethod
    def load_members(self) -> List[dict]:
        """
        Load all members of the index.

        Returns:
            List of company dictionaries with keys: title, wkn, isin, source_url
        """
        pass

    @abstractmethod
    def get_company_estimate_url(self, company: dict) -> Optional[str]:
        """
        Get the URL for a company's estimate page.

        Args:
            company: Company dictionary from load_members()

        Returns:
            URL to the company's estimate page or None if not found
        """
        pass

    def validate_company(self, company: dict) -> bool:
        """
        Validate that a company has required fields.

        Args:
            company: Company dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title']
        optional_fields = ['wkn', 'isin', 'source_url']

        # Check required fields
        for field in required_fields:
            if field not in company or not company[field]:
                logger.warning(f'Company missing required field: {field}')
                return False

        # Ensure optional fields exist (can be None)
        for field in optional_fields:
            if field not in company:
                company[field] = None

        return True

    def validate_all_companies(self) -> int:
        """
        Validate all loaded companies.

        Returns:
            Number of valid companies
        """
        valid_companies = []
        for company in self.companies:
            if self.validate_company(company):
                valid_companies.append(company)

        self.companies = valid_companies
        logger.info(
            f'Validated {len(valid_companies)} companies for {self.index_name}'
        )
        return len(valid_companies)

    def get_companies(self) -> List[dict]:
        """Get loaded companies."""
        return self.companies
