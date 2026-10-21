'use server'

import { cookies } from 'next/headers'
import { parsePreferences, PREFS_COOKIE, type Preferences } from '@/lib/preferences'

export async function savePreferences(input: Preferences) {
  const sanitized = parsePreferences(JSON.stringify(input))
  ;(await cookies()).set(PREFS_COOKIE, JSON.stringify(sanitized), {
    httpOnly: true,
    sameSite: 'lax',
    secure: true,
    path: '/',
    maxAge: 60 * 60 * 24 * 365,
  })
  return sanitized
}
