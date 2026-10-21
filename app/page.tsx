import { SiteHeader } from '@/components/landing/site-header'
import { Hero } from '@/components/landing/hero'
import { Features, HowItWorks, VerificationPreview, About } from '@/components/landing/sections'
import { SiteFooter } from '@/components/brand'

export default function HomePage() {
  return (
    <div className="app-backdrop min-h-dvh">
      <SiteHeader />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <VerificationPreview />
        <About />
      </main>
      <SiteFooter />
    </div>
  )
}
