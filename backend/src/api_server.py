"""
Simple Flask API server for ChatGPT integration.
Receives financial data from ChatGPT and imports into Supabase.

Run with:
  python -m src.api_server

Then expose via ngrok or similar for ChatGPT to access:
  ngrok http 5000
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.supabase_client import get_client
from src.calculations import calculate_cagr_for_metric, check_data_completeness
from config.indices import get_index_config
from src.logging_config import setup_logging

# Load environment
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Setup logging
logger = setup_logging('api_server')

# Create Flask app
app = Flask(__name__)
CORS(app)


class EstimateReceiver:
    """Receive and process financial estimates from ChatGPT."""

    def __init__(self):
        """Initialize receiver."""
        self.db_client = get_client()
        self.batch_id = None
        self.stats = {
            'companies': 0,
            'estimates': 0,
            'metrics': 0,
            'errors': [],
        }

    def normalize_numeric_value(self, value) -> Optional[float]:
        """Convert numeric values from various formats."""
        if not value or str(value).strip().upper() == 'NV':
            return None

        try:
            value = str(value).strip()

            # German format: 1.234,56
            dot_count = value.count('.')
            comma_count = value.count(',')

            if comma_count == 1 and dot_count >= 1:
                value = value.replace('.', '').replace(',', '.')
            elif comma_count == 1 and dot_count == 0:
                value = value.replace(',', '')
            elif dot_count == 1 and comma_count == 0:
                pass
            elif dot_count >= 1 and comma_count >= 1:
                if value.rfind(',') > value.rfind('.'):
                    value = value.replace('.', '').replace(',', '.')
                else:
                    value = value.replace(',', '')

            return float(value)
        except (ValueError, AttributeError):
            return None

    def get_or_create_company(
        self,
        index_id: str,
        isin: str,
        title: str,
        source_url: Optional[str] = None
    ) -> Optional[str]:
        """Get or create company."""
        try:
            existing = self.db_client.get_company_by_isin(isin)
            if existing:
                logger.info(f'Found existing: {title} ({isin})')
                return existing['id']

            company_data = {
                'index_id': index_id,
                'isin': isin,
                'title': title,
                'source_url': source_url or 'chatgpt_import',
                'last_scrape_status': 'chatgpt_import',
                'last_updated': datetime.utcnow().isoformat(),
            }

            response = self.db_client.client.table('companies').insert(
                company_data
            ).execute()

            if response.data:
                company_id = response.data[0]['id']
                logger.info(f'Created: {title} ({isin})')
                self.stats['companies'] += 1
                return company_id

        except Exception as e:
            logger.error(f'Error creating company {title}: {e}')
            self.stats['errors'].append(f'Company {title}: {str(e)}')

        return None

    def process_estimate(
        self,
        index_id: str,
        company_data: Dict,
        index_name: str
    ) -> bool:
        """Process single company estimate."""
        try:
            isin = company_data.get('isin', '').strip().upper()
            title = company_data.get('title', '').strip()

            if not isin or not title:
                self.stats['errors'].append('Missing ISIN or title')
                return False

            # Get or create company
            company_id = self.get_or_create_company(index_id, isin, title)
            if not company_id:
                return False

            # Group estimates by fiscal year
            estimates = {}

            for key, value in company_data.items():
                if key.startswith('fiscal_year_'):
                    fiscal_year = int(key.split('_')[2])
                    if fiscal_year not in estimates:
                        estimates[fiscal_year] = {'fiscal_year': fiscal_year}

            # Extract metrics for each fiscal year
            metric_fields = [
                'revenue_amount',
                'dividend',
                'dividend_yield_percent',
                'eps',
                'pe_ratio',
                'avg_price_target',
            ]

            for key, value in company_data.items():
                for field in metric_fields:
                    if key.startswith(f'{field}_'):
                        fiscal_year = int(key.split('_')[-1])
                        if fiscal_year in estimates:
                            numeric_value = self.normalize_numeric_value(value)
                            if numeric_value is not None:
                                estimates[fiscal_year][field] = numeric_value

            if not estimates:
                logger.warning(f'No estimates for {title}')
                return False

            # Add currency
            currency = company_data.get('currency', 'EUR').upper()
            for est_data in estimates.values():
                est_data['revenue_currency'] = currency
                if 'source_url' in company_data:
                    est_data['source_url'] = company_data['source_url']

            # Insert estimates
            for fiscal_year, estimate_data in estimates.items():
                success = self.db_client.upsert_estimate(
                    company_id, fiscal_year, estimate_data
                )
                if success:
                    self.stats['estimates'] += 1

            # Calculate metrics
            if self._calculate_and_store_metrics(company_id, estimates):
                self.stats['metrics'] += 1

            self.db_client.update_company_status(company_id, 'success')
            return True

        except Exception as e:
            logger.error(f'Error processing estimate: {e}')
            self.stats['errors'].append(str(e))
            return False

    def _calculate_and_store_metrics(
        self,
        company_id: str,
        estimates: Dict[int, dict]
    ) -> bool:
        """Calculate and store metrics."""
        try:
            if not estimates:
                return False

            metrics_data = {}
            metrics_to_calculate = [
                'revenue_amount',
                'dividend',
                'dividend_yield_percent',
                'eps',
                'pe_ratio',
            ]

            data_completeness = {}

            for metric in metrics_to_calculate:
                values_by_year = {
                    year: est.get(metric)
                    for year, est in estimates.items()
                }

                cagr = calculate_cagr_for_metric(values_by_year)
                if cagr and cagr != 'NV':
                    metrics_data[f'{metric}_cagr_percent'] = float(cagr)
                else:
                    metrics_data[f'{metric}_cagr_percent'] = None

                is_complete, _, _ = check_data_completeness(values_by_year)
                data_completeness[metric] = is_complete

            fiscal_years = sorted(estimates.keys())
            metrics_data['first_estimate_year'] = fiscal_years[0]
            metrics_data['last_estimate_year'] = fiscal_years[-1]
            metrics_data['estimate_count'] = len(fiscal_years)
            metrics_data['data_completeness'] = data_completeness

            return self.db_client.insert_metrics(company_id, metrics_data)

        except Exception as e:
            logger.error(f'Error calculating metrics: {e}')
            return False


receiver = EstimateReceiver()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
    })


@app.route('/api/submit-estimate', methods=['POST'])
def submit_estimate():
    """
    Receive financial estimate from ChatGPT and save to Supabase.

    Expected JSON payload:
    {
        "index": "DAX",
        "isin": "DE0005140008",
        "title": "Deutsche Telekom",
        "currency": "EUR",
        "source_url": "https://...",
        "estimates": [
            {
                "fiscal_year": 2024,
                "revenue_amount": 120000,
                "dividend": 0.70,
                "dividend_yield_percent": 2.5,
                "eps": 2.50,
                "pe_ratio": 15.5,
                "avg_price_target": 40.50
            },
            {
                "fiscal_year": 2025,
                ...
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate required fields
        index_name = data.get('index')
        isin = data.get('isin')
        title = data.get('title')
        estimates = data.get('estimates', [])

        if not all([index_name, isin, title]):
            return jsonify({
                'error': 'Missing required fields: index, isin, title'
            }), 400

        if not estimates:
            return jsonify({'error': 'No estimates provided'}), 400

        # Get index config
        index_config = get_index_config(index_name)
        if not index_config:
            return jsonify({'error': f'Unknown index: {index_name}'}), 400

        # Get index record
        index_record = receiver.db_client.get_index(index_name)
        if not index_record:
            return jsonify({
                'error': f'Index {index_name} not found in database'
            }), 400

        index_id = index_record['id']

        # Get or create company
        company_id = receiver.get_or_create_company(
            index_id,
            isin,
            title,
            data.get('source_url')
        )

        if not company_id:
            return jsonify({'error': 'Failed to create company'}), 500

        # Process estimates
        estimates_count = 0
        for estimate in estimates:
            fiscal_year = estimate.get('fiscal_year')
            if not fiscal_year:
                continue

            # Normalize numeric fields
            estimate_data = {'fiscal_year': fiscal_year}
            numeric_fields = [
                'revenue_amount',
                'dividend',
                'dividend_yield_percent',
                'eps',
                'pe_ratio',
                'avg_price_target',
            ]

            for field in numeric_fields:
                if field in estimate:
                    value = receiver.normalize_numeric_value(estimate[field])
                    if value is not None:
                        estimate_data[field] = value

            estimate_data['revenue_currency'] = data.get('currency', 'EUR')

            # Upsert estimate
            success = receiver.db_client.upsert_estimate(
                company_id, fiscal_year, estimate_data
            )
            if success:
                estimates_count += 1

        # Calculate metrics
        estimates_dict = {
            est['fiscal_year']: est for est in estimates
        }
        receiver._calculate_and_store_metrics(company_id, estimates_dict)

        # Update company status
        receiver.db_client.update_company_status(company_id, 'success')

        return jsonify({
            'status': 'success',
            'message': f'Saved {title}: {estimates_count} estimates',
            'company_id': company_id,
            'estimates_saved': estimates_count,
        }), 200

    except Exception as e:
        logger.error(f'Error in submit_estimate: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get import statistics."""
    return jsonify({
        'status': 'ok',
        'stats': receiver.stats,
        'timestamp': datetime.utcnow().isoformat(),
    })


@app.route('/api/list-indexes', methods=['GET'])
def list_indexes():
    """List available indexes."""
    from config.indices import INDEX_CONFIG

    indexes = [
        {
            'name': name,
            'display_name': config.get('display_name'),
            'region': config.get('region'),
        }
        for name, config in INDEX_CONFIG.items()
    ]

    return jsonify({
        'indexes': indexes,
        'count': len(indexes),
    }), 200


@app.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """Return OpenAPI spec for ChatGPT Actions."""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Aktienvergleich DAX Importer API",
            "description": "API for ChatGPT to submit financial estimates directly to Supabase",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": os.getenv('API_BASE_URL', 'http://localhost:5000'),
                "description": "API server"
            }
        ],
        "paths": {
            "/api/submit-estimate": {
                "post": {
                    "summary": "Submit financial estimate",
                    "description": "Submit a company's financial estimates to be saved to Supabase",
                    "operationId": "submitEstimate",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["index", "isin", "title", "estimates"],
                                    "properties": {
                                        "index": {
                                            "type": "string",
                                            "description": "Index name (DAX, MDAX, SPX, etc)",
                                            "example": "DAX"
                                        },
                                        "isin": {
                                            "type": "string",
                                            "description": "Company ISIN",
                                            "example": "DE0005140008"
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "Company name",
                                            "example": "Deutsche Telekom"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "description": "Currency (EUR, USD, GBP)",
                                            "default": "EUR",
                                            "example": "EUR"
                                        },
                                        "source_url": {
                                            "type": "string",
                                            "description": "Source page URL",
                                            "example": "https://www.finanzen.net/aktien/deutsche-telekom-aktie"
                                        },
                                        "estimates": {
                                            "type": "array",
                                            "description": "Array of fiscal year estimates",
                                            "items": {
                                                "type": "object",
                                                "required": ["fiscal_year"],
                                                "properties": {
                                                    "fiscal_year": {
                                                        "type": "integer",
                                                        "description": "Fiscal year",
                                                        "example": 2024
                                                    },
                                                    "revenue_amount": {
                                                        "type": "number",
                                                        "description": "Revenue in millions",
                                                        "example": 120000
                                                    },
                                                    "dividend": {
                                                        "type": "number",
                                                        "description": "Dividend per share",
                                                        "example": 0.70
                                                    },
                                                    "dividend_yield_percent": {
                                                        "type": "number",
                                                        "description": "Dividend yield percentage",
                                                        "example": 2.5
                                                    },
                                                    "eps": {
                                                        "type": "number",
                                                        "description": "Earnings per share",
                                                        "example": 2.50
                                                    },
                                                    "pe_ratio": {
                                                        "type": "number",
                                                        "description": "Price-to-earnings ratio",
                                                        "example": 15.5
                                                    },
                                                    "avg_price_target": {
                                                        "type": "number",
                                                        "description": "Average price target",
                                                        "example": 40.50
                                                    }
                                                }
                                            },
                                            "minItems": 1
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Estimate saved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "message": {"type": "string"},
                                            "company_id": {"type": "string"},
                                            "estimates_saved": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request"
                        },
                        "500": {
                            "description": "Server error"
                        }
                    }
                }
            },
            "/api/status": {
                "get": {
                    "summary": "Get import status",
                    "operationId": "getStatus",
                    "responses": {
                        "200": {
                            "description": "Status information"
                        }
                    }
                }
            },
            "/api/list-indexes": {
                "get": {
                    "summary": "List available indexes",
                    "operationId": "listIndexes",
                    "responses": {
                        "200": {
                            "description": "List of indexes"
                        }
                    }
                }
            }
        }
    }

    return jsonify(spec), 200


def main():
    """Run the API server."""
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info('=' * 70)
    logger.info('Aktienvergleich API Server')
    logger.info('=' * 70)
    logger.info(f'Starting server on port {port}...')
    logger.info('For ChatGPT integration, expose with:')
    logger.info('  ngrok http 5000')
    logger.info('  Then add https://[ngrok-url] to ChatGPT Custom Action')
    logger.info('=' * 70)

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
