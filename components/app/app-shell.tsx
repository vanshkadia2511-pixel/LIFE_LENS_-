'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { AnimatePresence, motion } from 'motion/react'
import {
  LayoutDashboard,
  ShieldCheck,
  BriefcaseBusiness,
  UsersRound,
  Building2,
  Video,
  FileText,
  BookLock,
  Settings,
  Search,
  Bell,
  Menu,
  X,
} from 'lucide-react'
import { Logo } from '@/components/brand'
import { ThemeToggle } from '@/components/theme-toggle'
import { Avatar, DemoBadge } from '@/components/ui/primitives'
import { DEMO_USER } from '@/lib/demo-data'
import { cn } from '@/lib/utils'

export const navItems = [
  { href: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { href: '/verify', label: 'Verify', Icon: ShieldCheck },
  { href: '/analysis?tab=jobs', label: 'Job Offers', Icon: BriefcaseBusiness },
  { href: '/analysis?tab=recruiters', label: 'Recruiters', Icon: UsersRound },
  { href: '/analysis?tab=companies', label: 'Companies', Icon: Building2 },
  { href: '/meetings', label: 'Meetings', Icon: Video },
  { href: '/reports', label: 'Reports', Icon: FileText },
  { href: '/ledger', label: 'Evidence Ledger', Icon: BookLock },
  { href: '/settings', label: 'Settings', Icon: Settings },
]

function useIsActive() {
  const pathname = usePathname()
  const params = useSearchParams()
  return (href: string) => {
    const [path, query] = href.split('?')
    if (query) {
      const tab = new URLSearchParams(query).get('tab')
      return pathname === path && (params.get('tab') ?? 'jobs') === tab
    }
    return pathname === path || pathname.startsWith(path + '/')
  }
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const isActive = useIsActive()
  return (
    <ul className="flex flex-col gap-1">
      {navItems.map(({ href, label, Icon }) => {
        const active = isActive(href)
        return (
          <li key={href}>
            <Link
              href={href}
              onClick={onNavigate}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                active ? 'text-foreground' : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground',
              )}
            >
              {active && (
                <motion.span
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-lg border border-border-strong bg-primary/20 shadow-[0_0_20px_-6px_var(--primary)]"
                  transition={{ type: 'spring', stiffness: 400, damping: 34 }}
                />
              )}
              <Icon className="relative size-4" aria-hidden="true" />
              <span className="relative">{label}</span>
            </Link>
          </li>
        )
      })}
    </ul>
  )
}

function SearchBox() {
  const router = useRouter()
  const [q, setQ] = useState('')
  return (
    <form
      role="search"
      className="relative w-full max-w-md"
      onSubmit={(e) => {
        e.preventDefault()
        const term = q.trim()
        router.push(term ? `/analysis?tab=jobs&q=${encodeURIComponent(term)}` : '/analysis')
      }}
    >
      <label htmlFor="global-search" className="sr-only">
        Search jobs, recruiters, companies
      </label>
      <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
      <input
        id="global-search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search jobs, recruiters, companies..."
        className="h-9 w-full rounded-lg border border-border bg-input pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
      />
    </form>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [drawer, setDrawer] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const pathname = usePathname()

  return (
    <div className="app-backdrop flex min-h-dvh">
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r border-border bg-card/40 px-3 py-5 backdrop-blur-xl lg:flex">
        <Logo className="px-2" />
        <nav aria-label="App" className="mt-8 flex-1">
          <NavList />
        </nav>
        <div className="glass rounded-xl p-3 text-xs text-muted-foreground">
          <DemoBadge />
          <p className="mt-2 leading-relaxed">Verification services are not connected. Figures shown are demonstration data.</p>
        </div>
      </aside>

      <AnimatePresence>
        {drawer && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/50 lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setDrawer(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-card-solid px-3 py-5 lg:hidden"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 32 }}
            >
              <div className="flex items-center justify-between px-2">
                <Logo />
                <button type="button" aria-label="Close navigation" onClick={() => setDrawer(false)} className="inline-flex size-9 items-center justify-center rounded-lg border border-border">
                  <X className="size-4" />
                </button>
              </div>
              <nav aria-label="App mobile" className="mt-6">
                <NavList onNavigate={() => setDrawer(false)} />
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/70 px-4 backdrop-blur-xl sm:px-6">
          <button type="button" aria-label="Open navigation" onClick={() => setDrawer(true)} className="inline-flex size-9 items-center justify-center rounded-lg border border-border lg:hidden">
            <Menu className="size-4" />
          </button>
          <SearchBox />
          <div className="ml-auto flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                aria-label="Notifications"
                aria-expanded={notifOpen}
                onClick={() => setNotifOpen((v) => !v)}
                className="relative inline-flex size-9 cursor-pointer items-center justify-center rounded-lg border border-border text-muted-foreground hover:text-foreground"
              >
                <Bell className="size-4" />
                <span className="absolute right-2 top-2 size-1.5 rounded-full bg-danger" />
              </button>
              <AnimatePresence>
                {notifOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="glass absolute right-0 top-11 z-50 w-72 rounded-xl bg-card-solid p-3"
                  >
                    <p className="text-xs font-semibold text-foreground">Notifications</p>
                    <ul className="mt-2 flex flex-col gap-2 text-xs text-muted-foreground">
                      <li className="rounded-lg bg-danger/10 p-2 text-danger">Acme Corp flagged as High Risk</li>
                      <li className="rounded-lg bg-warning/10 p-2 text-warning">Sarah Johnson needs review</li>
                    </ul>
                    <DemoBadge className="mt-3" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <ThemeToggle />
            <div className="hidden items-center gap-2 pl-2 sm:flex">
              <Avatar name={DEMO_USER.name} />
              <div className="leading-tight">
                <p className="text-xs font-medium text-foreground">{DEMO_USER.name}</p>
                <p className="text-[11px] text-muted-foreground">{DEMO_USER.role}</p>
              </div>
            </div>
          </div>
        </header>
        <main key={pathname} className="flex-1 px-4 pb-24 pt-6 sm:px-6 lg:pb-10">
          {children}
        </main>
      </div>

      <nav aria-label="Quick" className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/85 backdrop-blur-xl lg:hidden">
        <ul className="grid grid-cols-5">
          {[navItems[0], navItems[1], navItems[6], navItems[5], navItems[8]].map(({ href, label, Icon }) => {
            const active = pathname === href.split('?')[0]
            return (
              <li key={href}>
                <Link href={href} className={cn('flex flex-col items-center gap-1 py-2.5 text-[10px]', active ? 'text-accent' : 'text-muted-foreground')}>
                  <Icon className="size-5" aria-hidden="true" />
                  {label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </div>
  )
}
