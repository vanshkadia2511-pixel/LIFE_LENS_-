'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { Logo } from '@/components/brand'
import { ThemeToggle } from '@/components/theme-toggle'
import { ButtonLink } from '@/components/ui/primitives'

const links = [
  { href: '#home', label: 'Home' },
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#verification', label: 'Verification' },
  { href: '#about', label: 'About' },
]

export function SiteHeader() {
  const [open, setOpen] = useState(false)
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-5">
        <Logo />
        <nav aria-label="Primary" className="hidden md:block">
          <ul className="flex items-center gap-1">
            {links.map((l, i) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className={
                    'relative rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
                    (i === 0 ? 'text-foreground after:absolute after:inset-x-3 after:-bottom-[13px] after:h-0.5 after:rounded-full after:bg-accent' : '')
                  }
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <p className="hidden text-xs text-accent/90 xl:block">Real Evidence. Smarter Decisions. Safer Futures.</p>
          <ThemeToggle />
          <ButtonLink href="/dashboard" size="sm" className="hidden sm:inline-flex">
            Open App
          </ButtonLink>
          <button
            type="button"
            className="inline-flex size-9 items-center justify-center rounded-lg border border-border md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.nav
            id="mobile-nav"
            aria-label="Mobile"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-border md:hidden"
          >
            <ul className="flex flex-col gap-1 px-5 py-3">
              {links.map((l) => (
                <li key={l.href}>
                  <a href={l.href} onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2.5 text-sm text-foreground hover:bg-primary/10">
                    {l.label}
                  </a>
                </li>
              ))}
              <li>
                <Link href="/dashboard" className="block rounded-lg px-3 py-2.5 text-sm font-medium text-accent hover:bg-primary/10">
                  Open App
                </Link>
              </li>
            </ul>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
