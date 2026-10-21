import { Suspense } from 'react'
import { AppShell } from '@/components/app/app-shell'
import { SiteFooter } from '@/components/brand'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Suspense>
        <AppShell>{children}</AppShell>
      </Suspense>
      <SiteFooter className="mb-16 lg:mb-0" />
    </>
  )
}
