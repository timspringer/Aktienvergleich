"""Supabase database client for Aktienvergleich."""

import os
import logging
from typing import Any, Optional
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper around Supabase client for database operations."""

    def __init__(self):
        """Initialize Supabase client with environment variables."""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')

        if not self.url or not self.key:
            raise ValueError(
                'SUPABASE_URL and SUPABASE_KEY must be set in environment'
            )

        self.client: Client = create_client(self.url, self.key)
        logger.info('Supabase client initialized')

    def get_index(self, index_name: str) -> Optional[dict]:
        """Get index by name."""
        try:
            response = self.client.table('indices').select('*').eq(
                'name', index_name
            ).execute()
            data = response.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f'Error fetching index {index_name}: {e}')
            return None

    def get_all_indexes(self) -> list[dict]:
        """Get all configured indexes."""
        try:
            response = self.client.table('indices').select('*').execute()
            return response.data or []
        except Exception as e:
            logger.error(f'Error fetching indexes: {e}')
            return []

    def insert_index_members(
        self, index_id: str, companies: list[dict]
    ) -> int:
        """Insert company members for an index."""
        inserted = 0
        failed = 0

        for company in companies:
            try:
                # Add index_id to company data
                company['index_id'] = index_id
                self.client.table('companies').insert(company).execute()
                inserted += 1
            except Exception as e:
                logger.warning(f'Failed to insert company {company.get("title")}: {e}')
                failed += 1

        logger.info(f'Inserted {inserted} companies, {failed} failed')
        return inserted

    def upsert_estimate(
        self, company_id: str, fiscal_year: int, estimate_data: dict
    ) -> bool:
        """Insert or update an estimate for a company."""
        try:
            estimate_data['company_id'] = company_id
            estimate_data['fiscal_year'] = fiscal_year
            estimate_data['updated_at'] = datetime.utcnow().isoformat()

            response = self.client.table('estimates').upsert(
                estimate_data, onconflict='company_id,fiscal_year'
            ).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(
                f'Error upserting estimate for company {company_id}, year {fiscal_year}: {e}'
            )
            return False

    def get_company(self, company_id: str) -> Optional[dict]:
        """Get company by ID."""
        try:
            response = self.client.table('companies').select('*').eq(
                'id', company_id
            ).execute()
            data = response.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f'Error fetching company {company_id}: {e}')
            return None

    def get_company_by_isin(self, isin: str) -> Optional[dict]:
        """Get company by ISIN."""
        try:
            response = self.client.table('companies').select('*').eq(
                'isin', isin
            ).execute()
            data = response.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f'Error fetching company by ISIN {isin}: {e}')
            return None

    def get_companies_by_index(self, index_id: str) -> list[dict]:
        """Get all companies in an index."""
        try:
            response = self.client.table('companies').select('*').eq(
                'index_id', index_id
            ).execute()
            return response.data or []
        except Exception as e:
            logger.error(f'Error fetching companies for index {index_id}: {e}')
            return []

    def update_company_status(
        self, company_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        """Update company scrape status."""
        try:
            data = {
                'last_scrape_status': status,
                'last_updated': datetime.utcnow().isoformat(),
            }
            if error_message:
                data['error_message'] = error_message

            response = self.client.table('companies').update(data).eq(
                'id', company_id
            ).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f'Error updating company {company_id} status: {e}')
            return False

    def get_estimates_by_company(self, company_id: str) -> list[dict]:
        """Get all estimates for a company."""
        try:
            response = (
                self.client.table('estimates')
                .select('*')
                .eq('company_id', company_id)
                .order('fiscal_year', desc=False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f'Error fetching estimates for company {company_id}: {e}')
            return []

    def insert_metrics(self, company_id: str, metrics_data: dict) -> bool:
        """Insert calculated metrics for a company."""
        try:
            metrics_data['company_id'] = company_id
            metrics_data['calculated_at'] = datetime.utcnow().isoformat()

            self.client.table('metrics').upsert(
                metrics_data, onconflict='company_id'
            ).execute()

            return True
        except Exception as e:
            logger.error(f'Error inserting metrics for company {company_id}: {e}')
            return False

    def get_metrics(self, company_id: str) -> Optional[dict]:
        """Get calculated metrics for a company."""
        try:
            response = self.client.table('metrics').select('*').eq(
                'company_id', company_id
            ).execute()
            data = response.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f'Error fetching metrics for company {company_id}: {e}')
            return None

    def log_scrape_run(
        self,
        index_id: str,
        total_companies: int,
        successful: int,
        failed: int,
        error_message: Optional[str] = None,
        status: str = 'success',
    ) -> bool:
        """Log a scraping run."""
        try:
            now = datetime.utcnow().isoformat()
            log_data = {
                'index_id': index_id,
                'started_at': now,
                'completed_at': now,
                'status': status,
                'total_companies': total_companies,
                'successful': successful,
                'failed': failed,
                'error_message': error_message,
            }

            response = self.client.table('scrape_logs').insert(log_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f'Error logging scrape run for index {index_id}: {e}')
            return False

    def get_last_scrape_log(self, index_id: str) -> Optional[dict]:
        """Get the most recent scrape log for an index."""
        try:
            response = (
                self.client.table('scrape_logs')
                .select('*')
                .eq('index_id', index_id)
                .order('created_at', desc=True)
                .limit(1)
                .execute()
            )
            data = response.data
            return data[0] if data else None
        except Exception as e:
            logger.error(f'Error fetching scrape logs for index {index_id}: {e}')
            return None

    def health_check(self) -> bool:
        """Check if Supabase connection is working."""
        try:
            self.client.table('indices').select('id').limit(1).execute()
            logger.info('Supabase health check passed')
            return True
        except Exception as e:
            logger.error(f'Supabase health check failed: {e}')
            return False


# Global instance
_client: Optional[SupabaseClient] = None


def get_client() -> SupabaseClient:
    """Get or create the global Supabase client."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
