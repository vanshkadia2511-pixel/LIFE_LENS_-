import type { Status } from '@/components/ui/primitives'

export type EntityKind = 'Company' | 'Recruiter' | 'Job Offer' | 'Interview' | 'Meeting'

export type Activity = {
  id: string
  name: string
  kind: EntityKind
  status: Status
  time: string
}

export const DEMO_USER = { name: 'Alex Carter', role: 'Student' }

export const dashboardStats = [
  { key: 'total', label: 'Total Verifications', value: 12, delta: '+20% from last week', tone: 'primary' },
  { key: 'verified', label: 'Verified', value: 8, delta: '+33% from last week', tone: 'success' },
  { key: 'review', label: 'Needs Review', value: 3, delta: '+15% from last week', tone: 'warning' },
  { key: 'risk', label: 'High Risk', value: 1, delta: '+50% from last week', tone: 'danger' },
] as const

export const recentActivity: Activity[] = [
  { id: 'a1', name: 'TechCorp Solutions', kind: 'Company', status: 'verified', time: '2 hours ago' },
  { id: 'a2', name: 'Sarah Johnson', kind: 'Recruiter', status: 'review', time: '4 hours ago' },
  { id: 'a3', name: 'Global Talent Hub', kind: 'Job Offer', status: 'verified', time: '6 hours ago' },
  { id: 'a4', name: 'Zoom Meeting', kind: 'Interview', status: 'safe', time: '1 day ago' },
  { id: 'a5', name: 'Acme Corp', kind: 'Company', status: 'risk', time: '1 day ago' },
]

export const activityTrend = [
  { label: 'Aug 18', value: 3 },
  { label: 'Aug 19', value: 5 },
  { label: 'Aug 20', value: 4 },
  { label: 'Aug 21', value: 7 },
  { label: 'Aug 22', value: 6 },
  { label: 'Aug 23', value: 9 },
  { label: 'Aug 24', value: 12 },
]

export type AnalysisRow = {
  id: string
  title: string
  company: string
  recruiter: string
  risk: 'low' | 'medium' | 'high'
  location: string
  remote: boolean
}

export const analysisRows: AnalysisRow[] = [
  { id: 'job-1', title: 'Software Engineer', company: 'TechCorp Solutions', recruiter: 'Sarah Johnson', risk: 'low', location: 'US', remote: false },
  { id: 'job-2', title: 'Frontend Developer', company: 'BrightTech', recruiter: 'Mike Wilson', risk: 'medium', location: 'Remote', remote: true },
  { id: 'job-3', title: 'Data Analyst', company: 'Global Talent Hub', recruiter: 'Emily Davis', risk: 'low', location: 'US', remote: false },
  { id: 'job-4', title: 'Product Manager', company: 'NextGen Systems', recruiter: 'David Brown', risk: 'high', location: 'Remote', remote: true },
  { id: 'job-5', title: 'Full Stack Developer', company: 'Innovate Labs', recruiter: 'Jessica Taylor', risk: 'medium', location: 'US', remote: false },
  { id: 'job-6', title: 'DevOps Engineer', company: 'CloudNova', recruiter: 'Priya Shah', risk: 'low', location: 'UK', remote: false },
  { id: 'job-7', title: 'UX Designer', company: 'PixelForge', recruiter: 'Tom Becker', risk: 'medium', location: 'Remote', remote: true },
]

export type Claim = { label: string; status: Status }

export type EvidenceReport = {
  id: string
  title: string
  subject: string
  verdict: Status
  verdictLabel: string
  confidence: number
  createdAt: string
  entity: { label: string; value: string }[]
  claims: Claim[]
  sources: { name: string; type: string; checked: string; result: Status }[]
  why: string
  cect: { label: string; score: number }[]
}

