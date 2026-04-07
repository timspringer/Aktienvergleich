export interface Index {
  id: string
  name: string
  display_name: string
  description: string
  region: 'Germany' | 'Europe' | 'USA'
  currency: 'EUR' | 'USD' | 'GBP'
  member_count: number
  data_source: string
  last_updated: string
  created_at: string
}

export interface Company {
  id: string
  index_id: string
  title: string
  wkn: string
  isin: string
  source_url: string
  last_updated: string
  last_scrape_status: 'success' | 'partial' | 'failed'
  created_at: string
}

export interface Estimate {
  id: string
  company_id: string
  fiscal_year: number
  revenue_amount: number | null
  revenue_currency: 'EUR' | 'USD' | 'GBP'
  dividend: number | null
  dividend_yield_percent: number | null
  eps: number | null
  pe_ratio: number | null
  avg_price_target: number | null
  source_url: string
  created_at: string
  updated_at: string
}

export interface Metrics {
  id: string
  company_id: string
  revenue_cagr_percent: number | null
  dividend_cagr_percent: number | null
  dividend_yield_cagr_percent: number | null
  eps_cagr_percent: number | null
  pe_ratio_cagr_percent: number | null
  first_estimate_year: number
  last_estimate_year: number
  estimate_count: number
  data_completeness: Record<string, boolean>
  calculated_at: string
}

export interface FilterPreset {
  id: string
  user_id: string
  index_id: string
  name: string
  filter_config: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ScrapeLog {
  id: string
  index_id: string
  started_at: string
  completed_at: string | null
  status: 'running' | 'success' | 'partial' | 'failed'
  total_companies: number
  successful: number
  failed: number
  error_message: string | null
  created_at: string
}
