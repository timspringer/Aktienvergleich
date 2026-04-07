# Phase 3: Index Loader Implementation

## Overview

Phase 3 implements the index loader system to fetch stock index members from multiple data sources.

## Architecture

### Components

#### Base Loader (`loaders/base_loader.py`)
Abstract base class defining the loader interface:
- `load_members()` - Load all members of an index
- `get_company_estimate_url()` - Get the URL for a company's estimate page
- `validate_company()` - Validate company data
- `validate_all_companies()` - Validate all loaded companies

#### Data Source Loaders

**FinanzenNetLoader** (`loaders/finanzen_net_loader.py`)
- Loads German indexes: DAX, MDAX, SDAX, TecDAX
- Scrapes finanzen.net index pages
- Extracts company names and links
- Uses retry logic with exponential backoff
- Caches pages to avoid excessive requests

**YahooFinanceLoader** (`loaders/yahoo_finance_loader.py`)
- Loads US indexes: S&P 500, NASDAQ 100, Russell 2000
- Uses predefined company lists (as Yahoo Finance API is not fully documented)
- Provides fallback mechanism for major indexes
- Extensible for future API integration

**EuropeanLoader** (`loaders/european_loader.py`)
- Loads European indexes: Euro Stoxx 50, STOXX 600, CAC 40, FTSE 100
- Uses YahooFinanceLoader as fallback
- Ready for integration with European stock exchange APIs

#### Dispatcher (`index_loader.py`)
Routes index loading to the appropriate loader:
- `IndexLoaderDispatcher` - Main dispatcher class
- `load_single_index()` - Convenience function for single index
- `load_all_indexes()` - Convenience function for all indexes

#### Main Entry Point (`main.py`)
CLI application with flexible arguments:
- `--index` - Load single index
- `--indexes` - Load multiple indexes (comma-separated)
- `--all` - Load all configured indexes
- `--region` - Load all indexes in a region
- `--limit` - Limit companies per index (for testing)
- `-v/--verbose` - Verbose logging
- `--dry-run` - Test without database writes

## Usage

### Setup

1. Create `.env` file with Supabase credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Load Single Index

```bash
python main.py --index DAX
python main.py --index SPX
python main.py --index STOXX50
```

### Load Multiple Indexes

```bash
python main.py --indexes DAX,MDAX,SPX
```

### Load All Indexes

```bash
python main.py --all
```

### Load with Limit (Testing)

```bash
python main.py --index DAX --limit 5
```

### Load by Region

```bash
python main.py --region Germany
python main.py --region USA
python main.py --region Europe
```

### Verbose Output

```bash
python main.py --index DAX -v
```

### Dry Run (No Database Writes)

```bash
python main.py --index DAX --dry-run
```

## Testing

Run the test script:

```bash
python test_index_loader.py
```

This will:
1. Verify Supabase connection
2. Load DAX companies (German index test)
3. Load SPX companies (US index test)
4. Load all indexes
5. Report success/failure

## Data Flow

```
main.py
  ↓
index_loader.py (IndexLoaderDispatcher)
  ↓
loaders/ (specific loader)
  ├─ finanzen_net_loader.py (German)
  ├─ yahoo_finance_loader.py (US)
  └─ european_loader.py (Europe)
  ↓
supabase_client.py (database)
  ↓
Supabase Database
```

## Error Handling

### Retry Logic
- Uses `@retry_with_backoff` decorator
- Maximum 3 retries with exponential backoff
- Initial delay: 1 second, backoff factor: 2x
- Optional jitter to avoid thundering herd

### Fallbacks
- If finanzen.net page fails: Log error, return empty list, continue
- If Yahoo Finance API fails: Use predefined company lists
- If database write fails: Log error, continue with other companies

### Logging
- Console output with color/formatting
- Rotating file logs (10 MB per file, 5 backups)
- Separate error log for failures
- Debug logging with `-v` flag

## Supported Indexes

### German (finanzen.net)
- **DAX** - 40 companies
- **MDAX** - 50 companies
- **SDAX** - 70 companies
- **TecDAX** - 30 companies

### US (Yahoo Finance)
- **S&P 500** - ~500 companies
- **NASDAQ 100** - 100 companies
- **Russell 2000** - ~2000 companies

### European (Yahoo Finance + alternatives)
- **Euro Stoxx 50** - 50 companies
- **STOXX 600** - 600 companies
- **CAC 40** - 40 companies
- **FTSE 100** - 100 companies

## Known Limitations

### finanzen.net
- HTML structure may change, requiring parser updates
- Some companies may not have full WKN/ISIN data
- Rate limiting is respected with delays

### Yahoo Finance
- Official API not fully documented
- Using predefined lists as fallback
- ISIN used for company identification instead of ticker

### General
- No real-time data (snapshot approach)
- Requires manual list updates if index composition changes
- First run may be slower due to network requests

## Future Enhancements

1. **API Integration**
   - Official Yahoo Finance API when available
   - European stock exchange APIs
   - Alternative financial data providers

2. **Caching**
   - Cache company lists to avoid re-scraping
   - TTL-based cache invalidation
   - Delta sync for incremental updates

3. **Parallel Loading**
   - Load multiple companies concurrently
   - Thread pool for HTTP requests
   - Connection pooling to Supabase

4. **Validation**
   - Validate company data against historical records
   - Check for duplicate entries
   - Verify data consistency

5. **Monitoring**
   - Metrics on load times
   - Alert on failures
   - Dashboard for tracking

## Troubleshooting

### "SUPABASE_URL and SUPABASE_KEY must be set"
- Make sure `.env` file exists in backend directory
- Check environment variables: `echo $SUPABASE_URL`

### "Could not find index table"
- finanzen.net HTML structure may have changed
- Check the actual page in browser
- Update the parser in `finanzen_net_loader.py`

### "Connection refused" (Supabase)
- Verify SUPABASE_URL is correct
- Check internet connection
- Verify Supabase project is running

### Slow loading
- Normal for first run (network requests)
- Check internet connection
- Monitor logs for warnings

## Files Modified/Created

- `loaders/base_loader.py` - Abstract base class
- `loaders/finanzen_net_loader.py` - German index loader
- `loaders/yahoo_finance_loader.py` - US index loader
- `loaders/european_loader.py` - European index loader
- `index_loader.py` - Main dispatcher
- `main.py` - CLI entry point
- `test_index_loader.py` - Test script
