'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Index } from '@/lib/types'

export default function Home() {
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

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Loading indexes...</p>
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

  const germanIndexes = indexes.filter((i) => i.region === 'Germany')
  const europeanIndexes = indexes.filter((i) => i.region === 'Europe')
  const usaIndexes = indexes.filter((i) => i.region === 'USA')

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-4 text-accent">Welcome to Aktienvergleich</h2>
        <p className="text-gray-300 mb-6">
          Compare stock valuation estimates and metrics across global indexes. Select an index
          below to start analyzing.
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
            className="bg-secondary hover:bg-slate-700 p-4 rounded border border-slate-600 transition-colors cursor-pointer"
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
