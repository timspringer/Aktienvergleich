'use client'

import { useState, useEffect } from 'react'
import { ChevronUp, ChevronDown, Loader } from 'lucide-react'

interface Stock {
  id: string
  title: string
  wkn: string | null
  isin: string | null
  last_scrape_status: string
  indices: {
    id: string
    name: string
    display_name: string
    currency: string
  }
  estimates: Array<{
    fiscal_year: number
    revenue_amount: number | null
    dividend: number | null
    dividend_yield_percent: number | null
    eps: number | null
    pe_ratio: number | null
    avg_price_target: number | null
  }>
  metrics: Array<{
    revenue_cagr_percent: number | null
    dividend_cagr_percent: number | null
    dividend_yield_cagr_percent: number | null
    eps_cagr_percent: number | null
    pe_ratio_cagr_percent: number | null
    estimate_count: number
    first_estimate_year: number
    last_estimate_year: number
  }>
}

interface StockTableProps {
  indexId?: string
  search?: string
}

export function StockTable({ indexId, search }: StockTableProps) {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState('title')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const limit = 25

  useEffect(() => {
    fetchStocks()
  }, [indexId, search, sortBy, sortOrder, page])

  const fetchStocks = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString(),
        sortBy,
        sortOrder,
      })

      if (indexId) params.append('indexId', indexId)
      if (search) params.append('search', search)

      const response = await fetch(`/api/stocks?${params}`)
      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch stocks')
      }

      setStocks(result.data)
      setTotal(result.count)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setPage(0)
  }

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <div className="w-4 h-4" />
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    )
  }

  if (loading && stocks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader className="w-8 h-8 animate-spin mx-auto mb-2 text-accent" />
          <p className="text-gray-400">Loading stocks...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 p-4 rounded">
        <p className="text-red-200">Error: {error}</p>
      </div>
    )
  }

  if (stocks.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">No stocks found</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-secondary border-b border-slate-600">
            <tr>
              <th
                onClick={() => toggleSort('title')}
                className="px-4 py-3 text-left font-semibold cursor-pointer hover:bg-primary transition-colors"
              >
                <div className="flex items-center gap-2">
                  Company
                  <SortIcon field="title" />
                </div>
              </th>
              <th
                onClick={() => toggleSort('isin')}
                className="px-4 py-3 text-left font-semibold cursor-pointer hover:bg-primary transition-colors"
              >
                <div className="flex items-center gap-2">
                  ISIN/WKN
                  <SortIcon field="isin" />
                </div>
              </th>
              <th className="px-4 py-3 text-left font-semibold">Years</th>
              <th className="px-4 py-3 text-right font-semibold">
                Latest P/E
              </th>
              <th className="px-4 py-3 text-right font-semibold">
                Revenue CAGR
              </th>
              <th className="px-4 py-3 text-right font-semibold">
                EPS CAGR
              </th>
              <th className="px-4 py-3 text-right font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock, idx) => {
              const metrics = stock.metrics?.[0]
              const latestEstimate = stock.estimates?.sort(
                (a, b) => b.fiscal_year - a.fiscal_year
              )?.[0]

              return (
                <tr
                  key={stock.id}
                  className={`border-b border-slate-700 hover:bg-secondary/50 transition-colors ${
                    idx % 2 === 0 ? '' : 'bg-primary/30'
                  }`}
                >
                  <td className="px-4 py-3 font-medium">
                    <div>
                      <p className="text-white">{stock.title}</p>
                      <p className="text-xs text-gray-500">
                        {stock.indices?.display_name}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {stock.isin && (
                      <div>
                        <p>{stock.isin}</p>
                        {stock.wkn && (
                          <p className="text-xs text-gray-500">{stock.wkn}</p>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {metrics ? (
                      <span>
                        {metrics.first_estimate_year} - {metrics.last_estimate_year}
                      </span>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {latestEstimate?.pe_ratio ? (
                      <span className="font-medium">
                        {latestEstimate.pe_ratio.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {metrics?.revenue_cagr_percent !== null &&
                    metrics?.revenue_cagr_percent !== undefined ? (
                      <span
                        className={
                          metrics.revenue_cagr_percent > 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }
                      >
                        {metrics.revenue_cagr_percent.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {metrics?.eps_cagr_percent !== null &&
                    metrics?.eps_cagr_percent !== undefined ? (
                      <span
                        className={
                          metrics.eps_cagr_percent > 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }
                      >
                        {metrics.eps_cagr_percent.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        stock.last_scrape_status === 'success'
                          ? 'bg-green-900/30 text-green-200'
                          : stock.last_scrape_status === 'partial'
                            ? 'bg-yellow-900/30 text-yellow-200'
                            : 'bg-red-900/30 text-red-200'
                      }`}
                    >
                      {stock.last_scrape_status || 'Unknown'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of{' '}
          {total}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1 bg-secondary border border-slate-600 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:border-accent transition-colors"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-gray-400">
            Page {page + 1} of {Math.ceil(total / limit)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= total}
            className="px-3 py-1 bg-secondary border border-slate-600 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:border-accent transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
