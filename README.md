# Aktienvergleich - Global Stock Index Data Collector

A web application for collecting, normalizing, and comparing stock valuation data across 12 global indexes (German, European, and US markets).

## Project Structure

```
aktienvergleich/
├── backend/                    # Python scraper & data processing
│   ├── config/
│   │   └── indices.py         # Index configurations
│   ├── src/
│   │   ├── loaders/           # Index member loaders (finanzen.net, Yahoo Finance, etc.)
│   │   ├── parsers/           # Company data parsers
│   │   ├── normalizer.py      # Data normalization
│   │   ├── calculations.py    # CAGR calculations
│   │   ├── supabase_client.py # Database operations
│   │   └── retry_utils.py     # Retry logic
│   ├── main.py                # Entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js 14 application
│   ├── app/                   # Next.js app directory
│   ├── components/            # React components
│   ├── lib/                   # Utilities and types
│   ├── package.json
│   └── .env.local.example
└── docs/
    └── API.md
```

## Quick Start

### Backend Setup

1. Create Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

4. Run scraper:
```bash
python main.py --index DAX              # Single index
python main.py --index DAX --limit 5    # With limit
python main.py --all                    # All indexes
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Setup environment:
```bash
cp .env.local.example .env.local
# Edit with your Supabase credentials
```

3. Run development server:
```bash
npm run dev
```

Visit http://localhost:3000

## Supported Indexes

### German (via finanzen.net)
- DAX (40 companies)
- MDAX (50 companies)
- SDAX (70 companies)
- TecDAX (30 companies)

### European (via Yahoo Finance & alternatives)
- Euro Stoxx 50
- STOXX 600
- CAC 40
- FTSE 100

### USA (via Yahoo Finance)
- S&P 500
- NASDAQ 100
- Russell 2000

## Features

- ✅ Multi-region stock data collection
- ✅ Automatic data normalization (German & English formats)
- ✅ CAGR calculations (Revenue, Dividends, EPS, P/E Ratio)
- ✅ User authentication (Supabase Auth)
- ✅ Advanced filtering and search
- ✅ Data quality tracking
- ✅ Robust error handling with fallbacks

## Database Schema

Key tables:
- `indices` - Index configurations
- `companies` - Stock companies
- `estimates` - Annual estimates per company
- `metrics` - Calculated metrics (CAGR, etc.)
- `filter_presets` - User-saved filters
- `scrape_logs` - Scraping history and errors

## Development Phases

1. ✅ Project Setup
2. ⏳ Database Setup
3. ⏳ Backend - Index Loader
4. ⏳ Backend - Company Parser
5. ⏳ Backend - Data Normalization
6. ⏳ Backend - CAGR Calculations
7. ⏳ Backend - Supabase Operations
8. ⏳ Backend - Main Scraper Entry Point
9. ⏳ Frontend - Authentication
10. ⏳ Frontend - Data Display
11. ⏳ Frontend - Admin Panel (Optional)
12. ⏳ Deployment

## Configuration

### Index Configuration
Modify `backend/config/indices.py` to add or modify indexes:

```python
"SPX": {
    "display_name": "S&P 500",
    "region": "USA",
    "currency": "USD",
    "data_source": "yahoo_finance",
    "ticker": "^GSPC",
}
```

### Environment Variables

**Backend (.env)**:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anonymous key
- `SCRAPER_TIMEOUT` - Request timeout in seconds
- `SCRAPER_RETRIES` - Number of retry attempts
- `SCRAPER_DELAY` - Delay between requests (seconds)

**Frontend (.env.local)**:
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key

## API Endpoints

Frontend API routes (Next.js):
- `GET /api/indices` - List all indexes
- `GET /api/companies?index_id=...` - List companies in index
- `GET /api/estimates?company_id=...` - Get company estimates
- `GET /api/metrics?company_id=...` - Get company metrics

## Data Quality

- Missing or invalid values are marked as "NV" (Not Valid)
- All CAGR values are calculated from original data, never imported
- Data completeness tracked per metric per company
- Source URLs maintained for all data points

## Error Handling

The system includes robust error handling:
1. Retry failed requests with exponential backoff
2. Fallback to alternative data sources
3. Log all errors for review
4. Continue processing other companies/indexes despite failures

## Contributing

When adding new features:
1. Follow the existing code structure
2. Add proper error handling
3. Update documentation
4. Test with both small and large datasets

## License

Private project

## Support

For issues or questions about the project, please check:
1. The plan file at `/root/.claude/plans/composed-churning-riddle.md`
2. Individual module documentation
3. Error logs in `backend/logs/`
