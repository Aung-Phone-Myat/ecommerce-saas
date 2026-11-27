const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
const TOKEN_STORAGE_KEY = 'ecommerce_access_token'
const REQUEST_TIMEOUT_MS = 10_000

let memoryToken: string | null = null

export interface CurrentUser {
  id: number
  username: string
  email: string
  created_at: string
  updated_at: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

interface RequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function getStoredToken(): string | null {
  try {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
    if (token?.trim()) {
      memoryToken = token
      return token
    }
    if (token !== null) {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // localStorage may be disabled; fall back to in-memory storage.
  }
  return memoryToken
}

export function setStoredToken(token: string): void {
  memoryToken = token
  try {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } catch {
    // Keep the in-memory token so the current session still works.
  }
}

export function clearStoredToken(): void {
  memoryToken = null
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    // Nothing else to clear.
  }
}

function formatDetail(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) => {
      if (item === null || typeof item !== 'object' || !('msg' in item)) return []
      const message = (item as { msg?: unknown }).msg
      return typeof message === 'string' && message.trim() ? [message] : []
    })
    if (messages.length > 0) {
      return messages.join(' — ')
    }
  }

  return null
}

async function readErrorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (body !== null && typeof body === 'object' && 'detail' in body) {
      const detail = formatDetail((body as { detail?: unknown }).detail)
      if (detail !== null) {
        return detail
      }
    }
  } catch {
    // The response did not contain valid JSON.
  }
  return fallback
}

export async function requestJson<T>(path: string, options: RequestOptions, fallbackError: string): Promise<T> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method,
      headers: {
        Accept: 'application/json',
        ...options.headers,
      },
      body: options.body,
      signal: controller.signal,
    })
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError(0, 'The request timed out. Please try again.')
    }
    throw new ApiError(0, 'Could not connect to the server. Check that the API is running.')
  } finally {
    window.clearTimeout(timeoutId)
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response, fallbackError))
  }

  if (response.status === 204) {
    return undefined as T
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(response.status, 'The server returned an invalid response.')
  }
}

function isCurrentUser(value: unknown): value is CurrentUser {
  if (value === null || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  return (
    typeof candidate.id === 'number' &&
    typeof candidate.username === 'string' &&
    typeof candidate.email === 'string' &&
    typeof candidate.created_at === 'string' &&
    typeof candidate.updated_at === 'string'
  )
}

export async function login(identifier: string, password: string): Promise<string> {
  const normalizedIdentifier = identifier.trim()
  const credentials = normalizedIdentifier.includes('@')
    ? { email: normalizedIdentifier, password }
    : { username: normalizedIdentifier, password }

  const body: unknown = await requestJson<unknown>(
    '/api/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    },
    'Unable to log in.',
  )

  if (body === null || typeof body !== 'object' || !('access_token' in body)) {
    throw new ApiError(200, 'The server did not return an access token.')
  }
  const token = (body as { access_token?: unknown }).access_token
  if (typeof token !== 'string' || !token) {
    throw new ApiError(200, 'The server did not return an access token.')
  }
  return token
}

export async function registerUser(payload: RegisterPayload): Promise<void> {
  await requestJson<unknown>(
    '/api/auth/register',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    'Unable to create account.',
  )
}

export async function getCurrentUser(token: string): Promise<CurrentUser> {
  const user: unknown = await requestJson<unknown>(
    '/api/users/me',
    {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
    },
    'Could not load your profile.',
  )

  if (!isCurrentUser(user)) {
    throw new ApiError(200, 'The server returned an invalid profile.')
  }
  return user
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (error instanceof ApiError) return error.message
  return fallback
}
