import crypto from 'crypto'
import type { User } from '@/types/auth'

const AUTH_PERSIST_SECRET = process.env.AUTH_PERSIST_SECRET || process.env.SUPABASE_SERVICE_KEY || 'default-secret-key'
const TOKEN_TTL_DAYS = 7
const PBKDF2_ITERATIONS = 100000
const PBKDF2_ALGORITHM = 'sha256'

/**
 * Generate PBKDF2-SHA256 password hash
 * Returns: salt_hex:hash_hex
 */
export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16)
  const hash = crypto.pbkdf2Sync(password, salt, PBKDF2_ITERATIONS, 64, PBKDF2_ALGORITHM)
  return `${salt.toString('hex')}:${hash.toString('hex')}`
}

/**
 * Verify password against stored hash
 */
export function verifyPassword(password: string, storedHash: string): boolean {
  const [saltHex, hashHex] = storedHash.split(':')
  if (!saltHex || !hashHex) return false

  const salt = Buffer.from(saltHex, 'hex')
  const hash = crypto.pbkdf2Sync(password, salt, PBKDF2_ITERATIONS, 64, PBKDF2_ALGORITHM)

  // Use constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(hash, Buffer.from(hashHex, 'hex'))
}

/**
 * Generate HMAC-signed login token
 */
export function generateLoginToken(user: { username: string; role: string }): string {
  const expiresAt = new Date(Date.now() + TOKEN_TTL_DAYS * 24 * 60 * 60 * 1000)

  const payload = JSON.stringify({
    u: user.username,
    r: user.role,
    exp: expiresAt.getTime(),
  })

  const signature = crypto
    .createHmac('sha256', AUTH_PERSIST_SECRET)
    .update(payload)
    .digest('hex')

  return `${Buffer.from(payload).toString('base64')}.${signature}`
}

/**
 * Parse and validate login token
 */
export function parseLoginToken(token: string): { username: string; role: string } | null {
  try {
    const [payloadB64, signature] = token.split('.')
    if (!payloadB64 || !signature) return null

    const payload = Buffer.from(payloadB64, 'base64').toString('utf-8')

    // Verify signature
    const expectedSignature = crypto
      .createHmac('sha256', AUTH_PERSIST_SECRET)
      .update(payload)
      .digest('hex')

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
      return null
    }

    const data = JSON.parse(payload)

    // Check expiration
    if (data.exp && data.exp < Date.now()) {
      return null
    }

    return {
      username: data.u,
      role: data.r,
    }
  } catch {
    return null
  }
}

/**
 * Create session from user
 */
export function createSession(user: User, token: string) {
  return {
    user,
    token,
    timestamp: new Date().toISOString(),
  }
}
