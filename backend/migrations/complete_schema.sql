-- ============================================================
-- Aktienvergleich Complete Database Schema
-- ============================================================
-- This file contains the complete schema for Supabase PostgreSQL
-- Run this in Supabase SQL Editor if running migrations individually fails
-- ============================================================

-- ============================================================
-- 1. INDICES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS indices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  description TEXT,
  region VARCHAR(20) NOT NULL CHECK (region IN ('Germany', 'Europe', 'USA')),
  currency VARCHAR(3) NOT NULL CHECK (currency IN ('EUR', 'USD', 'GBP')),
  member_count INTEGER DEFAULT 0,
  data_source VARCHAR(50) NOT NULL,
  last_updated TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indices_region ON indices(region);
COMMENT ON TABLE indices IS 'Stock index configurations (DAX, S&P 500, etc.)';

-- ============================================================
-- 2. COMPANIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  index_id UUID NOT NULL REFERENCES indices(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  wkn VARCHAR(20),
  isin VARCHAR(20),
  source_url TEXT,
  last_updated TIMESTAMP WITH TIME ZONE,
  last_scrape_status VARCHAR(20) DEFAULT 'pending' CHECK (last_scrape_status IN ('success', 'partial', 'failed', 'pending')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(index_id, isin)
);

CREATE INDEX idx_companies_index_id ON companies(index_id);
CREATE INDEX idx_companies_isin ON companies(isin);
CREATE INDEX idx_companies_wkn ON companies(wkn);
CREATE INDEX idx_companies_title ON companies USING GIN (to_tsvector('english', title));
COMMENT ON TABLE companies IS 'Individual stock companies belonging to indexes';

-- ============================================================
-- 3. ESTIMATES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS estimates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  fiscal_year INTEGER NOT NULL CHECK (fiscal_year > 1900 AND fiscal_year < 3000),
  revenue_amount DECIMAL(15, 2),
  revenue_currency VARCHAR(3) CHECK (revenue_currency IN ('EUR', 'USD', 'GBP')),
  dividend DECIMAL(10, 4),
  dividend_yield_percent DECIMAL(10, 4),
  eps DECIMAL(10, 4),
  pe_ratio DECIMAL(10, 4),
  avg_price_target DECIMAL(12, 2),
  source_url TEXT,
  data_source VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(company_id, fiscal_year)
);

CREATE INDEX idx_estimates_company_id ON estimates(company_id);
CREATE INDEX idx_estimates_fiscal_year ON estimates(fiscal_year);
CREATE INDEX idx_estimates_company_year ON estimates(company_id, fiscal_year);
CREATE INDEX idx_estimates_pe_ratio ON estimates(pe_ratio);
CREATE INDEX idx_estimates_dividend_yield ON estimates(dividend_yield_percent);
COMMENT ON TABLE estimates IS 'Annual financial estimates for companies';

-- ============================================================
-- 4. METRICS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
  revenue_cagr_percent DECIMAL(10, 4),
  dividend_cagr_percent DECIMAL(10, 4),
  dividend_yield_cagr_percent DECIMAL(10, 4),
  eps_cagr_percent DECIMAL(10, 4),
  pe_ratio_cagr_percent DECIMAL(10, 4),
  first_estimate_year INTEGER,
  last_estimate_year INTEGER,
  estimate_count INTEGER DEFAULT 0,
  data_completeness JSONB DEFAULT '{}'::JSONB,
  calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_company_id ON metrics(company_id);
COMMENT ON TABLE metrics IS 'Calculated metrics for each company (CAGR, data completeness)';

-- ============================================================
-- 5. FILTER PRESETS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS filter_presets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  index_id UUID NOT NULL REFERENCES indices(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  filter_config JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_filter_presets_user_id ON filter_presets(user_id);
CREATE INDEX idx_filter_presets_index_id ON filter_presets(index_id);
CREATE INDEX idx_filter_presets_user_index ON filter_presets(user_id, index_id);
COMMENT ON TABLE filter_presets IS 'User-saved filter configurations for stock screening';

-- ============================================================
-- 6. SCRAPE LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS scrape_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  index_id UUID NOT NULL REFERENCES indices(id) ON DELETE CASCADE,
  started_at TIMESTAMP WITH TIME ZONE NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,
  status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'partial', 'failed')),
  total_companies INTEGER DEFAULT 0,
  successful INTEGER DEFAULT 0,
  failed INTEGER DEFAULT 0,
  error_message TEXT,
  duration_seconds INTEGER,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scrape_logs_index_id ON scrape_logs(index_id);
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status);
CREATE INDEX idx_scrape_logs_created_at ON scrape_logs(created_at DESC);
CREATE INDEX idx_scrape_logs_index_created ON scrape_logs(index_id, created_at DESC);
COMMENT ON TABLE scrape_logs IS 'Log of all data scraping runs with results and errors';

-- ============================================================
-- 7. ROW-LEVEL SECURITY POLICIES
-- ============================================================
ALTER TABLE indices ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_logs ENABLE ROW LEVEL SECURITY;

-- Public read access for all main data tables
CREATE POLICY "indices_read_public" ON indices FOR SELECT USING (true);
CREATE POLICY "companies_read_public" ON companies FOR SELECT USING (true);
CREATE POLICY "estimates_read_public" ON estimates FOR SELECT USING (true);
CREATE POLICY "metrics_read_public" ON metrics FOR SELECT USING (true);
CREATE POLICY "scrape_logs_read_public" ON scrape_logs FOR SELECT USING (true);

-- User-scoped filter presets
CREATE POLICY "filter_presets_read" ON filter_presets
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "filter_presets_insert" ON filter_presets
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "filter_presets_update" ON filter_presets
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "filter_presets_delete" ON filter_presets
  FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- 8. PERMISSIONS
-- ============================================================
GRANT SELECT ON indices TO authenticated;
GRANT SELECT ON companies TO authenticated;
GRANT SELECT ON estimates TO authenticated;
GRANT SELECT ON metrics TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON filter_presets TO authenticated;
GRANT SELECT ON scrape_logs TO authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON indices TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON companies TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON estimates TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON metrics TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON scrape_logs TO service_role;
