import crypto from 'crypto';

import type { User, UserRole } from './types';

const AUTH_SECRET =
  process.env.AUTH_PERSIST_SECRET ||
  process.env.SUPABASE_SERVICE_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  'tdb-auth-fallback-secret';

const TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60;
const DEMO_USERNAME = process.env.DEMO_USERNAME || 'SPOIDERMON';
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || 'SPOIDERMON123';

type SupabaseUserRecord = {
  id: string;
  username: string;
  password_hash: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
};

function normalizeUsername(value: string): string {
  return value.trim();
}

function base64UrlEncode(value: string): string {
  return Buffer.from(value, 'utf-8')
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
}

function base64UrlDecode(value: string): string {
  const padding = '='.repeat((4 - (value.length % 4)) % 4);
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/') + padding;
  return Buffer.from(normalized, 'base64').toString('utf-8');
}

function hashPassword(password: string, salt?: string): string {
  const resolvedSalt = salt || crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, Buffer.from(resolvedSalt, 'hex'), 100000, 32, 'sha256');
  return `${resolvedSalt}:${hash.toString('hex')}`;
}

function verifyPassword(password: string, storedHash: string): boolean {
  const [salt, hash] = storedHash.split(':');
  if (!salt || !hash) {
    return false;
  }

  const computed = hashPassword(password, salt).split(':')[1];
  return crypto.timingSafeEqual(Buffer.from(computed, 'hex'), Buffer.from(hash, 'hex'));
}

export function issueLoginToken(user: { username: string; role: UserRole }): string {
  const payload = JSON.stringify({
    u: user.username,
    r: user.role,
    exp: Math.floor(Date.now() / 1000) + TOKEN_TTL_SECONDS,
  });

  const payloadBase64 = base64UrlEncode(payload);
  const signature = crypto
    .createHmac('sha256', AUTH_SECRET)
    .update(payloadBase64)
    .digest('hex');

  return `${payloadBase64}.${signature}`;
}

export function parseLoginToken(token: string): { username: string; role: UserRole } | null {
  const rawToken = token.trim();
  if (!rawToken.includes('.')) {
    return null;
  }

  try {
    const [payloadBase64, signature] = rawToken.split('.', 2);
    const expectedSignature = crypto
      .createHmac('sha256', AUTH_SECRET)
      .update(payloadBase64)
      .digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
      return null;
    }

    const payload = JSON.parse(base64UrlDecode(payloadBase64)) as {
      u?: string;
      r?: UserRole;
      exp?: number;
    };

    if (!payload.u || !payload.r || !payload.exp || payload.exp <= Math.floor(Date.now() / 1000)) {
      return null;
    }

    return {
      username: payload.u,
      role: payload.r,
    };
  } catch {
    return null;
  }
}

async function fetchSupabaseUser(username: string): Promise<SupabaseUserRecord | null> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey =
    process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return null;
  }

  const requestUrl = new URL('/rest/v1/users', supabaseUrl);
  requestUrl.searchParams.set(
    'select',
    'id,username,password_hash,role,is_active,created_at'
  );
  requestUrl.searchParams.set('username', `ilike.${normalizeUsername(username)}`);
  requestUrl.searchParams.set('limit', '1');

  const response = await fetch(requestUrl.toString(), {
    headers: {
      apikey: supabaseKey,
      Authorization: `Bearer ${supabaseKey}`,
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Supabase auth request failed with ${response.status}`);
  }

  const records = (await response.json()) as SupabaseUserRecord[];
  return records[0] ?? null;
}

function getDemoUser(): User {
  return {
    id: 'local-admin',
    username: DEMO_USERNAME,
    role: 'admin',
    isActive: true,
    createdAt: new Date(0).toISOString(),
  };
}

export async function authenticateUser(username: string, password: string): Promise<User | null> {
  const normalizedUsername = normalizeUsername(username);
  if (!normalizedUsername || !password.trim()) {
    return null;
  }

  try {
    const supabaseUser = await fetchSupabaseUser(normalizedUsername);
    if (supabaseUser) {
      if (!supabaseUser.is_active) {
        return null;
      }

      if (!verifyPassword(password, supabaseUser.password_hash)) {
        return null;
      }

      return {
        id: supabaseUser.id,
        username: supabaseUser.username,
        role: supabaseUser.role,
        isActive: supabaseUser.is_active,
        createdAt: supabaseUser.created_at,
      };
    }
  } catch (error) {
    console.error('Supabase authentication failed:', error);
  }

  if (
    normalizedUsername.toLowerCase() === DEMO_USERNAME.toLowerCase() &&
    password === DEMO_PASSWORD
  ) {
    return getDemoUser();
  }

  return null;
}
