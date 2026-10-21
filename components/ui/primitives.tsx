'use client'

import { forwardRef } from 'react'
import Link from 'next/link'
import { CircleCheck, CircleAlert, TriangleAlert, ShieldCheck, LoaderCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

const buttonBase =
  'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-60 cursor-pointer'

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    'bg-brand-gradient text-primary-foreground shadow-[0_8px_30px_-8px_var(--primary)] hover:brightness-110 hover:shadow-[0_10px_40px_-6px_var(--primary)]',
  secondary: 'glass text-foreground hover:border-border-strong',
  outline:
    'border border-border-strong bg-transparent text-foreground hover:bg-primary/10 hover:shadow-[0_0_24px_-8px_var(--primary)]',
  ghost: 'text-muted-foreground hover:text-foreground hover:bg-primary/10',
  danger: 'bg-danger text-white hover:brightness-110 shadow-[0_8px_30px_-10px_var(--danger)]',
}

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
}

export function buttonClass(variant: ButtonVariant = 'primary', size: ButtonSize = 'md', className?: string) {
  return cn(buttonBase, buttonVariants[variant], buttonSizes[size], className)
}

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize; loading?: boolean }
>(function Button({ variant = 'primary', size = 'md', loading, className, children, disabled, ...props }, ref) {
  return (
    <button ref={ref} className={buttonClass(variant, size, className)} disabled={disabled || loading} {...props}>
      {loading && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
})

export function ButtonLink({
  href,
  variant = 'primary',
  size = 'md',
  className,
  children,
}: {
  href: string
  variant?: ButtonVariant
  size?: ButtonSize
  className?: string
  children: React.ReactNode
}) {
  return (
    <Link href={href} className={buttonClass(variant, size, className)}>
      {children}
    </Link>
  )
}

export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('glass rounded-2xl', className)} {...props}>
      {children}
    </div>
  )
}

export function CardHeader({
  title,
  description,
  action,
  className,
}: {
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex items-start justify-between gap-3 px-5 pt-5', className)}>
      <div>
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export type Status = 'verified' | 'review' | 'risk' | 'safe' | 'pending' | 'low' | 'medium' | 'high'

const statusStyles: Record<Status, { className: string; label: string; Icon: typeof CircleCheck }> = {
  verified: { className: 'text-success bg-success/12 border-success/40', label: 'Verified', Icon: CircleCheck },
  safe: { className: 'text-success bg-success/12 border-success/40', label: 'Safe', Icon: ShieldCheck },
  low: { className: 'text-success bg-success/12 border-success/40', label: 'Low', Icon: CircleCheck },
  review: { className: 'text-warning bg-warning/12 border-warning/40', label: 'Review', Icon: CircleAlert },
  medium: { className: 'text-warning bg-warning/12 border-warning/40', label: 'Medium', Icon: CircleAlert },
  risk: { className: 'text-danger bg-danger/12 border-danger/45', label: 'High Risk', Icon: TriangleAlert },
  high: { className: 'text-danger bg-danger/12 border-danger/45', label: 'High', Icon: TriangleAlert },
  pending: { className: 'text-muted-foreground bg-muted border-border', label: 'Pending', Icon: LoaderCircle },
}

export function StatusBadge({ status, label, className }: { status: Status; label?: string; className?: string }) {
  const s = statusStyles[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 whitespace-nowrap rounded-md border px-2 py-0.5 text-[11px] font-medium',
        s.className,
        className,
      )}
    >
      <s.Icon className="size-3" aria-hidden="true" />
      {label ?? s.label}
    </span>
  )
}

export function DemoBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-warning',
        className,
      )}
    >
      Demo data
    </span>
  )
}

export const inputClass =
  'h-10 w-full rounded-lg border border-border bg-input px-3 text-sm text-foreground placeholder:text-muted-foreground/70 transition-colors focus-visible:outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 aria-[invalid=true]:border-danger aria-[invalid=true]:ring-danger/20'

export function Switch({
  checked,
  onChange,
  label,
  id,
}: {
  checked: boolean
  onChange: (value: boolean) => void
  label: string
  id?: string
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        checked ? 'border-primary bg-primary' : 'border-border bg-muted',
      )}
    >
      <span
        className={cn(
          'inline-block size-3.5 rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-[18px]' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}

export function Tabs<T extends string>({
  tabs,
  value,
  onChange,
  className,
  label,
}: {
  tabs: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
  className?: string
  label: string
}) {
  return (
    <div role="tablist" aria-label={label} className={cn('flex flex-wrap gap-1 rounded-xl border border-border bg-input/60 p-1', className)}>
      {tabs.map((tab) => (
        <button
          key={tab.value}
          role="tab"
          type="button"
          aria-selected={value === tab.value}
          onClick={() => onChange(tab.value)}
          className={cn(
            'cursor-pointer rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            value === tab.value
              ? 'bg-primary/90 text-primary-foreground shadow-[0_0_20px_-4px_var(--primary)]'
              : 'text-muted-foreground hover:bg-primary/10 hover:text-foreground',
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
  const hue = [...name].reduce((a, c) => a + c.charCodeAt(0), 0) % 360
  return (
    <span
      aria-hidden="true"
      className={cn('inline-flex size-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold text-white ring-2 ring-white/10', className)}
      style={{ background: `linear-gradient(135deg, hsl(${hue} 70% 55%), hsl(${(hue + 50) % 360} 70% 40%))` }}
    >
      {initials}
    </span>
  )
}
