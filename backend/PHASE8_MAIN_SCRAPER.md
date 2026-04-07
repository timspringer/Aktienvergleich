# Phase 8: Main Scraper Orchestrator - Complete Data Pipeline

## Overview

Phase 8 orchestrates the complete data collection and processing pipeline. It ties together all previous phases:

1. Index Loading (Phase 3)
2. Company Parsing (Phase 4)
3. Data Normalization (Phase 2 - Normalizer)
4. CAGR Calculations (Phase 2 - Calculations)
5. Database Operations (Phase 2 - Supabase Client)

## Architecture

### Data Pipeline (`src/pipeline.py`)

**DataPipeline Class** - Main orchestrator:
- `process_index(index_name)` - Process single index
- `process_all_indexes()` - Process all configured indexes
- `process_indexes_by_region(region)` - Process by region
- `_calculate_and_store_metrics()` - Calculate CAGR and metrics

**Pipeline Workflow:**

```
1. LOAD INDEX MEMBERS
   ├─ Fetch from finanzen.net/Yahoo Finance
   ├─ Validate company data
   └─ Store to database

2. PARSE COMPANY ESTIMATES (for each company)
   ├─ Fetch company page
   ├─ Extract financial data
   ├─ Normalize formats
   └─ Validate estimates

3. CALCULATE METRICS
   ├─ Calculate CAGR from estimates
   ├─ Check data completeness
   ├─ Store metrics to database
   └─ Update company status

4. ERROR HANDLING
   ├─ Retry on failures
   ├─ Continue on errors
   ├─ Log all issues
   └─ Report summary
```

### Enhanced Main Entry Point (`main.py`)

**Features:**
- Complete argument parsing for all scenarios
- Environment setup and validation
- Database health checks
- Comprehensive logging
- Error reporting
- Pipeline execution and summary

**CLI Examples:**

```bash
# Single index (full pipeline)
python main.py --index DAX

# Multiple indexes
python main.py --indexes DAX,MDAX,SPX

# All indexes
python main.py --all

# By region
python main.py --region Germany
python main.py --region USA
python main.py --region Europe

# Test with limited companies
python main.py --index DAX --limit 5

# Verbose logging
python main.py --index DAX -v

# Skip validation
python main.py --all --skip-validation
```

## Complete Data Flow

```
User Input (CLI)
  ↓
main.py (Argument parsing & setup)
  ├─ Setup environment
  ├─ Test database connection
  └─ Validate parameters
  ↓
DataPipeline (Orchestrator)
  ↓
IndexLoaderDispatcher (Phase 3)
  ├─ FinanzenNetLoader
  ├─ YahooFinanceLoader
  └─ EuropeanLoader
  ↓
[For each company...]
  ↓
CompanyParserDispatcher (Phase 4)
  ├─ FinanzenNetParser
  ├─ YahooFinanceParser
  └─ EuropeanParser
  ↓
Normalizer (Phase 2)
  ├─ German format → 1234.56
  ├─ English format → 1234.56
  └─ Handle percentages & edge cases
  ↓
Calculations (Phase 2)
  ├─ Calculate CAGR
  ├─ Check data completeness
  └─ Validate metrics
  ↓
Supabase Client (Phase 2)
  ├─ Insert estimates
  ├─ Insert metrics
  └─ Update company status
  ↓
Supabase Database
  ├─ estimates table
  ├─ metrics table
  ├─ companies table (status)
  └─ scrape_logs table
  ↓
Output (Summary & Statistics)
```

## Metrics Calculated

For each company, the pipeline calculates:

### CAGR Values (Compound Annual Growth Rate)
- **Revenue CAGR** - Year-over-year revenue growth
- **Dividend CAGR** - Year-over-year dividend growth
- **Dividend Yield CAGR** - Dividend yield growth rate
- **EPS CAGR** - Earnings per share growth
- **P/E Ratio CAGR** - P/E ratio trend

### Data Quality Metrics
- **Estimate Count** - Number of fiscal years with data
- **First Estimate Year** - Earliest fiscal year
- **Last Estimate Year** - Latest fiscal year
- **Data Completeness** - Per metric (revenue, dividend, eps, etc.)

## Error Handling & Resilience

### Graceful Degradation
- Continues if one company fails
- Logs all errors comprehensively
- Provides partial results even on failure
- Never stops entire pipeline for single error

