-- ============================================================
-- Insert Initial Index Configurations
-- ============================================================
-- Run this after creating the tables to populate all 12 indexes

INSERT INTO indices (name, display_name, description, region, currency, data_source)
VALUES
  ('DAX', 'DAX', 'German Blue Chip Index - 40 largest German companies', 'Germany', 'EUR', 'finanzen_net'),
  ('MDAX', 'MDAX', 'Mid-Cap German Companies - 50 companies', 'Germany', 'EUR', 'finanzen_net'),
  ('SDAX', 'SDAX', 'Small-Cap German Companies - 70 companies', 'Germany', 'EUR', 'finanzen_net'),
  ('TecDAX', 'TecDAX', 'Technology-focused German Companies - 30 companies', 'Germany', 'EUR', 'finanzen_net'),
  ('STOXX50', 'Euro Stoxx 50', 'Leading blue-chip companies across Eurozone', 'Europe', 'EUR', 'yahoo_finance'),
  ('STOXX600', 'STOXX 600', 'Large, mid and small-cap companies across Europe', 'Europe', 'EUR', 'yahoo_finance'),
  ('CAC40', 'CAC 40', 'French blue-chip index - 40 companies', 'Europe', 'EUR', 'yahoo_finance'),
  ('FTSE100', 'FTSE 100', 'UK blue-chip index - 100 companies', 'Europe', 'GBP', 'yahoo_finance'),
  ('SPX', 'S&P 500', '500 largest US companies', 'USA', 'USD', 'yahoo_finance'),
  ('CCMP', 'NASDAQ 100', '100 largest non-financial companies on NASDAQ', 'USA', 'USD', 'yahoo_finance'),
  ('RUT', 'Russell 2000', 'Small-cap US companies - 2000 companies', 'USA', 'USD', 'yahoo_finance')
ON CONFLICT (name) DO NOTHING;

-- Verify insertion
SELECT COUNT(*) as total_indexes,
       COUNT(CASE WHEN region = 'Germany' THEN 1 END) as german,
       COUNT(CASE WHEN region = 'Europe' THEN 1 END) as european,
       COUNT(CASE WHEN region = 'USA' THEN 1 END) as usa
FROM indices;
