# Phase 4: Company Parser Implementation

## Overview

Phase 4 implements the company estimate parsers to extract financial data from company pages across all data sources.

## Architecture

### Components

#### Base Parser (`parsers/base_parser.py`)
Abstract base class defining the parser interface:
- `fetch_company_page()` - Fetch company estimate page
- `parse_estimates()` - Parse estimate data from page
- `get_estimates()` - Complete fetch and parse workflow
- `validate_estimate()` - Validate estimate records
- `filter_valid_estimates()` - Return only valid estimates

#### Data Source Parsers

**FinanzenNetParser** (`parsers/finanzen_net_parser.py`)
- Parses German company estimates from finanzen.net
- Extracts data from estimate tables
- Handles German number formats (comma as decimal)
- Automatically detects fiscal years from table headers
- Extracts WKN/ISIN from company pages
- Metrics extracted:
  - Revenue (Umsatz)
  - Dividends
  - Dividend Yield
  - EPS (Earnings Per Share / Gewinn je Aktie)
  - P/E Ratio (KGV)
  - Price Target (Kursziel)

**YahooFinanceParser** (`parsers/yahoo_finance_parser.py`)
- Parses US company estimates from Yahoo Finance
- Uses ISIN to identify companies
- Extracts analysis and estimates data
- Fallback to general page metrics if detailed estimates unavailable
- Handles US number formats (period as decimal)

**EuropeanParser** (`parsers/european_parser.py`)
- Parses European company estimates
- Uses Yahoo Finance as primary source
- Ready for extension with European stock exchange APIs
- Supports multi-source fallback

#### Main Dispatcher (`company_parser.py`)
Routes parsing to appropriate parser:
- `CompanyParserDispatcher` - Main dispatcher class
- `parse_single_company()` - Convenience function for single company
- `parse_index_companies()` - Parse all companies in an index

## Data Extraction

### Metrics Extracted

| Metric | Source | Format | Notes |
|--------|--------|--------|-------|
| Revenue (Umsatz) | Company page table | Millions of base currency | Can be EUR, USD, or GBP |
| Dividend | Company page table | Per share, base currency | Annual or latest available |
| Dividend Yield | Company page table | Percentage (0-100) | Annualized |
| EPS | Company page table | Per share, base currency | Earnings per share |
| P/E Ratio (KGV) | Company page table | Unitless ratio | Price-to-earnings |
| Price Target | Company page table | Base currency | Analyst consensus target |

### Fiscal Years

- Extracted automatically from table headers
- Supports various formats: "2024", "2024e", "2024E", etc.
- Multiple years per company (e.g., 2024, 2025, 2026, 2027, 2028)

### Number Format Handling

- **German format**: "1.234,56" → 1234.56 (comma = decimal, period = thousands separator)
- **English format**: "1,234.56" → 1234.56 (period = decimal, comma = thousands separator)
- **Percentages**: "5,5%" → 5.5
- **Scientific notation**: "1,5e6" → 1500000
- **Missing values**: Dashes, empty cells → None/NV

## Usage

### Test Parser

```bash
python test_company_parser.py
```

### Parse Single Company (Manual)

```python
from src.company_parser import parse_single_company

company = {
    'title': 'SAP SE',
    'wkn': '716460',
    'isin': 'DE0007164600',
    'source_url': 'https://www.finanzen.net/aktien/sap-aktie'
}

estimates = parse_single_company(company, 'DAX')
# Returns: {2024: {...}, 2025: {...}, ...}
```

### Parse and Store Companies

```python
from src.company_parser import parse_index_companies

# Parse all companies in an index
total_stored, total_companies = parse_index_companies(
    index_id='some-uuid',
    index_name='DAX'
)
```

## Data Flow

```
Company Parser Dispatcher
  ├─ Get Parser (based on index data source)
  │  ├─ FinanzenNetParser
  │  ├─ YahooFinanceParser
  │  └─ EuropeanParser
  ├─ Fetch Company Page
  │  └─ Retry with exponential backoff
  ├─ Parse HTML/Content
  │  ├─ Extract table structure
  │  ├─ Detect fiscal years
  │  ├─ Detect metrics
  │  └─ Extract values
  ├─ Normalize Values
  │  └─ normalizer.py
  ├─ Validate Estimates
  │  └─ Check data quality
  └─ Store to Database
     └─ supabase_client.py
```

## Error Handling

### Retry Strategy
- Maximum 3 retries with exponential backoff
- Initial delay: 1 second
- Backoff factor: 2x
- Optional jitter to avoid thundering herd

### Fallbacks
- If detailed estimates not found: extract from general page
- If page fails to load: log error, mark as 'failed', continue
- If estimate parsing fails: try alternative extraction methods

### Logging
- Debug: Detailed parsing information
- Info: Successful estimates parsed
- Warning: Partial data or missing fields
- Error: Complete failures

## Supported Data Extraction

### finanzen.net (German Companies)
- Table-based estimates
- Multiple fiscal years
- WKN and ISIN extraction
- Revenue in millions EUR
- Dividend and yield calculations
- EPS and P/E ratio

### Yahoo Finance (US & European)
- Analysis and estimates sections
- Limited fiscal year data (often current year only)
- ISIN-based company identification
- Analyst consensus data
- Per-share metrics

## Known Limitations

### HTML Parsing
- Website structure changes may break parsers
- JavaScript-rendered content not captured by basic requests
- Playwright support available for future enhancement

### Data Availability
- Not all companies have full estimate data
- Some years may be missing estimates
- Price targets may be outdated

### Number Formats
- Edge cases with special characters may not parse correctly
- Scientific notation only partially supported
- Currency conversion not implemented

## Future Enhancements

1. **Playwright Integration**
   - Handle JavaScript-rendered pages
   - Wait for dynamic content loading
   - Screenshot validation for debugging

2. **Multi-Year Support**
   - Better fiscal year extraction
   - Handle different fiscal year end dates
   - Support quarterly estimates

3. **Enhanced Fallbacks**
   - Alternative financial data providers
   - API integration when available
   - AI-assisted data extraction

4. **Caching**
   - Cache parsed pages
   - Incremental updates
   - TTL-based invalidation

5. **Quality Assurance**
   - Cross-validate with other sources
   - Anomaly detection
   - Historical comparison

## Testing Strategy

1. **Unit Tests** (future)
   - Test normalizer for various number formats
   - Test parser extraction logic
   - Test error handling

2. **Integration Tests** (future)
   - Test full fetch→parse→store workflow
   - Test with real data from sources
   - Test database interactions

3. **Manual Tests**
   - Parse known companies
   - Verify extracted data accuracy
   - Test edge cases

## Files Modified/Created

- `parsers/base_parser.py` - Abstract base class
- `parsers/finanzen_net_parser.py` - German company parser
- `parsers/yahoo_finance_parser.py` - US company parser
- `parsers/european_parser.py` - European company parser
- `company_parser.py` - Main dispatcher
- `test_company_parser.py` - Test script
- `PHASE4_COMPANY_PARSER.md` - This documentation

## Next Steps

Phase 5 will focus on:
1. Integrating parsers into the main scraper workflow
2. Building CAGR calculations from extracted data
3. Storing calculated metrics to database
4. Comprehensive error logging and recovery