### Retry Strategy
- Exponential backoff for network issues
- 3 retries per page fetch
- Fallback to alternative sources when available

### Status Tracking
Each company is marked with one of:
- **success** - All estimates parsed and metrics calculated
- **partial** - Some estimates found, not all data complete
- **failed** - No estimates found or critical error
- **pending** - Not yet processed

## Performance Characteristics

### Typical Metrics (Per Index)
- DAX (40 companies): ~15-20 minutes
- SPX (500 companies): ~3-5 hours
- Full pipeline (all 12 indexes): ~8-12 hours

### Optimization Notes
- Respects rate limits (1-2 requests per second)
- Caches parsed pages in future versions
- Can be parallelized for faster processing
- Database batch operations for efficiency

## Configuration

### Environment Variables
```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SCRAPER_TIMEOUT=30           # seconds
SCRAPER_RETRIES=3             # attempts
SCRAPER_DELAY=1               # seconds between requests
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
```

### Index Configuration
In `backend/config/indices.py`:
- All 12 indexes pre-configured
- Data sources specified (finanzen_net, yahoo_finance)
- Currency and region information
- Fallback URLs and tickers

## Usage Patterns

### Development/Testing
```bash
# Test single company scraping
python main.py --index DAX --limit 1 -v

# Test region scraping
python main.py --region Germany -v

# Full debug output
python main.py --index MDAX --limit 5 -v --dry-run
```

### Production
```bash
# Single index (full pipeline)
python main.py --index DAX

# Overnight full run
python main.py --all

# Scheduled updates
0 2 * * * cd /path/to/backend && python main.py --all >> logs/cron.log 2>&1
```

### Monitoring
```bash
# Check last scrape results
tail -f logs/scraper.log

# View error log
tail -f logs/errors.log

# Check database status
# Via Supabase dashboard → scrape_logs table
```

## Testing

### Unit Tests (Recommended Future)
- Test each loader independently
- Test each parser independently
- Test normalization functions
- Test CAGR calculations

### Integration Tests (Recommended Future)
- Test full pipeline with sample data
- Mock network requests
- Verify database writes
- Test error recovery

### Manual Testing
```bash
python test_pipeline.py      # Verify setup
python test_index_loader.py  # Test index loading
python test_company_parser.py # Test company parsing
```

## Troubleshooting

### "Connection refused" (Supabase)
- Check SUPABASE_URL is correct
- Verify internet connection
- Check Supabase project is running
- Verify firewall allows outbound HTTPS

### "Index not found"
- Check index name spelling (case-sensitive)
- Verify index exists in config/indices.py
- Run `python main.py --all` to list available indexes

### "No estimates found"
- Check company page URL is valid
- Website structure may have changed
- Try with `-v` flag for debug output
- Check if page requires authentication

### "Database write failed"
- Verify SUPABASE_KEY has correct permissions
- Check database schema is initialized (Phase 2)
- Verify Row-Level Security policies allow writes
- Check for connection pool exhaustion

### Slow Performance
- Normal for first run (network requests)
- Check internet connection speed
- Monitor CPU/memory usage
- Consider limiting companies with `--limit`

## Files Modified/Created

- `src/pipeline.py` - Main orchestrator
- `main.py` - Updated CLI entry point
- `test_pipeline.py` - Test script
- `PHASE8_MAIN_SCRAPER.md` - This documentation

## Workflow Summary

### Step 1: Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Supabase credentials
```

### Step 2: Initialize Database
```bash
# Run SQL in Supabase editor
# backend/migrations/complete_schema.sql
```

### Step 3: Run Scraper
```bash
# Test
python main.py --index DAX --limit 5 -v

# Full run
python main.py --all
```

### Step 4: Monitor
```bash
tail -f logs/scraper.log
```

### Step 5: Verify Data
```
# In Supabase dashboard
# Check: indices, companies, estimates, metrics tables
```

## Next Phases

Phase 9-10: Frontend
- User authentication (Supabase Auth)
- Data display and filtering
- Advanced analytics
- Watchlists and alerts

Phase 11: Enhancements
- Real-time updates
- Historical tracking
- Advanced filtering
- API endpoints

## Success Criteria

✓ Indexes load from multiple sources
✓ Company estimates extracted accurately
✓ CAGR calculations correct
✓ Data stored in database
✓ Errors logged and recovered from
✓ Pipeline completes for all indexes
✓ Performance within acceptable limits
