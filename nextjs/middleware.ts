import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { parseLoginToken } from '@/lib/auth'

const PUBLIC_ROUTES = ['/login', '/reset-password']
const AUTH_ROUTES = ['/api/auth/login', '/api/auth/reset-password']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow public auth routes
  if (AUTH_ROUTES.includes(pathname)) {
    return NextResponse.next()
  }

  // Allow public pages
  if (PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.next()
  }

  // Check for auth token in cookies
  const token = request.cookies.get('auth_token')?.value

  if (!token) {
    // Redirect to login if trying to access protected route
    if (pathname.startsWith('/api/') || pathname.startsWith('/scheduling') || pathname.startsWith('/assistants') || pathname.startsWith('/doctors') || pathname.startsWith('/admin')) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
    return NextResponse.next()
  }

  //Validate token
  const claims = parseLoginToken(token)
  if (!claims) {
    // Token is invalid or expired
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('auth_token')
    return response
  }

  // Token is valid, continue
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
