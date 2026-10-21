'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'motion/react'
import { ShieldCheck, CircleCheck, CircleAlert, TriangleAlert, ArrowRight } from 'lucide-react'
import { PageHeader } from '@/components/app/page-header'
import { AreaChart, RingChart, Sparkline } from '@/components/charts'
import { Avatar, ButtonLink, Card, CardHeader, StatusBadge, Tabs } from '@/components/ui/primitives'
import { activityTrend, dashboardStats, DEMO_USER, recentActivity } from '@/lib/demo-data'
import { cn } from '@/lib/utils'

const toneStyles = {
  primary: { ring: 'border-primary/50', text: 'text-accent', bg: 'from-primary/25', Icon: ShieldCheck, color: 'var(--accent)' },
  success: { ring: 'border-success/50', text: 'text-success', bg: 'from-success/20', Icon: CircleCheck, color: 'var(--success)' },
  warning: { ring: 'border-warning/50', text: 'text-warning', bg: 'from-warning/20', Icon: CircleAlert, color: 'var(--warning)' },
  danger: { ring: 'border-danger/50', text: 'text-danger', bg: 'from-danger/20', Icon: TriangleAlert, color: 'var(--danger)' },
}

type Filter = 'all' | 'verified' | 'review' | 'risk'

export function DashboardView() {
  const [filter, setFilter] = useState<Filter>('all')
  const items = recentActivity.filter((a) => {
    if (filter === 'all') return true
    if (filter === 'verified') return a.status === 'verified' || a.status === 'safe'
    return a.status === filter
  })

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        title={`Welcome back, ${DEMO_USER.name.split(' ')[0]}`}
        description="Here's what's happening with your verifications today."
        demo
        action={
          <ButtonLink href="/verify">
            New Verification <ArrowRight className="size-4" aria-hidden="true" />
          </ButtonLink>
        }
      />

      <ul className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {dashboardStats.map((s, i) => {
          const t = toneStyles[s.tone]
          return (
            <motion.li key={s.key} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}>
              <Card className={cn('relative overflow-hidden bg-gradient-to-br to-transparent p-4 transition-transform hover:-translate-y-0.5', t.bg, t.ring)}>
                <div className="flex items-center gap-2">
                  <t.Icon className={cn('size-4', t.text)} aria-hidden="true" />
                  <p className={cn('text-xs font-medium', t.text)}>{s.label}</p>
                </div>
                <div className="mt-3 flex items-end justify-between gap-2">
                  <p className="text-4xl font-semibold tabular-nums text-foreground">{s.value}</p>
                  <Sparkline values={[2, 4, 3, 5, 4, 6, s.value]} color={t.color} />
                </div>
                <p className={cn('mt-2 text-[11px]', t.text)}>{s.delta}</p>
              </Card>
            </motion.li>
          )
        })}
      </ul>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.25fr_1fr]">
        <Card>
          <CardHeader
            title="Recent Activity"
            action={
              <Tabs
                label="Filter activity"
                value={filter}
                onChange={setFilter}
                tabs={[
                  { value: 'all', label: 'All' },
                  { value: 'verified', label: 'Verified' },
                  { value: 'review', label: 'Review' },
                  { value: 'risk', label: 'Risk' },
                ]}
              />
            }
          />
          <ul className="flex flex-col divide-y divide-border px-5 pb-3 pt-2">
            {items.length === 0 && <li className="py-8 text-center text-sm text-muted-foreground">No activity matches this filter.</li>}
            {items.map((a) => (
              <li key={a.id}>
                <Link href="/reports" className="-mx-2 flex items-center gap-3 rounded-lg px-2 py-3 transition-colors hover:bg-primary/8">
                  <Avatar name={a.name} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">
                      {a.name} <span className="font-normal text-muted-foreground">({a.kind})</span>
                    </p>
                    <p className="text-[11px] text-muted-foreground">{a.time}</p>
                  </div>
                  <StatusBadge status={a.status} />
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader title="Verification Overview" />
          <div className="flex flex-wrap items-center gap-6 px-5 pt-4">
            <RingChart
              label="12 total checks: 8 verified, 3 need review, 1 high risk"
              segments={[
                { value: 8, color: 'var(--success)', label: 'Verified' },
                { value: 3, color: 'var(--warning)', label: 'Needs Review' },
                { value: 1, color: 'var(--danger)', label: 'High Risk' },
              ]}
              center={
                <>
                  <span className="text-3xl font-semibold text-foreground">12</span>
                  <span className="text-[10px] text-muted-foreground">Total Checks</span>
                </>
              }
            />
            <ul className="flex min-w-40 flex-1 flex-col gap-3 text-sm">
              {[
                ['Verified', '8 (67%)', 'bg-success'],
                ['Needs Review', '3 (25%)', 'bg-warning'],
                ['High Risk', '1 (8%)', 'bg-danger'],
              ].map(([l, v, c]) => (
                <li key={l} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <span className={cn('size-2 rounded-full', c)} />
                    {l}
                  </span>
                  <span className="tabular-nums text-foreground">{v}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="px-5 pb-5 pt-6">
            <p className="mb-2 text-xs font-medium text-muted-foreground">Activity Trend</p>
            <AreaChart data={activityTrend} label="Verifications per day, rising from 3 to 12 over the past week" height={120} />
          </div>
        </Card>
      </div>
    </div>
  )
}
