-- Create companies table to store individual stock companies
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

-- Create indexes for common queries
CREATE INDEX idx_companies_index_id ON companies(index_id);
CREATE INDEX idx_companies_isin ON companies(isin);
CREATE INDEX idx_companies_wkn ON companies(wkn);
CREATE INDEX idx_companies_title ON companies USING GIN (to_tsvector('english', title));

-- Add comments
COMMENT ON TABLE companies IS 'Individual stock companies belonging to indexes';
COMMENT ON COLUMN companies.index_id IS 'Reference to the parent index';
COMMENT ON COLUMN companies.wkn IS 'German securities identification number (Wertpapierkennnummer)';
COMMENT ON COLUMN companies.isin IS 'International Securities Identification Number';
COMMENT ON COLUMN companies.last_scrape_status IS 'Status of last data scrape attempt';
COMMENT ON COLUMN companies.error_message IS 'Error details if scrape failed';
