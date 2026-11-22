import type { ReactNode } from 'react'

export type StatIcon = 'revenue' | 'orders' | 'customers' | 'products' | 'pending'

interface StatCardProps {
  label: string
  value: string
  icon: StatIcon
  hint?: string
  featured?: boolean
  warning?: boolean
}

const ICONS: Record<StatIcon, ReactNode> = {
  revenue: (
    <>
      <path d="M12 2v20" />
      <path d="M17 6.5H9.5a2.5 2.5 0 0 0 0 5h5a2.5 2.5 0 0 1 0 5H6" />
    </>
  ),
  orders: (
    <>
      <path d="M6 8h12l1 12H5L6 8Z" />
      <path d="M9 9V6a3 3 0 0 1 6 0v3" />
    </>
  ),
  customers: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <path d="M16 5.5a3 3 0 0 1 0 5.5" />
      <path d="M18 14c2 .9 3 2.8 3 5" />
    </>
  ),
  products: (
    <>
      <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" />
      <path d="m4 7.5 8 4.5 8-4.5" />
      <path d="M12 12v9" />
    </>
  ),
  pending: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
}

export function StatCard({
  label,
  value,
  icon,
  hint,
  featured = false,
  warning = false,
}: StatCardProps) {
  const className = `stat-card${featured ? ' stat-card--featured' : ''}${warning ? ' stat-card--warning' : ''}`

  return (
    <article className={className}>
      <div className="stat-card__heading">
        <span className="stat-card__icon" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {ICONS[icon]}
          </svg>
        </span>
        <span className="stat-card__label">{label}</span>
      </div>
      <strong className="stat-card__value">{value}</strong>
      {hint !== undefined && <p className="stat-card__hint">{hint}</p>}
    </article>
  )
}
