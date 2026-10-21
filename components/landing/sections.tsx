'use client'

import Image from 'next/image'
import { motion } from 'motion/react'
import { BriefcaseBusiness, UserRoundCheck, Building2, Link2, FileSearch, Network, ClipboardCheck, ArrowRight } from 'lucide-react'
import { ButtonLink, Card, StatusBadge } from '@/components/ui/primitives'

const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: 0.6, ease: 'easeOut' as const },
}

function SectionTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return (
    <motion.div {...reveal} className="mx-auto max-w-2xl text-center">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">{eyebrow}</p>
      <h2 className="mt-3 font-display text-3xl font-bold text-foreground text-balance sm:text-4xl">{title}</h2>
      <p className="mt-4 text-muted-foreground text-pretty">{text}</p>
    </motion.div>
  )
}

const features = [
  { Icon: BriefcaseBusiness, title: 'Job Offers', text: 'Validate salary, role, and posting sources against independent market and registry data.' },
  { Icon: UserRoundCheck, title: 'Recruiters', text: 'Confirm recruiter identity, history, and company affiliation before you share anything.' },
  { Icon: Building2, title: 'Companies', text: 'Check registration, domain age, address, and public signals for consistency.' },
  { Icon: Link2, title: 'Meeting Links', text: 'Inspect invite URLs for redirects, lookalike domains, and host mismatches.' },
]

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
      <SectionTitle eyebrow="Features" title="One lens for every opportunity" text="LifeLens Ω cross-checks the claims behind an offer and shows you the evidence, so you can decide with confidence." />
      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {features.map(({ Icon, title, text }, i) => (
          <motion.div key={title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }}>
            <Card className="group h-full p-6 transition-all duration-300 hover:-translate-y-1 hover:border-border-strong hover:shadow-[0_20px_50px_-20px_var(--primary)]">
              <span className="inline-flex size-11 items-center justify-center rounded-xl bg-primary/15 text-accent ring-1 ring-border-strong transition-transform group-hover:scale-110">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <h3 className="mt-5 font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{text}</p>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

const steps = [
  { Icon: ClipboardCheck, title: 'Submit details', text: 'Paste a job post, recruiter email, company name, or meeting link.' },
  { Icon: Network, title: 'Cross-verify evidence', text: 'Each claim is checked against multiple independent sources.' },
  { Icon: FileSearch, title: 'Read the verdict', text: 'See a transparent report: what passed, what needs review, and why.' },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
      <SectionTitle eyebrow="How it works" title="Evidence, not opinions" text="Three steps from a suspicious message to a decision you can defend." />
      <ol className="mt-12 grid gap-5 md:grid-cols-3">
        {steps.map(({ Icon, title, text }, i) => (
          <motion.li key={title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.1 }}>
            <Card className="relative h-full p-6">
              <span className="absolute right-5 top-5 font-display text-4xl font-bold text-primary/25">{`0${i + 1}`}</span>
              <span className="inline-flex size-11 items-center justify-center rounded-full bg-brand-gradient text-white shadow-[0_0_24px_-4px_var(--primary)]">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <h3 className="mt-5 font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{text}</p>
            </Card>
          </motion.li>
        ))}
      </ol>
    </section>
  )
}

export function VerificationPreview() {
  return (
    <section id="verification" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <motion.div {...reveal}>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Verification</p>
          <h2 className="mt-3 font-display text-3xl font-bold text-foreground text-balance sm:text-4xl">A transparent report for every check</h2>
          <p className="mt-4 text-muted-foreground text-pretty">
            Every verdict comes with its claims, sources, and a confidence score. Nothing is marked safe without evidence — when sources are unavailable, results stay pending.
          </p>
          <ul className="mt-6 flex flex-col gap-3">
            {[
              ['Company exists & registered', 'verified'],
              ['Recruiter is legitimate', 'review'],
              ['Domain registered 9 days ago', 'risk'],
            ].map(([label, s]) => (
              <li key={label} className="glass flex items-center justify-between rounded-xl px-4 py-3 text-sm">
                <span className="text-foreground">{label}</span>
                <StatusBadge status={s as 'verified' | 'review' | 'risk'} />
              </li>
            ))}
          </ul>
          <ButtonLink href="/reports" variant="outline" className="mt-8">
            View sample report <ArrowRight className="size-4" aria-hidden="true" />
          </ButtonLink>
        </motion.div>
        <motion.div {...reveal} className="relative">
          <div aria-hidden="true" className="absolute inset-10 rounded-full bg-primary/30 blur-3xl" />
          <Image
            src="/images/shield-hologram.png"
            alt="Holographic security shield hovering above a glowing verification platform"
            width={640}
            height={640}
            className="relative mx-auto w-full max-w-md rounded-3xl"
          />
        </motion.div>
      </div>
    </section>
  )
}

export function About() {
  return (
    <section id="about" className="mx-auto max-w-5xl scroll-mt-20 px-5 py-20">
      <motion.div {...reveal}>
        <Card className="glow-border relative overflow-hidden p-8 text-center sm:p-12">
          <div aria-hidden="true" className="absolute -top-24 left-1/2 size-72 -translate-x-1/2 rounded-full bg-primary/30 blur-3xl" />
          <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-accent">About</p>
          <h2 className="relative mt-3 font-display text-3xl font-bold text-foreground text-balance sm:text-4xl">Built for people starting their careers</h2>
          <p className="relative mx-auto mt-4 max-w-2xl text-muted-foreground text-pretty">
            Recruitment scams target students and job seekers first. LifeLens Ω gives you the same evidence a security analyst would gather — in plain language, with your privacy protected.
          </p>
          <div className="relative mt-8 flex flex-wrap justify-center gap-4">
            <ButtonLink href="/verify" size="lg">
              Start Verification <ArrowRight className="size-4" aria-hidden="true" />
            </ButtonLink>
            <ButtonLink href="/dashboard" size="lg" variant="outline">
              Explore Platform
            </ButtonLink>
          </div>
        </Card>
      </motion.div>
    </section>
  )
}
