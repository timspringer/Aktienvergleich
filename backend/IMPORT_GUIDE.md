# Financial Estimates Import Guide

Progressive import of German DAX stock data extracted by ChatGPT.

## Overview

This workflow allows you to:
1. Extract financial data from finanzen.net using ChatGPT
2. Format it as CSV
3. Import into Supabase using Claude Code
4. Repeat progressively to load all DAX stocks

## Quick Start

### Step 1: Extract Data with ChatGPT

Ask ChatGPT to extract financial estimates from finanzen.net for a company. Example prompt:

```
Please extract financial estimates for Deutsche Telekom (ISIN: DE0005140008) from:
https://www.finanzen.net/aktien/deutsche-telekom-aktie

I need:
- Fiscal years 2024, 2025, 2026
- Revenue (Umsatz)
- Dividend (Dividende)
- Dividend Yield (Dividendenrendite)
- EPS (Gewinn je Aktie)
- P/E Ratio (KGV)
- Average Price Target (Mittleres Kursziel)

Format as CSV with these columns:
isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent,eps,pe_ratio,avg_price_target,currency,source_url
```

### Step 2: Prepare CSV File

ChatGPT will provide CSV data. Save it as `dax_estimates.csv` in the `backend/` directory.

#### CSV Format

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| isin | string | ✓ | Company ISIN (e.g., DE0005140008) |
| title | string | ✓ | Company name |
| fiscal_year | integer | ✓ | Year (e.g., 2024) |
| revenue_amount | number | | In millions EUR/USD |
| dividend | number | | Per share |
| dividend_yield_percent | number | | As percentage (e.g., 2.5) |
| eps | number | | Earnings per share |
| pe_ratio | number | | Price-to-earnings ratio |
| avg_price_target | number | | Target price |
| currency | string | | Default: EUR. Use EUR, USD, GBP |
| source_url | string | | Source page URL |

#### Numeric Value Format

- Handles both formats: `1.234,56` (German) or `1,234.56` (US)
- Use `NV` for missing values
- Leave empty cells for missing data

### Step 3: Run Import on Local Terminal

Navigate to backend directory and run:

```bash
cd backend

# Single import
python -m src.import_estimates --file dax_estimates.csv --index DAX

# With verbose output
python -m src.import_estimates --file dax_estimates.csv --index DAX -v
```

#### Command Options

```
--file <path>          Path to CSV file (required)
--index <name>         Index name: DAX, MDAX, SDAX, TecDAX (required)
--skip-validation      Skip validation checks (optional)
```

### Step 4: Monitor Progress

The script outputs:
- Number of companies created/updated
- Number of estimates inserted
- Number of metric sets calculated
- Any warnings/errors

Example output:
```
======================================================================
Importing estimates from: dax_estimates.csv
Index: DAX
======================================================================
Read 10 rows from CSV
Parsed 2 unique companies

Processing: Deutsche Telekom (ISIN: DE0005140008)
  Fiscal years: [2024, 2025, 2026]
Created company: Deutsche Telekom (ISIN: DE0005140008)
✓ 3 estimates inserted
✓ Metrics calculated

Processing: Sample Company (ISIN: DE0008469008)
  Fiscal years: [2024, 2025]
Created company: Sample Company (ISIN: DE0008469008)
✓ 2 estimates inserted
✓ Metrics calculated

======================================================================
Import Summary
======================================================================
Companies created: 2
Estimates inserted: 5
Metrics calculated: 2
======================================================================
```

## Workflow: Progressive DAX Loading

### Phase 1: Test with Single Company

1. Ask ChatGPT to extract **Deutsche Telekom** (most liquid DAX stock)
2. Create `test_import.csv`
3. Run: `python -m src.import_estimates --file test_import.csv --index DAX`
4. Verify in Supabase dashboard

### Phase 2: Add 5-10 More Companies

Extract data for:
- Siemens (SIE)
- SAP (SAP)
- BASF (BAS)
- BMW (BMW)
- Allianz (ALV)

Create `dax_batch2.csv` with their data and run import.

### Phase 3: Complete DAX Loading

Continue with remaining ~30 companies in batches of 5-10 per iteration.

## Handling Missing Data

If ChatGPT cannot extract a value:

- Use `NV` to indicate "Not Valid"
- Leave the cell empty
- Script will mark as `data_completeness[metric] = false`

Example:
```csv
isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent
DE0005140008,Deutsche Telekom,2026,NV,0.80,2.7
```

## Verification in Supabase

After import, verify in Supabase dashboard:

### Companies Table
- New company record created
- Correct `index_id` for DAX
- `last_scrape_status` = 'success'

### Estimates Table
- Multiple rows per company (one per fiscal year)
- All numeric fields populated or marked NV
- Correct `fiscal_year` values

### Metrics Table
- One row per company
- CAGR values calculated (e.g., `revenue_amount_cagr_percent`)
- `data_completeness` shows which metrics are complete

## Troubleshooting

### Error: "Index DAX not found in database"

Ensure DAX index exists in `indices` table. If missing:
```sql
INSERT INTO indices (name, display_name, region, currency, data_source) 
VALUES ('DAX', 'DAX', 'Germany', 'EUR', 'finanzen_net');
```

### Error: "ISIN must be unique"

CSV has duplicate ISINs for same company but different years. Script handles this by upserting estimates - should continue normally.

### Error: "Numeric value invalid"

Check CSV numeric format:
- Use decimal separator: `.` (period)
- Remove currency symbols
- Examples: `120000`, `0.70`, `2.5`

### Companies Created but No Estimates

Check that:
1. CSV has required columns: `fiscal_year`, numeric fields
2. Fiscal years are valid integers
3. At least one numeric field per row is non-empty

## Tips for ChatGPT Data Extraction

### Effective Prompts

✅ **Good:**
```
Please extract the financial estimates table for [Company] from:
[URL]

Focus on: revenue, dividend, EPS, P/E ratio for years 2024-2026.
Format as CSV with columns:
isin,title,fiscal_year,revenue_amount,dividend,eps,pe_ratio
```

❌ **Avoid:**
- Vague company references ("the first DAX stock")
- Requesting HTML tables (causes formatting issues)
- Multiple companies in single request (do one-by-one)

### Source URLs to Use

All from finanzen.net:
- List: `https://www.finanzen.net/index/dax`
- Individual: `https://www.finanzen.net/aktien/[ticker]`

### Extract Estimates Page

On each company page, look for "Schätzungen" (estimates) section with:
- Fiscal year columns
- Revenue row (Umsatz)
- Dividend row (Dividende)
- EPS row (Gewinn je Aktie)
- P/E ratio row (KGV)

## Dashboard Integration

Once data is imported:

1. Frontend automatically queries Supabase
2. Dashboard displays all imported companies
3. Filter by index (DAX selected)
4. Sort by metrics (CAGR, P/E, dividend yield, etc.)

No additional configuration needed.

## API Endpoints Used

The import script uses existing Supabase operations:
- `companies` table: CRUD operations
- `estimates` table: upsert fiscal year estimates
- `metrics` table: store calculated CAGR values

All operations use Supabase client from `src/supabase_client.py`.

## Next Steps

1. ✓ Create import script
2. Extract first batch with ChatGPT
3. Run import and verify
4. Repeat for remaining DAX companies
5. Add international indexes (Yahoo Finance data if needed)
