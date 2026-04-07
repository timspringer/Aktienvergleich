-- Create scrape_logs table for tracking data collection runs
CREATE TABLE IF NOT EXISTS scrape_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  index_id UUID NOT NULL REFERENCES indices(id) ON DELETE CASCADE,

  -- Execution times
  started_at TIMESTAMP WITH TIME ZONE NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,

  -- Status tracking
  status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'partial', 'failed')),

  -- Results
  total_companies INTEGER DEFAULT 0,
  successful INTEGER DEFAULT 0,
  failed INTEGER DEFAULT 0,

  -- Error details
  error_message TEXT,

  -- Additional metadata
  duration_seconds INTEGER,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_scrape_logs_index_id ON scrape_logs(index_id);
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status);
CREATE INDEX idx_scrape_logs_created_at ON scrape_logs(created_at DESC);
CREATE INDEX idx_scrape_logs_index_created ON scrape_logs(index_id, created_at DESC);

-- Add comments
COMMENT ON TABLE scrape_logs IS 'Log of all data scraping runs with results and errors';
COMMENT ON COLUMN scrape_logs.index_id IS 'Reference to the index being scraped';
COMMENT ON COLUMN scrape_logs.status IS 'Overall status of the scrape run';
COMMENT ON COLUMN scrape_logs.total_companies IS 'Total number of companies attempted';
COMMENT ON COLUMN scrape_logs.successful IS 'Number of companies successfully scraped';
COMMENT ON COLUMN scrape_logs.failed IS 'Number of companies that failed';
COMMENT ON COLUMN scrape_logs.duration_seconds IS 'Total execution time in seconds';
