'use client'

import { AuthGuard } from '@/components/AuthGuard'
import { useAuth } from '@/lib/auth'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <AuthGuard>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Dashboard</h2>
          <p className="text-gray-400">
            Welcome back, {user?.email}!
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="font-semibold text-accent mb-2">Total Stocks</h3>
            <p className="text-3xl font-bold">Coming Soon</p>
          </div>

          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="font-semibold text-accent mb-2">Saved Filters</h3>
            <p className="text-3xl font-bold">0</p>
          </div>

          <div className="bg-secondary border border-slate-600 p-6 rounded">
            <h3 className="font-semibold text-accent mb-2">Last Updated</h3>
            <p className="text-gray-400">No data yet</p>
          </div>
        </div>

        <div className="bg-blue-900/20 border border-blue-700 p-4 rounded">
          <p className="text-blue-200">
            🚀 <strong>Next Phase:</strong> Stock data display and filtering coming next!
          </p>
        </div>
      </div>
    </AuthGuard>
  )
}
