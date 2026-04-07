'use client'

import { useState } from 'react'
import { AuthGuard } from '@/components/AuthGuard'
import { StockTable } from '@/components/StockTable'
import { SearchBar } from '@/components/SearchBar'
import { IndexFilter } from '@/components/IndexFilter'
import { useAuth } from '@/lib/auth'

export default function DashboardPage() {
  const { user } = useAuth()
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState('')

  return (
    <AuthGuard>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Stock Comparison Dashboard</h2>
          <p className="text-gray-400">
            Compare valuations and metrics across global indexes
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-2">Search</label>
            <SearchBar value={search} onChange={setSearch} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Index</label>
            <IndexFilter value={selectedIndex} onChange={setSelectedIndex} />
          </div>
        </div>

        <div className="bg-secondary border border-slate-600 rounded p-6">
          <StockTable indexId={selectedIndex} search={search} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-secondary border border-slate-600 p-4 rounded">
            <h3 className="text-sm font-semibold text-accent mb-1">💡 Tip</h3>
            <p className="text-xs text-gray-400">
              Click column headers to sort by that metric
            </p>
          </div>
          <div className="bg-secondary border border-slate-600 p-4 rounded">
            <h3 className="text-sm font-semibold text-accent mb-1">🔍 Search</h3>
            <p className="text-xs text-gray-400">
              Search by company name, ISIN, or WKN
            </p>
          </div>
          <div className="bg-secondary border border-slate-600 p-4 rounded">
            <h3 className="text-sm font-semibold text-accent mb-1">📊 Metrics</h3>
            <p className="text-xs text-gray-400">
              View CAGR, P/E ratios, and more
            </p>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
