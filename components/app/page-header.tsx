import { DemoBadge } from '@/components/ui/primitives'

export function PageHeader({
  title,
  description,
  demo,
  action,
}: {
  title: string
  description?: React.ReactNode
  demo?: boolean
  action?: React.ReactNode
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance">{title}</h1>
          {demo && <DemoBadge />}
        </div>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  )
}
