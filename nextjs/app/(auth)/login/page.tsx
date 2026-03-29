'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'
import { AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const { login, isLoading, error } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    try {
      await login(username, password)
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="glass-light w-full max-w-md p-8 rounded-3xl shadow-2xl">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🦷</div>
          <h1 className="text-3xl font-bold text-gradient mb-2">THE DENTAL BOND</h1>
          <p className="text-gray-600">Implant & Micro-dentistry</p>
        </div>

        {/* Error Message */}
        {(error || localError) && (
          <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded-lg flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <p className="text-red-700 text-sm">{error || localError}</p>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              className="input bg-white/50 border-white/50 text-gray-900 placeholder-gray-500"
              disabled={isLoading}
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="input bg-white/50 border-white/50 text-gray-900 placeholder-gray-500"
              disabled={isLoading}
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary py-3 font-semibold rounded-lg hover:bg-medical-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>
            Forgot your password?{' '}
            <Link href="/reset-password" className="text-medical-blue-600 hover:underline font-medium">
              Reset it here
            </Link>
          </p>
        </div>

        {/* Demo credentials info */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200 text-xs text-gray-700">
          <p className="font-medium mb-1">Demo Account (Default):</p>
          <p>Username: <code className="bg-gray-200 px-1 rounded">SPOIDERMON</code></p>
          <p>Password: <code className="bg-gray-200 px-1 rounded">SPOIDERMON123</code></p>
        </div>
      </div>
    </div>
  )
}
