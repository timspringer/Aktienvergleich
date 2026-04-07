'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { LogOut, User as UserIcon, ChevronDown } from 'lucide-react'

export function UserMenu() {
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  const handleSignOut = async () => {
    try {
      await signOut()
      router.push('/auth/login')
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  if (!user) return null

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-secondary border border-slate-600 rounded hover:border-accent transition-colors"
      >
        <UserIcon className="w-4 h-4" />
        <span className="text-sm truncate max-w-xs">{user.email}</span>
        <ChevronDown className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-secondary border border-slate-600 rounded shadow-lg z-50">
          <div className="px-4 py-3 border-b border-slate-600">
            <p className="text-sm text-gray-400">Signed in as</p>
            <p className="text-sm font-medium truncate">{user.email}</p>
          </div>
          <button
            onClick={handleSignOut}
            className="w-full text-left px-4 py-2 flex items-center gap-2 hover:bg-primary transition-colors text-red-400 hover:text-red-300"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      )}
    </div>
  )
}
