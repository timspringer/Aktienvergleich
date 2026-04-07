'use client'

import { Search, X } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchBar({
  value,
  onChange,
  placeholder = 'Search by company name, ISIN, or WKN...',
}: SearchBarProps) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-10 py-2 bg-secondary border border-slate-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-3 text-gray-500 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}
