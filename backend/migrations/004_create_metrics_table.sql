-- Create metrics table for calculated company-level metrics
CREATE TABLE IF NOT EXISTS metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,

  -- CAGR (Compound Annual Growth Rate) values
  revenue_cagr_percent DECIMAL(10, 4),
  dividend_cagr_percent DECIMAL(10, 4),
  dividend_yield_cagr_percent DECIMAL(10, 4),
  eps_cagr_percent DECIMAL(10, 4),
  pe_ratio_cagr_percent DECIMAL(10, 4),

  -- Estimate period information
  first_estimate_year INTEGER,
  last_estimate_year INTEGER,
  estimate_count INTEGER DEFAULT 0,

  -- Data quality tracking
  data_completeness JSONB DEFAULT '{}'::JSONB,

  -- Timestamps
  calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on company_id (already unique)
CREATE INDEX idx_metrics_company_id ON metrics(company_id);

-- Add comments
COMMENT ON TABLE metrics IS 'Calculated metrics for each company (CAGR, data completeness)';
COMMENT ON COLUMN metrics.revenue_cagr_percent IS 'Compound annual growth rate for revenue (%)';
COMMENT ON COLUMN metrics.dividend_cagr_percent IS 'Compound annual growth rate for dividends (%)';
COMMENT ON COLUMN metrics.dividend_yield_cagr_percent IS 'Compound annual growth rate for dividend yield (%)';
COMMENT ON COLUMN metrics.eps_cagr_percent IS 'Compound annual growth rate for EPS (%)';
COMMENT ON COLUMN metrics.pe_ratio_cagr_percent IS 'Compound annual growth rate for P/E ratio (%)';
COMMENT ON COLUMN metrics.data_completeness IS 'JSON object tracking completeness per metric (e.g., {"revenue": true, "dividend": false})';