export const demoReports: EvidenceReport[] = [
  {
    id: 'LL-2025-0047',
    title: 'Software Engineer',
    subject: 'Job Offer · TechCorp Solutions · Software Engineer',
    verdict: 'review',
    verdictLabel: 'Needs Review',
    confidence: 68,
    createdAt: 'Aug 24, 2025 · 2:34 PM',
    entity: [
      { label: 'Company', value: 'TechCorp Solutions' },
      { label: 'Domain', value: 'techcorp.com' },
      { label: 'Location', value: 'United States' },
      { label: 'Job Title', value: 'Software Engineer' },
      { label: 'Source Platform', value: 'LinkedIn' },
    ],
    claims: [
      { label: 'Company exists & registered', status: 'verified' },
      { label: 'Domain is active & matches', status: 'verified' },
      { label: 'Recruiter is legitimate', status: 'review' },
      { label: 'Salary range is realistic', status: 'review' },
      { label: 'Location matches company', status: 'verified' },
    ],
    sources: [
      { name: 'Companies registry lookup', type: 'Registry', checked: '2:31 PM', result: 'verified' },
      { name: 'DNS / WHOIS record', type: 'Domain', checked: '2:31 PM', result: 'verified' },
      { name: 'Professional network profile', type: 'Identity', checked: '2:32 PM', result: 'review' },
      { name: 'Salary benchmark dataset', type: 'Market', checked: '2:33 PM', result: 'review' },
      { name: 'Office address geocode', type: 'Location', checked: '2:33 PM', result: 'verified' },
    ],
    why: "Most information is consistent and verified. However, the recruiter's profile has limited history and the job post source shows some inconsistencies. We recommend further verification.",
    cect: [
      { label: 'Coherence', score: 0.74 },
      { label: 'Evidence independence', score: 0.62 },
      { label: 'Contradiction resistance', score: 0.7 },
      { label: 'Temporal consistency', score: 0.66 },
    ],
  },
  {
    id: 'LL-2025-0046',
    title: 'Acme Corp',
    subject: 'Company · Acme Corp',
    verdict: 'risk',
    verdictLabel: 'High Risk',
    confidence: 81,
    createdAt: 'Aug 23, 2025 · 9:12 AM',
    entity: [
      { label: 'Company', value: 'Acme Corp' },
      { label: 'Domain', value: 'acme-careers-hr.net' },
      { label: 'Location', value: 'Unknown' },
      { label: 'Job Title', value: 'Data Entry Specialist' },
      { label: 'Source Platform', value: 'Messaging app' },
    ],
    claims: [
      { label: 'Company exists & registered', status: 'risk' },
      { label: 'Domain is active & matches', status: 'risk' },
      { label: 'Recruiter is legitimate', status: 'risk' },
      { label: 'Salary range is realistic', status: 'review' },
      { label: 'Location matches company', status: 'review' },
    ],
    sources: [
      { name: 'Companies registry lookup', type: 'Registry', checked: '9:10 AM', result: 'risk' },
      { name: 'DNS / WHOIS record', type: 'Domain', checked: '9:10 AM', result: 'risk' },
      { name: 'Professional network profile', type: 'Identity', checked: '9:11 AM', result: 'risk' },
    ],
    why: 'The domain was registered 9 days ago and does not match any registered entity. The recruiter requested an upfront equipment fee, a common fraud pattern.',
    cect: [
      { label: 'Coherence', score: 0.21 },
      { label: 'Evidence independence', score: 0.55 },
      { label: 'Contradiction resistance', score: 0.18 },
      { label: 'Temporal consistency', score: 0.3 },
    ],
  },
  {
    id: 'LL-2025-0045',
    title: 'Global Talent Hub',
    subject: 'Job Offer · Global Talent Hub · Data Analyst',
    verdict: 'verified',
    verdictLabel: 'Verified',
    confidence: 92,
    createdAt: 'Aug 22, 2025 · 4:02 PM',
    entity: [
      { label: 'Company', value: 'Global Talent Hub' },
      { label: 'Domain', value: 'globaltalenthub.com' },
      { label: 'Location', value: 'United States' },
      { label: 'Job Title', value: 'Data Analyst' },
      { label: 'Source Platform', value: 'Company careers page' },
    ],
    claims: [
      { label: 'Company exists & registered', status: 'verified' },
      { label: 'Domain is active & matches', status: 'verified' },
      { label: 'Recruiter is legitimate', status: 'verified' },
      { label: 'Salary range is realistic', status: 'verified' },
      { label: 'Location matches company', status: 'verified' },
    ],
    sources: [
      { name: 'Companies registry lookup', type: 'Registry', checked: '4:00 PM', result: 'verified' },
      { name: 'DNS / WHOIS record', type: 'Domain', checked: '4:00 PM', result: 'verified' },
      { name: 'Professional network profile', type: 'Identity', checked: '4:01 PM', result: 'verified' },
    ],
    why: 'All claims were corroborated by independent sources with no contradictions.',
    cect: [
      { label: 'Coherence', score: 0.95 },
      { label: 'Evidence independence', score: 0.9 },
      { label: 'Contradiction resistance', score: 0.93 },
      { label: 'Temporal consistency', score: 0.88 },
    ],
  },
]

export const ledgerEntries = [
  { id: 'EV-1042', report: 'LL-2025-0047', source: 'Companies registry lookup', hash: '7f3a…c91e', time: 'Aug 24, 2:31 PM', status: 'verified' as Status },
  { id: 'EV-1041', report: 'LL-2025-0047', source: 'DNS / WHOIS record', hash: '19bd…04aa', time: 'Aug 24, 2:31 PM', status: 'verified' as Status },
  { id: 'EV-1040', report: 'LL-2025-0047', source: 'Professional network profile', hash: 'e2c0…7b13', time: 'Aug 24, 2:32 PM', status: 'review' as Status },
  { id: 'EV-1039', report: 'LL-2025-0046', source: 'DNS / WHOIS record', hash: 'a91f…3d22', time: 'Aug 23, 9:10 AM', status: 'risk' as Status },
  { id: 'EV-1038', report: 'LL-2025-0046', source: 'Companies registry lookup', hash: '5cc8…e810', time: 'Aug 23, 9:10 AM', status: 'risk' as Status },
  { id: 'EV-1037', report: 'LL-2025-0045', source: 'Companies registry lookup', hash: '0b77…91fe', time: 'Aug 22, 4:00 PM', status: 'verified' as Status },
]
