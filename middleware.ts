import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const DASHBOARD_PREFIX = '/dashboard';
const LOGIN_ROUTE = '/auth/login';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/auth/login') ||
    pathname.startsWith('/api/auth/logout') ||
    pathname.startsWith('/api/auth/check')
  ) {
    return NextResponse.next();
  }

  const token = request.cookies.get('auth_token')?.value;

  if (pathname.startsWith(DASHBOARD_PREFIX) && !token) {
    return NextResponse.redirect(new URL(LOGIN_ROUTE, request.url));
  }

  if (pathname === LOGIN_ROUTE && token) {
    return NextResponse.redirect(new URL(DASHBOARD_PREFIX, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!favicon.ico).*)'],
};
