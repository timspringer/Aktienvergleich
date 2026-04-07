-- Create indices table to store stock index configurations
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

-- Create index on region for quick filtering
CREATE INDEX idx_indices_region ON indices(region);

-- Add comment for documentation
COMMENT ON TABLE indices IS 'Stock index configurations (DAX, S&P 500, etc.)';
COMMENT ON COLUMN indices.name IS 'Unique identifier for the index (e.g., DAX, SPX)';
COMMENT ON COLUMN indices.region IS 'Geographic region: Germany, Europe, or USA';
COMMENT ON COLUMN indices.currency IS 'Base currency: EUR, USD, or GBP';
COMMENT ON COLUMN indices.member_count IS 'Number of companies in the index';
COMMENT ON COLUMN indices.data_source IS 'Primary data source (finanzen_net, yahoo_finance)';
