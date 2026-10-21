'use client'

import dynamic from 'next/dynamic'
import { motion, useMotionValue, useSpring, useTransform } from 'motion/react'
import { ArrowRight, BriefcaseBusiness, Building2, Link2, UserRoundCheck, ScanSearch, Database, ShieldAlert, Percent } from 'lucide-react'
import { ButtonLink } from '@/components/ui/primitives'

const HeroScene = dynamic(() => import('@/components/three/hero-scene'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center" role="status">
      <span className="size-40 animate-pulse rounded-full bg-primary/20 blur-2xl" />
      <span className="sr-only">Loading 3D scene</span>
    </div>
  ),
})

const panels = [
  { label: 'Job Offer', sub: 'Verified', Icon: BriefcaseBusiness, className: 'left-[4%] top-[22%]', depth: 26, rotate: -8 },
  { label: 'Recruiter', sub: 'Verified', Icon: UserRoundCheck, className: 'right-[4%] top-[10%]', depth: 18, rotate: 6 },
  { label: 'Company', sub: 'Trusted', Icon: Building2, className: 'left-[0%] top-[52%]', depth: 34, rotate: -6 },
  { label: 'Meeting Link', sub: 'Safe', Icon: Link2, className: 'right-[0%] top-[42%]', depth: 22, rotate: 5 },
]

const stats = [
  { value: '48K+', label: 'Scans Analyzed', Icon: ScanSearch },
  { value: '330M+', label: 'Data Points', Icon: Database },
  { value: '1 in 7', label: 'Jobs Flagged', Icon: ShieldAlert },
  { value: '27-43%', label: 'False Positive Rate', Icon: Percent },
]

export function Hero() {
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const sx = useSpring(mx, { stiffness: 60, damping: 18 })
  const sy = useSpring(my, { stiffness: 60, damping: 18 })

  return (
    <section
      id="home"
      className="relative overflow-hidden"
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect()
        mx.set((e.clientX - r.left) / r.width - 0.5)
        my.set((e.clientY - r.top) / r.height - 0.5)
      }}
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_70%_at_70%_40%,color-mix(in_oklab,var(--primary)_28%,transparent),transparent_70%)]" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-6 px-5 pb-10 pt-10 lg:grid-cols-[1fr_1.1fr] lg:pt-16">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: 'easeOut' }}>
          <h1 className="font-display text-5xl font-bold leading-[1.02] tracking-tight text-foreground text-balance sm:text-6xl lg:text-7xl">
            Trust Before
            <br />
            <span className="text-brand-gradient">You Commit</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-muted-foreground text-pretty">
            {'Check job offers, recruiters, companies and meeting links with real evidence — not just opinions.'}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <ButtonLink href="/verify" size="lg">
              Start Verification <ArrowRight className="size-4" aria-hidden="true" />
            </ButtonLink>
            <ButtonLink href="/dashboard" size="lg" variant="outline">
              Explore Platform
            </ButtonLink>
          </div>
        </motion.div>

        <div className="relative h-[420px] sm:h-[520px] lg:h-[600px]">
          <HeroScene />
          {panels.map((p, i) => (
            <Panel key={p.label} {...p} index={i} sx={sx} sy={sy} />
          ))}
        </div>
      </div>

      <div className="relative mx-auto max-w-7xl px-5 pb-14">
        <ul className="grid grid-cols-2 gap-6 sm:grid-cols-4 lg:max-w-3xl">
          {stats.map(({ value, label, Icon }, i) => (
            <motion.li
              key={label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="flex items-center gap-3 sm:border-r sm:border-border sm:pr-4 last:border-0"
            >
              <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-full border border-border-strong bg-primary/10 text-accent">
                <Icon className="size-4" aria-hidden="true" />
              </span>
              <div>
                <p className="text-xl font-semibold text-foreground">{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            </motion.li>
          ))}
        </ul>
        <p className="mt-4 text-[11px] text-muted-foreground/80">Illustrative platform figures shown for demonstration.</p>
      </div>
    </section>
  )
}

function Panel({
  label,
  sub,
  Icon,
  className,
  depth,
  rotate,
  index,
  sx,
  sy,
}: (typeof panels)[number] & {
  index: number
  sx: ReturnType<typeof useSpring>
  sy: ReturnType<typeof useSpring>
}) {
  const x = useTransform(sx, (v) => v * depth * -1.4)
  const y = useTransform(sy, (v) => v * depth * -1.4)
  return (
    <motion.div
      aria-hidden="true"
      style={{ x, y, rotate }}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.6 + index * 0.15, duration: 0.6 }}
      className={`pointer-events-none absolute hidden sm:block ${className}`}
    >
      <div
        className="glass glow-border flex items-center gap-3 rounded-xl px-4 py-3"
        style={{ animation: `float-y ${5 + index}s ease-in-out ${index * 0.6}s infinite` }}
      >
        <span className="inline-flex size-9 items-center justify-center rounded-lg bg-primary/25 text-accent">
          <Icon className="size-4" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-medium text-foreground">{label}</p>
          <p className="text-sm text-accent">{sub}</p>
        </div>
      </div>
    </motion.div>
  )
}
