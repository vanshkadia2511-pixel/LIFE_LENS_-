import type { Metadata, Viewport } from 'next'
import { Inter, Playfair_Display } from 'next/font/google'
import { cookies } from 'next/headers'
import { Providers } from '@/components/providers'
import { parsePreferences, PREFS_COOKIE } from '@/lib/preferences'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const display = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-display-serif',
  weight: ['600', '700'],
})

export const metadata: Metadata = {
  title: 'LifeLens Ω — Trust Before You Commit',
  description:
    'Check job offers, recruiters, companies and meeting links with real evidence — not just opinions.',
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: dark)', color: '#040a1d' },
    { media: '(prefers-color-scheme: light)', color: '#eef3fc' },
  ],
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const prefs = parsePreferences((await cookies()).get(PREFS_COOKIE)?.value)
  return (
    <html
      lang="en"
      suppressHydrationWarning
      data-accent={prefs.accent}
      data-text-size={prefs.textSize}
      className={`${inter.variable} ${display.variable}`}
    >
      <body className="font-sans antialiased">
        <Providers initialPreferences={prefs}>{children}</Providers>
      </body>
    </html>
  )
}
