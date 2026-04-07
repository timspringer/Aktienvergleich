'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { ChevronDown } from 'lucide-react'
import type { Index } from '@/lib/types'

interface IndexFilterProps {
  value: string
  onChange: (value: string) => void
}

export function IndexFilter({ value, onChange }: IndexFilterProps) {
  const [indexes, setIndexes] = useState<Index[]>([])
  const [loading, setLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    async function fetchIndexes() {
      try {
        const { data } = await supabase
          .from('indices')
          .select('*')
          .order('region')

        setIndexes(data || [])
      } catch (error) {
        console.error('Failed to fetch indexes:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchIndexes()
  }, [])

  const selectedIndex = indexes.find((i) => i.id === value)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 bg-secondary border border-slate-600 rounded text-left flex items-center justify-between hover:border-accent transition-colors"
      >
        <span>{selectedIndex ? selectedIndex.display_name : 'All Indexes'}</span>
        <ChevronDown
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-secondary border border-slate-600 rounded shadow-lg z-10 max-h-48 overflow-y-auto">
          <button
            onClick={() => {
              onChange('')
              setIsOpen(false)
            }}
            className={`w-full text-left px-4 py-2 hover:bg-primary transition-colors ${
              !value ? 'bg-primary text-accent' : ''
            }`}
          >
            All Indexes
          </button>

          {indexes.map((index) => (
            <button
              key={index.id}
              onClick={() => {
                onChange(index.id)
                setIsOpen(false)
              }}
              className={`w-full text-left px-4 py-2 hover:bg-primary transition-colors text-sm ${
                value === index.id ? 'bg-primary text-accent' : ''
              }`}
            >
              <div>
                <p className="font-medium">{index.display_name}</p>
                <p className="text-xs text-gray-500">{index.region}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
