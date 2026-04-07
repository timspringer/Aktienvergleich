'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { Mail, Lock, AlertCircle, CheckCircle, Loader } from 'lucide-react'

export default function SignupPage() {
  const router = useRouter()
  const { signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)

    try {
      await signUp(email, password)
      setSuccess(true)
      setTimeout(() => {
        router.push('/auth/login')
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <CheckCircle className="w-16 h-16 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold">Account Created!</h2>
        <p className="text-gray-400">
          Your account has been created successfully. Redirecting to login...
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-accent mb-2">Aktienvergleich</h1>
        <p className="text-gray-400">Create a new account</p>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded p-3 flex gap-2 text-red-200 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2">
            Email Address
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-primary border border-slate-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              placeholder="you@example.com"
            />
          </div>
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-2">
            Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-primary border border-slate-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              placeholder="••••••••"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Must be at least 8 characters
          </p>
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium mb-2"
          >
            Confirm Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
            <input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-primary border border-slate-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              placeholder="••••••••"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-accent hover:bg-blue-600 disabled:bg-gray-600 text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Creating account...
            </>
          ) : (
            'Create Account'
          )}
        </button>
      </form>

      <p className="text-center text-gray-400 text-sm">
        Already have an account?{' '}
        <Link href="/auth/login" className="text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  )
}
