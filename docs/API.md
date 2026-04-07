# Aktienvergleich API Documentation

## Database Schema

All data is stored in Supabase PostgreSQL database.

### Tables

#### indices
```sql
CREATE TABLE indices (
  id UUID PRIMARY KEY,
  name VARCHAR UNIQUE,
  display_name VARCHAR,
  description TEXT,
  region VARCHAR,
  currency VARCHAR,
  member_count INTEGER,
  data_source VARCHAR,
  last_updated TIMESTAMP,
  created_at TIMESTAMP
);
```

#### companies
```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY,
  index_id UUID REFERENCES indices(id),
  title VARCHAR,
  wkn VARCHAR,
  isin VARCHAR,
  source_url TEXT,
  last_updated TIMESTAMP,
  last_scrape_status VARCHAR,
  created_at TIMESTAMP
);
```

#### estimates
```sql
CREATE TABLE estimates (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  fiscal_year INTEGER,
  revenue_amount DECIMAL,
  revenue_currency VARCHAR,
  dividend DECIMAL,
  dividend_yield_percent DECIMAL,
  eps DECIMAL,
  pe_ratio DECIMAL,
  avg_price_target DECIMAL,
  source_url TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### metrics
```sql
CREATE TABLE metrics (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  revenue_cagr_percent DECIMAL,
  dividend_cagr_percent DECIMAL,
  dividend_yield_cagr_percent DECIMAL,
  eps_cagr_percent DECIMAL,
  pe_ratio_cagr_percent DECIMAL,
  first_estimate_year INTEGER,
  last_estimate_year INTEGER,
  estimate_count INTEGER,
  data_completeness JSONB,
  calculated_at TIMESTAMP
);
```

#### filter_presets
```sql
CREATE TABLE filter_presets (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  index_id UUID REFERENCES indices(id),
  name VARCHAR,
  filter_config JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### scrape_logs
```sql
CREATE TABLE scrape_logs (
  id UUID PRIMARY KEY,
  index_id UUID REFERENCES indices(id),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status VARCHAR,
  total_companies INTEGER,
  successful INTEGER,
  failed INTEGER,
  error_message TEXT,
  created_at TIMESTAMP
);
```

## Frontend API Routes

### GET /api/indices
List all configured indexes.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "DAX",
    "display_name": "DAX",
    "region": "Germany",
    "currency": "EUR",
    "member_count": 40,
    "last_updated": "2024-01-15T10:00:00Z"
  }
]
```

### GET /api/companies
List companies in a specific index.

**Query Parameters:**
- `index_id` (required): UUID of the index

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "SAP SE",
    "wkn": "716460",
    "isin": "DE0007164600",
    "last_scrape_status": "success"
  }
]
```

### GET /api/estimates
Get all estimates for a company.

**Query Parameters:**
- `company_id` (required): UUID of the company

**Response:**
```json
[
  {
    "id": "uuid",
    "fiscal_year": 2024,
    "revenue_amount": 28000,
    "revenue_currency": "EUR",
    "dividend": 2.5,
    "dividend_yield_percent": 1.2,
    "eps": 7.5,
    "pe_ratio": 25.0,
    "avg_price_target": 187.5
  }
]
```

### GET /api/metrics
Get calculated metrics for a company.

**Query Parameters:**
- `company_id` (required): UUID of the company

**Response:**
```json
{
  "id": "uuid",
  "revenue_cagr_percent": 5.2,
  "dividend_cagr_percent": 3.1,
  "eps_cagr_percent": 6.8,
  "first_estimate_year": 2024,
  "last_estimate_year": 2028,
  "estimate_count": 5,
  "data_completeness": {
    "revenue": true,
    "dividend": true,
    "eps": true,
    "pe_ratio": false
  }
}
```

## Backend CLI

### main.py

```bash
# Single index
python main.py --index DAX

# With company limit
python main.py --index SPX --limit 10

# Multiple indexes
python main.py --indexes DAX,MDAX,SPX

# All configured indexes
python main.py --all

# Verbose logging
python main.py --index DAX --verbose

# Dry run (no database writes)
python main.py --index DAX --dry-run
```

## Data Format Standards

### Numbers
- Revenue: Stored in millions (EUR/USD/GBP)
- Dividend: Per share, in base currency
- Dividend Yield: Percentage (0-100)
- EPS: Per share, in base currency
- P/E Ratio: Unitless ratio
- Price Target: In base currency
- CAGR: Percentage with 2 decimal places (-100.00 to 1000.00)

### Missing Data
- Represented as null in database
- Represented as "NV" (Not Valid) when exported to UI
- Never calculated or interpolated

### Date Format
- ISO 8601: `YYYY-MM-DDTHH:MM:SSZ`
- Fiscal years: Integer (e.g., 2024, 2025)

## Authentication

### User Signup/Login
Via Supabase Auth (JWT tokens).

**Frontend Usage:**
```typescript
import { supabase } from '@/lib/supabase'

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password'
})

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})
```

### Row-Level Security (RLS)

- Public read access to all indexes, companies, estimates, metrics
- Authenticated users can create and modify their own filter presets
- Admin role can modify scrape logs (future enhancement)

## Error Handling

### Scraper Errors

Logged in `scrape_logs` table with:
- HTTP errors (status codes)
- Timeout errors
- Parse errors
- Database errors

### Frontend Errors

Standard HTTP status codes:
- 200: Success
- 400: Invalid parameters
- 404: Not found
- 500: Server error

## Rate Limiting

- Per-source request delays configured in `.env`
- Exponential backoff on failures
- Respectful of target websites' robots.txt and ToS

## Performance

### Indexes
- `companies(index_id)` - Quick company lookups
- `estimates(company_id, fiscal_year)` - Time series queries
- `metrics(company_id)` - Single company metrics
- `scrape_logs(index_id, created_at)` - Recent scrapes

### Pagination
- Default: 50 rows
- Maximum: 1000 rows
- Use `OFFSET` for pagination

## Future Enhancements

- Real-time data updates
- Historical data tracking
- Currency conversion utilities
- Advanced analytics endpoints
- Data export (CSV, Excel)
