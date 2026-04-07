'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import type { Index } from '@/lib/types'
import { ArrowRight } from 'lucide-react'

export default function Home() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [indexes, setIndexes] = useState<Index[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchIndexes() {
      try {
        const { data, error } = await supabase
          .from('indices')
          .select('*')
          .order('region')

        if (error) throw error
        setIndexes(data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load indexes')
      } finally {
        setLoading(false)
      }
    }

    fetchIndexes()
  }, [])

  if (authLoading) {
    return <div className="text-center py-12"><p className="text-gray-400">Loading...</p></div>
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-12">
        <div className="max-w-2xl">
          <h2 className="text-4xl font-bold mb-4 text-accent">
            Stock Index Data Comparison
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Compare stock valuation estimates and metrics across 12 global indexes from Germany, Europe, and the USA.
          </p>
          <div className="flex gap-4">
            <Link
              href="/auth/login"
              className="bg-accent hover:bg-blue-600 text-white font-medium py-2 px-6 rounded transition-colors flex items-center gap-2"
            >
              Sign In
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/auth/signup"
              className="bg-secondary hover:bg-slate-700 border border-slate-600 text-white font-medium py-2 px-6 rounded transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="text-lg font-semibold text-accent mb-2">📊 12 Indexes</h3>
            <p className="text-gray-400">
              Supported indexes from Germany, Europe, and USA
            </p>
          </div>
          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="text-lg font-semibold text-accent mb-2">📈 Real Data</h3>
            <p className="text-gray-400">
              Financial estimates from multiple sources
            </p>
          </div>
          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="text-lg font-semibold text-accent mb-2">🔍 Advanced Filters</h3>
            <p className="text-gray-400">
              Filter stocks by multiple criteria
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Authenticated view
  if (loading) {
    return <div className="text-center py-12"><p className="text-gray-400">Loading indexes...</p></div>
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 p-4 rounded">
        <p className="text-red-200">Error: {error}</p>
      </div>
    )
  }

  const germanIndexes = indexes.filter((i) => i.region === 'Germany')
  const europeanIndexes = indexes.filter((i) => i.region === 'Europe')
  const usaIndexes = indexes.filter((i) => i.region === 'USA')

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-4 text-accent">Available Indexes</h2>
        <p className="text-gray-300 mb-6">
          Select an index below to explore stock data.
        </p>
      </div>

      {germanIndexes.length > 0 && (
        <IndexSection title="🇩🇪 German Indexes" indexes={germanIndexes} />
      )}
      {europeanIndexes.length > 0 && (
        <IndexSection title="🇪🇺 European Indexes" indexes={europeanIndexes} />
      )}
      {usaIndexes.length > 0 && (
        <IndexSection title="🇺🇸 USA Indexes" indexes={usaIndexes} />
      )}

      {indexes.length === 0 && (
        <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded">
          <p className="text-yellow-200">
            No indexes configured yet. Please run the data scraper to populate indexes.
          </p>
        </div>
      )}
    </div>
  )
}

function IndexSection({ title, indexes }: { title: string; indexes: Index[] }) {
  return (
    <div>
      <h3 className="text-xl font-semibold mb-3 text-gray-200">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indexes.map((index) => (
          <div
            key={index.id}
            className="bg-secondary hover:bg-slate-700 p-4 rounded border border-slate-600 transition-colors"
          >
            <h4 className="font-bold text-lg text-accent">{index.display_name}</h4>
            <p className="text-sm text-gray-400 mt-2">{index.description}</p>
            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Companies</p>
                <p className="font-semibold">{index.member_count || 0}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Currency</p>
                <p className="font-semibold">{index.currency}</p>
              </div>
            </div>
            {index.last_updated && (
              <p className="text-xs text-gray-500 mt-3">
                Last updated: {new Date(index.last_updated).toLocaleDateString()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
