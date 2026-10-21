'use client'

import { createContext, useCallback, useContext, useState, useTransition } from 'react'
import { ThemeProvider } from 'next-themes'
import { MotionConfig } from 'motion/react'
import { savePreferences } from '@/app/actions/preferences'
import type { Preferences } from '@/lib/preferences'

type PreferencesContextValue = {
  preferences: Preferences
  updatePreferences: (patch: Partial<Preferences>) => Promise<void>
  status: 'idle' | 'saving' | 'saved' | 'error'
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null)

export function usePreferences() {
  const ctx = useContext(PreferencesContext)
  if (!ctx) throw new Error('usePreferences must be used inside <Providers>')
  return ctx
}

export function Providers({
  children,
  initialPreferences,
}: {
  children: React.ReactNode
  initialPreferences: Preferences
}) {
  const [preferences, setPreferences] = useState(initialPreferences)
  const [status, setStatus] = useState<PreferencesContextValue['status']>('idle')
  const [, startTransition] = useTransition()

  const updatePreferences = useCallback(
    async (patch: Partial<Preferences>) => {
      const previous = preferences
      const next = { ...preferences, ...patch }
      setPreferences(next)
      document.documentElement.dataset.accent = next.accent
      document.documentElement.dataset.textSize = next.textSize
      setStatus('saving')
      try {
        await savePreferences(next)
        startTransition(() => setStatus('saved'))
      } catch {
        setPreferences(previous)
        document.documentElement.dataset.accent = previous.accent
        document.documentElement.dataset.textSize = previous.textSize
        setStatus('error')
      }
    },
    [preferences],
  )

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
      <MotionConfig reducedMotion="user">
        <PreferencesContext.Provider value={{ preferences, updatePreferences, status }}>
          {children}
        </PreferencesContext.Provider>
      </MotionConfig>
    </ThemeProvider>
  )
}
