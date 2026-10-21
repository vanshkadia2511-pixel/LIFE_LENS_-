import type { Metadata } from 'next'
import { DashboardView } from '@/components/app/dashboard-view'

export const metadata: Metadata = { title: 'Dashboard — LifeLens Ω' }

export default function DashboardPage() {
  return <DashboardView />
}
