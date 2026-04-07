# Database Migrations

This directory contains SQL migrations for setting up the Aktienvergleich database in Supabase.

## Setup Instructions

### Option 1: Run Complete Schema (Recommended)

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **SQL Editor**
4. Create a new query
5. Copy the contents of `complete_schema.sql`
6. Paste into the SQL Editor
7. Click **Run**

This will create all tables, indexes, and RLS policies in one go.

### Option 2: Run Individual Migrations (Sequential)

If you prefer to run migrations step by step:

1. Go to **SQL Editor** in Supabase
2. Run each migration in order:
   1. `001_create_indices_table.sql`
   2. `002_create_companies_table.sql`
   3. `003_create_estimates_table.sql`
   4. `004_create_metrics_table.sql`
   5. `005_create_filter_presets_table.sql`
   6. `006_create_scrape_logs_table.sql`
   7. `007_setup_rls.sql`

## Table Structure

### indices
- Stores stock index configurations (DAX, S&P 500, etc.)
- **Fields**: id, name, display_name, region, currency, member_count, data_source

### companies
- Stores individual stocks within each index
- **Fields**: id, index_id, title, wkn, isin, source_url, last_scrape_status

### estimates
- Annual financial estimates for each company
- **Fields**: id, company_id, fiscal_year, revenue, dividend, eps, pe_ratio, price_target
- **Indexes**: By company, by year, by P/E ratio (for filtering)

### metrics
- Calculated metrics per company (CAGR values, data completeness)
- **Fields**: id, company_id, revenue_cagr, dividend_cagr, eps_cagr, etc.
- **One row per company**

### filter_presets
- User-saved filter configurations
- **Fields**: id, user_id, index_id, name, filter_config (JSON)
- **RLS**: Users can only see/edit their own presets

### scrape_logs
- Tracking of all scraping runs
- **Fields**: id, index_id, status, total_companies, successful, failed, error_message

## Security

### Row-Level Security (RLS) Policies

- **Public Tables**: `indices`, `companies`, `estimates`, `metrics`, `scrape_logs`
  - Anyone can read
  - Only service_role (backend) can insert/update/delete

- **User-Scoped Tables**: `filter_presets`
  - Users can only see their own presets
  - Users can CRUD only their own presets

## Initial Data

After running migrations, you should populate the `indices` table with the 12 configured indexes.

### Insert Indexes

```sql
INSERT INTO indices (name, display_name, description, region, currency, data_source)
VALUES
  ('DAX', 'DAX', 'German Blue Chip Index (40 companies)', 'Germany', 'EUR', 'finanzen_net'),
  ('MDAX', 'MDAX', 'Mid-Cap German Companies', 'Germany', 'EUR', 'finanzen_net'),
  ('SDAX', 'SDAX', 'Small-Cap German Companies', 'Germany', 'EUR', 'finanzen_net'),
  ('TecDAX', 'TecDAX', 'Technology-focused German Companies', 'Germany', 'EUR', 'finanzen_net'),
  ('STOXX50', 'Euro Stoxx 50', 'Leading blue-chip companies across Eurozone', 'Europe', 'EUR', 'yahoo_finance'),
  ('STOXX600', 'STOXX 600', 'Large, mid and small-cap companies across Europe', 'Europe', 'EUR', 'yahoo_finance'),
  ('CAC40', 'CAC 40', 'French blue-chip index', 'Europe', 'EUR', 'yahoo_finance'),
  ('FTSE100', 'FTSE 100', 'UK blue-chip index', 'Europe', 'GBP', 'yahoo_finance'),
  ('SPX', 'S&P 500', '500 largest US companies', 'USA', 'USD', 'yahoo_finance'),
  ('CCMP', 'NASDAQ 100', '100 largest non-financial companies on NASDAQ', 'USA', 'USD', 'yahoo_finance'),
  ('RUT', 'Russell 2000', 'Small-cap US companies', 'USA', 'USD', 'yahoo_finance');
```

## Verification

After running the migrations, verify everything is set up correctly:

### Check Tables Exist
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Check RLS is Enabled
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

### Check Indexes
```sql
SELECT indexname FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename;
```

### Check Policies
```sql
SELECT tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public';
```

## Troubleshooting

### "relation already exists"
- The table might already exist from a previous migration attempt
- Drop and recreate:
  ```sql
  DROP TABLE IF EXISTS table_name CASCADE;
  ```

### RLS Policies Not Working
- Make sure `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` was executed
- Check that policies exist with: `SELECT * FROM pg_policies`

### Performance Issues
- Check that all indexes were created: `SELECT * FROM pg_indexes WHERE schemaname = 'public'`
- Analyze table statistics: `ANALYZE indices; ANALYZE companies; ...`

## Next Steps

After database setup:

1. Install Python backend dependencies: `pip install -r requirements.txt`
2. Configure `.env` with Supabase credentials
3. Create initial index records in database
4. Build the index loader (Phase 3)
5. Build company parser (Phase 4)

## References

- [Supabase SQL Editor](https://app.supabase.com)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [Supabase Row-Level Security](https://supabase.com/docs/guides/auth/row-level-security)
