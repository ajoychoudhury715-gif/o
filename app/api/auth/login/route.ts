import { NextResponse } from 'next/server';

import { authenticateUser, issueLoginToken } from '../../../../lib/server-auth';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const username = typeof body?.username === 'string' ? body.username : '';
    const password = typeof body?.password === 'string' ? body.password : '';

    if (!username.trim() || !password.trim()) {
      return NextResponse.json(
        { error: 'Username and password are required.' },
        { status: 400 }
      );
    }

    const user = await authenticateUser(username, password);
    if (!user) {
      return NextResponse.json({ error: 'Invalid username or password.' }, { status: 401 });
    }

    const token = issueLoginToken({
      username: user.username,
      role: user.role,
    });

    const response = NextResponse.json(
      {
        authenticatedAt: new Date().toISOString(),
        token,
        user,
      },
      { status: 200 }
    );

    response.cookies.set('auth_token', token, {
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
    });

    return response;
  } catch (error) {
    console.error('Login failed:', error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
