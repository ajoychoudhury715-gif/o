import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

import { parseLoginToken } from '../../../../lib/server-auth';

export async function GET() {
  try {
    const authCookie = (await cookies()).get('auth_token')?.value;
    if (!authCookie) {
      return NextResponse.json({ authenticated: false }, { status: 401 });
    }

    const session = parseLoginToken(authCookie);
    if (!session) {
      return NextResponse.json({ authenticated: false }, { status: 401 });
    }

    return NextResponse.json(
      {
        authenticated: true,
        user: {
          username: session.username,
          role: session.role,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json({ error: 'Authentication check failed' }, { status: 500 });
  }
}
