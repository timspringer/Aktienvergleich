-- Create estimates table for annual financial estimates per company
CREATE TABLE IF NOT EXISTS estimates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  fiscal_year INTEGER NOT NULL CHECK (fiscal_year > 1900 AND fiscal_year < 3000),

  -- Revenue estimates
  revenue_amount DECIMAL(15, 2),
  revenue_currency VARCHAR(3) CHECK (revenue_currency IN ('EUR', 'USD', 'GBP')),

  -- Dividend information
  dividend DECIMAL(10, 4),
  dividend_yield_percent DECIMAL(10, 4),

  -- Per-share metrics
  eps DECIMAL(10, 4),

  -- Valuation metrics
  pe_ratio DECIMAL(10, 4),
  avg_price_target DECIMAL(12, 2),

  -- Source tracking
  source_url TEXT,
  data_source VARCHAR(50),

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- Ensure unique combination of company and year
  UNIQUE(company_id, fiscal_year)
);

-- Create indexes for common queries
CREATE INDEX idx_estimates_company_id ON estimates(company_id);
CREATE INDEX idx_estimates_fiscal_year ON estimates(fiscal_year);
CREATE INDEX idx_estimates_company_year ON estimates(company_id, fiscal_year);
CREATE INDEX idx_estimates_pe_ratio ON estimates(pe_ratio);
CREATE INDEX idx_estimates_dividend_yield ON estimates(dividend_yield_percent);

-- Add comments
COMMENT ON TABLE estimates IS 'Annual financial estimates for companies';
COMMENT ON COLUMN estimates.fiscal_year IS 'Fiscal year (actual or estimated)';
COMMENT ON COLUMN estimates.revenue_amount IS 'Revenue in millions of base currency';
COMMENT ON COLUMN estimates.dividend IS 'Dividend per share';
COMMENT ON COLUMN estimates.dividend_yield_percent IS 'Dividend yield as percentage';
COMMENT ON COLUMN estimates.eps IS 'Earnings per share';
COMMENT ON COLUMN estimates.pe_ratio IS 'Price-to-earnings ratio';
COMMENT ON COLUMN estimates.avg_price_target IS 'Average analyst price target';
COMMENT ON COLUMN estimates.data_source IS 'Source of the estimate data';
