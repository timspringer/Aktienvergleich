-- Enable Row-Level Security on all tables
ALTER TABLE indices ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- INDICES - Public Read Access
-- ============================================================
CREATE POLICY "indices_read_public" ON indices
  FOR SELECT USING (true);

-- ============================================================
-- COMPANIES - Public Read Access
-- ============================================================
CREATE POLICY "companies_read_public" ON companies
  FOR SELECT USING (true);

-- ============================================================
-- ESTIMATES - Public Read Access
-- ============================================================
CREATE POLICY "estimates_read_public" ON estimates
  FOR SELECT USING (true);

-- ============================================================
-- METRICS - Public Read Access
-- ============================================================
CREATE POLICY "metrics_read_public" ON metrics
  FOR SELECT USING (true);

-- ============================================================
-- FILTER PRESETS - User-scoped Access
-- ============================================================
-- Users can only see their own filter presets
CREATE POLICY "filter_presets_read" ON filter_presets
  FOR SELECT USING (auth.uid() = user_id);

-- Users can create filter presets
CREATE POLICY "filter_presets_insert" ON filter_presets
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own filter presets
CREATE POLICY "filter_presets_update" ON filter_presets
  FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own filter presets
CREATE POLICY "filter_presets_delete" ON filter_presets
  FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- SCRAPE LOGS - Admin-only (future enhancement)
-- For now, disable all access except SELECT via stored procedures
-- ============================================================
CREATE POLICY "scrape_logs_read_public" ON scrape_logs
  FOR SELECT USING (true);

-- Grant permissions to authenticated users
GRANT SELECT ON indices TO authenticated;
GRANT SELECT ON companies TO authenticated;
GRANT SELECT ON estimates TO authenticated;
GRANT SELECT ON metrics TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON filter_presets TO authenticated;
GRANT SELECT ON scrape_logs TO authenticated;

-- Grant permissions to service role (for backend)
GRANT SELECT, INSERT, UPDATE, DELETE ON indices TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON companies TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON estimates TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON metrics TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON scrape_logs TO service_role;
