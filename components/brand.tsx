import Link from 'next/link'
import { ShieldCheck, TriangleAlert, UserRound, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'relative inline-flex size-9 items-center justify-center rounded-full bg-[radial-gradient(circle_at_30%_30%,#7fc4ff,#3b5bff_55%,#2a1f8f)] shadow-[0_0_20px_-2px_rgba(80,140,255,0.8)]',
        className,
      )}
    >
      <span className="absolute inset-[3px] rounded-full border-2 border-white/80" />
      <span className="relative font-display text-[0.95em] font-bold leading-none text-white">Ω</span>
    </span>
  )
}

export function Logo({ href = '/', className, size = 'md' }: { href?: string; className?: string; size?: 'md' | 'lg' }) {
  return (
    <Link
      href={href}
      className={cn('inline-flex items-center gap-2.5 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring', className)}
    >
      <LogoMark className={size === 'lg' ? 'size-12 text-2xl' : 'text-lg'} />
      <span className={cn('font-semibold tracking-tight text-foreground', size === 'lg' ? 'text-3xl' : 'text-xl')}>
        LifeLens <span className="font-display">Ω</span>
      </span>
    </Link>
  )
}

const pillars = [
  { Icon: ShieldCheck, title: 'Trusted Sources', text: 'Cross-verify from multiple sources' },
  { Icon: TriangleAlert, title: 'Transparent Analysis', text: 'See why a verdict is given' },
  { Icon: UserRound, title: 'User Control', text: 'Your data, your choice' },
  { Icon: Lock, title: 'Privacy First', text: 'Built with security in mind' },
]

export function SiteFooter({ className }: { className?: string }) {
  return (
    <footer className={cn('border-t border-border', className)}>
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-10 lg:flex-row lg:items-center lg:gap-10">
        <div className="shrink-0 lg:border-r lg:border-border lg:pr-10">
          <Logo size="lg" />
          <p className="mt-2 text-xs text-accent/90">Real Evidence. Smarter Decisions. Safer Futures.</p>
        </div>
        <ul className="grid flex-1 grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {pillars.map(({ Icon, title, text }) => (
            <li key={title} className="flex items-center gap-3">
              <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-full border border-border-strong bg-primary/10 text-accent">
                <Icon className="size-4" aria-hidden="true" />
              </span>
              <div>
                <p className="text-sm font-medium text-foreground">{title}</p>
                <p className="text-xs text-muted-foreground">{text}</p>
              </div>
            </li>
          ))}
        </ul>
        <p className="shrink-0 text-sm leading-relaxed text-accent/90 lg:text-right">
          Smarter verification today.
          <br />A safer tomorrow.
        </p>
      </div>
      <div className="border-t border-border/60 py-4 text-center text-[11px] text-muted-foreground">
        {'© 2026 LifeLens Ω. Verification results support — never replace — your personal judgment.'}
      </div>
    </footer>
  )
}
