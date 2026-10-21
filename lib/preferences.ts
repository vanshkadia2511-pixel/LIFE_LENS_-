export const PREFS_COOKIE = 'lifelens-prefs'

export const ACCENTS = ['blue', 'cyan', 'emerald', 'amber', 'rose', 'violet'] as const
export const TEXT_SIZES = ['sm', 'md', 'lg'] as const
export const RETENTION = ['7', '30', '90'] as const

export type Accent = (typeof ACCENTS)[number]
export type TextSize = (typeof TEXT_SIZES)[number]

export type Preferences = {
  accent: Accent
  textSize: TextSize
  twoFactor: boolean
  encryption: boolean
  anonymous: boolean
  emailNotifications: boolean
  inAppNotifications: boolean
  securityAlerts: boolean
  dataUsage: 'only-my-data' | 'aggregate'
  retentionDays: (typeof RETENTION)[number]
}

export const DEFAULT_PREFERENCES: Preferences = {
  accent: 'blue',
  textSize: 'md',
  twoFactor: true,
  encryption: true,
  anonymous: false,
  emailNotifications: true,
  inAppNotifications: true,
  securityAlerts: true,
  dataUsage: 'only-my-data',
  retentionDays: '90',
}

export function parsePreferences(raw: string | undefined): Preferences {
  if (!raw) return DEFAULT_PREFERENCES
  try {
    const parsed = JSON.parse(raw) as Partial<Preferences>
    const merged = { ...DEFAULT_PREFERENCES, ...parsed }
    if (!ACCENTS.includes(merged.accent)) merged.accent = 'blue'
    if (!TEXT_SIZES.includes(merged.textSize)) merged.textSize = 'md'
    if (!RETENTION.includes(merged.retentionDays)) merged.retentionDays = '90'
    if (merged.dataUsage !== 'aggregate') merged.dataUsage = 'only-my-data'
    for (const key of ['twoFactor', 'encryption', 'anonymous', 'emailNotifications', 'inAppNotifications', 'securityAlerts'] as const) {
      merged[key] = Boolean(merged[key])
    }
    return merged
  } catch {
    return DEFAULT_PREFERENCES
  }
}
