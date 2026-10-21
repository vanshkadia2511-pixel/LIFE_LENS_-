'use client'

import { useId } from 'react'
import { motion } from 'motion/react'

export function RingChart({
  segments,
  size = 140,
  stroke = 12,
  center,
  label,
}: {
  segments: { value: number; color: string; label: string }[]
  size?: number
  stroke?: number
  center: React.ReactNode
  label: string
}) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const total = segments.reduce((a, s) => a + s.value, 0) || 1
  let offset = 0
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={label} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--muted)" strokeWidth={stroke} />
        {segments.map((s, i) => {
          const len = (s.value / total) * c
          const dash = Math.max(len - 3, 0)
          const el = (
            <motion.circle
              key={s.label}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDashoffset={-offset}
              initial={{ strokeDasharray: `0 ${c}` }}
              animate={{ strokeDasharray: `${dash} ${c}` }}
              transition={{ duration: 1, delay: 0.2 + i * 0.15, ease: 'easeOut' }}
              style={{ filter: `drop-shadow(0 0 6px ${s.color})` }}
            />
          )
          offset += len
          return el
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">{center}</div>
    </div>
  )
}

export function AreaChart({
  data,
  height = 140,
  label,
}: {
  data: { label: string; value: number }[]
  height?: number
  label: string
}) {
  const id = useId()
  const w = 400
  const h = height
  const pad = 8
  const max = Math.max(...data.map((d) => d.value)) * 1.15
  const pts = data.map((d, i) => [pad + (i / (data.length - 1)) * (w - pad * 2), h - pad - (d.value / max) * (h - pad * 2)] as const)
  const line = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const area = `${line} L${pts.at(-1)![0]},${h} L${pts[0][0]},${h} Z`
  return (
    <figure>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-auto w-full" role="img" aria-label={label} preserveAspectRatio="none">
        <defs>
          <linearGradient id={`${id}-fill`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.45" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((t) => (
          <line key={t} x1={0} x2={w} y1={h * t} y2={h * t} stroke="var(--border)" strokeDasharray="3 5" />
        ))}
        <motion.path d={area} fill={`url(#${id}-fill)`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.8 }} />
        <motion.path
          d={line}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={2.5}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.4, ease: 'easeInOut' }}
          style={{ filter: 'drop-shadow(0 0 6px var(--accent))' }}
        />
        {pts.map(([x, y], i) => (
          <motion.circle key={i} cx={x} cy={y} r={3.5} fill="var(--card-solid)" stroke="var(--accent)" strokeWidth={2} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.3 + i * 0.12 }} />
        ))}
      </svg>
      <figcaption className="mt-2 flex justify-between text-[10px] text-muted-foreground">
        {data.map((d) => (
          <span key={d.label}>{d.label}</span>
        ))}
      </figcaption>
    </figure>
  )
}

export function Sparkline({ values, color }: { values: number[]; color: string }) {
  const w = 80
  const h = 24
  const max = Math.max(...values)
  const min = Math.min(...values)
  const d = values
    .map((v, i) => `${i ? 'L' : 'M'}${(i / (values.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * (h - 4) - 2}`)
    .join(' ')
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      <motion.path d={d} fill="none" stroke={color} strokeWidth={1.8} initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2 }} />
    </svg>
  )
}
