"""Main index loader dispatcher."""

import logging
from typing import List, Optional, Dict

from config.indices import INDEX_CONFIG, get_index_config
from .loaders.base_loader import IndexLoader
from .loaders.finanzen_net_loader import FinanzenNetLoader
from .loaders.yahoo_finance_loader import YahooFinanceLoader
from .loaders.european_loader import EuropeanLoader
from .supabase_client import get_client

logger = logging.getLogger(__name__)


class IndexLoaderDispatcher:
    """Dispatcher for loading index members from appropriate sources."""

    def __init__(self):
        """Initialize dispatcher."""
        self.db_client = get_client()
        self.loaders: Dict[str, IndexLoader] = {}

    def get_loader(self, index_name: str) -> Optional[IndexLoader]:
        """
        Get or create a loader for the specified index.

        Args:
            index_name: Name of the index (e.g., 'DAX', 'SPX')

        Returns:
            Appropriate loader instance or None if index not found
        """
        if index_name in self.loaders:
            return self.loaders[index_name]

        config = get_index_config(index_name)
        if not config:
            logger.error(f'Index {index_name} not found in configuration')
            return None

        data_source = config.get('data_source', '')

        # Select appropriate loader based on data source
        if data_source == 'finanzen_net':
            loader = FinanzenNetLoader(index_name, config)
        elif data_source == 'yahoo_finance':
            region = config.get('region', '')
            if region == 'Europe':
                loader = EuropeanLoader(index_name, config)
            else:
                loader = YahooFinanceLoader(index_name, config)
        else:
            logger.warning(f'Unknown data source {data_source} for {index_name}')
            return None

        self.loaders[index_name] = loader
        return loader

    def load_index_members(self, index_name: str) -> List[dict]:
        """
        Load all members of an index and store in database.

        Args:
            index_name: Name of the index

        Returns:
            List of loaded companies
        """
        logger.info(f'Loading members for index: {index_name}')

        # Get loader
        loader = self.get_loader(index_name)
        if not loader:
            logger.error(f'Could not create loader for {index_name}')
            return []

        # Load members
        companies = loader.load_members()
        if not companies:
            logger.warning(f'No companies loaded for {index_name}')
            return []

        # Validate companies
        valid_count = loader.validate_all_companies()
        logger.info(f'Validated {valid_count}/{len(companies)} companies')

        # Get index ID from database
        index_record = self.db_client.get_index(index_name)
        if not index_record:
            logger.error(f'Index {index_name} not found in database')
            return []

        index_id = index_record['id']

        # Store in database
        inserted = self.db_client.insert_index_members(index_id, loader.get_companies())
        logger.info(f'Inserted {inserted} companies for {index_name}')

        return loader.get_companies()

    def load_all_indexes(self) -> Dict[str, int]:
        """
        Load members for all configured indexes.

        Returns:
            Dictionary mapping index names to number of companies loaded
        """
        results = {}

        for index_name in INDEX_CONFIG.keys():
            try:
                companies = self.load_index_members(index_name)
                results[index_name] = len(companies)
            except Exception as e:
                logger.error(f'Error loading {index_name}: {e}')
                results[index_name] = 0

        return results

    def load_indexes_by_region(self, region: str) -> Dict[str, int]:
        """
        Load members for all indexes in a region.

        Args:
            region: Region name ('Germany', 'Europe', 'USA')

        Returns:
            Dictionary mapping index names to number of companies loaded
        """
        results = {}

        for index_name, config in INDEX_CONFIG.items():
            if config.get('region') == region:
                try:
                    companies = self.load_index_members(index_name)
                    results[index_name] = len(companies)
                except Exception as e:
                    logger.error(f'Error loading {index_name}: {e}')
                    results[index_name] = 0

        return results


def load_single_index(index_name: str) -> List[dict]:
    """
    Convenience function to load a single index.

    Args:
        index_name: Name of the index

    Returns:
        List of loaded companies
    """
    dispatcher = IndexLoaderDispatcher()
    return dispatcher.load_index_members(index_name)


def load_all_indexes() -> Dict[str, int]:
    """
    Convenience function to load all indexes.

    Returns:
        Dictionary mapping index names to number of companies
    """
    dispatcher = IndexLoaderDispatcher()
    return dispatcher.load_all_indexes()
