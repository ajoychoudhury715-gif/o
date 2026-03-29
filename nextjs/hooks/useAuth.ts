'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { User, AuthSession } from '@/types/auth'
import Cookies from 'js-cookie'

interface UseAuthReturn {
  session: AuthSession | null
  user: User | null
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

export function useAuth(): UseAuthReturn {
  const router = useRouter()
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize session from cookie/storage
  useEffect(() => {
    const initSession = async () => {
      try {
        // Check if user data is in localStorage
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          const user = JSON.parse(storedUser)
          const token = Cookies.get('auth_token')
          if (token) {
            setSession({
              user,
              isAuthenticated: true,
              token,
            })
          }
        }
      } catch (err) {
        console.error('Failed to restore session:', err)
      } finally {
        setIsLoading(false)
      }
    }

    initSession()
  }, [])

  const login = useCallback(
    async (username: string, password: string) => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.error || 'Login failed')
        }

        const { user, token } = await response.json()

        // Store user in localStorage for quick access
        localStorage.setItem('user', JSON.stringify(user))

        // Set session
        setSession({
          user,
          isAuthenticated: true,
          token,
        })

        // Redirect to dashboard
        router.push('/scheduling')
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Login failed'
        setError(errorMessage)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [router]
  )

  const logout = useCallback(async () => {
    setIsLoading(true)

    try {
      // Call logout API
      await fetch('/api/auth/logout', {
        method: 'POST',
      })

      // Clear session
      setSession(null)
      localStorage.removeItem('user')
      Cookies.remove('auth_token')

      // Redirect to login
      router.push('/login')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [router])

  return {
    session,
    user: session?.user || null,
    isLoading,
    error,
    login,
    logout,
    isAuthenticated: session?.isAuthenticated || false,
  }
}
