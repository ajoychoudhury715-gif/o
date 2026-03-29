import { createClient } from '@supabase/supabase-js'
import { hashPassword, verifyPassword, generateLoginToken } from '@/lib/auth'
import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import type { User } from '@/types/auth'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

interface LoginRequest {
  username: string
  password: string
}

export async function POST(request: NextRequest) {
  try {
    const body: LoginRequest = await request.json()
    const { username, password } = body

    if (!username || !password) {
      return NextResponse.json(
        { error: 'Username and password required' },
        { status: 400 }
      )
    }

    // Fetch user from Supabase
    const { data: userData, error: fetchError } = await supabase
      .from('users')
      .select('id, username, password_hash, role, is_active')
      .eq('username', username.toLowerCase())
      .single()

    if (fetchError || !userData) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      )
    }

    // Check if user is active
    if (!userData.is_active) {
      return NextResponse.json(
        { error: 'User account is inactive' },
        { status: 401 }
      )
    }

    // Verify password
    try {
      const isValid = verifyPassword(password, userData.password_hash)
      if (!isValid) {
        return NextResponse.json(
          { error: 'Invalid credentials' },
          { status: 401 }
        )
      }
    } catch {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      )
    }

    // Create session
    const user: User = {
      id: userData.id,
      username: userData.username,
      role: userData.role,
      isActive: userData.is_active,
      createdAt: new Date().toISOString(),
    }

    const token = generateLoginToken({
      username: user.username,
      role: user.role,
    })

    const response = NextResponse.json(
      {
        success: true,
        user,
        token,
      },
      { status: 200 }
    )

    // Set secure HTTP-only cookie with token
    response.cookies.set('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/',
    })

    return response
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
