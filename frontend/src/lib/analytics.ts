import { ApiError, getStoredToken, requestJson } from './auth'

export interface AnalyticsSummary {
  total_products: number
  total_customers: number
  total_orders: number
  total_revenue: string
  pending_orders: number
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken()
  if (!token) {
    throw new ApiError(401, 'Your session has expired. Please log in again.')
  }
  return { Authorization: `Bearer ${token}` }
}

function readCount(value: unknown, label: string): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0) {
    throw new ApiError(200, `The server returned an invalid ${label}.`)
  }
  return value
}

function readMoney(value: unknown): string {
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  throw new ApiError(200, 'The server returned an invalid revenue total.')
}

function parseSummary(value: unknown): AnalyticsSummary {
  if (value === null || typeof value !== 'object') {
    throw new ApiError(200, 'The server returned an invalid analytics summary.')
  }

  const candidate = value as Record<string, unknown>
  return {
    total_products: readCount(candidate.total_products, 'product count'),
    total_customers: readCount(candidate.total_customers, 'customer count'),
    total_orders: readCount(candidate.total_orders, 'order count'),
    total_revenue: readMoney(candidate.total_revenue),
    pending_orders: readCount(candidate.pending_orders, 'pending order count'),
  }
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const body: unknown = await requestJson<unknown>(
    '/api/analytics/summary',
    { method: 'GET', headers: authHeaders() },
    'Could not load analytics.',
  )

  return parseSummary(body)
}
