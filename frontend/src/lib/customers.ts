import { ApiError, getStoredToken, requestJson } from './auth'

export interface Customer {
  id: number
  name: string
  email: string | null
  phone: string | null
  address: string | null
  owner_id: number
  created_at: string
  updated_at: string
}

export interface CustomerPayload {
  name: string
  email: string | null
  phone: string | null
  address: string | null
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken()
  if (!token) {
    throw new ApiError(401, 'Your session has expired. Please log in again.')
  }
  return { Authorization: `Bearer ${token}` }
}

function jsonHeaders(): Record<string, string> {
  return { ...authHeaders(), 'Content-Type': 'application/json' }
}

function parseCustomer(value: unknown): Customer {
  if (value === null || typeof value !== 'object') {
    throw new ApiError(200, 'The server returned an invalid customer.')
  }

  const candidate = value as Record<string, unknown>
  const optionalTextFields = ['email', 'phone', 'address'] as const

  if (
    typeof candidate.id !== 'number' ||
    typeof candidate.name !== 'string' ||
    typeof candidate.owner_id !== 'number' ||
    typeof candidate.created_at !== 'string' ||
    typeof candidate.updated_at !== 'string' ||
    optionalTextFields.some(
      (field) => candidate[field] !== null && typeof candidate[field] !== 'string',
    )
  ) {
    throw new ApiError(200, 'The server returned an invalid customer.')
  }

  return {
    id: candidate.id,
    name: candidate.name,
    email: candidate.email === null ? null : (candidate.email as string),
    phone: candidate.phone === null ? null : (candidate.phone as string),
    address: candidate.address === null ? null : (candidate.address as string),
    owner_id: candidate.owner_id,
    created_at: candidate.created_at,
    updated_at: candidate.updated_at,
  }
}

export async function listCustomers(): Promise<Customer[]> {
  const body: unknown = await requestJson<unknown>(
    '/api/customers',
    {
      method: 'GET',
      headers: authHeaders(),
    },
    'Could not load customers.',
  )

  if (!Array.isArray(body)) {
    throw new ApiError(200, 'The server returned an invalid customer list.')
  }
  return body.map(parseCustomer)
}

export async function createCustomer(payload: CustomerPayload): Promise<Customer> {
  const body: unknown = await requestJson<unknown>(
    '/api/customers',
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify(payload),
    },
    'Could not create customer.',
  )

  return parseCustomer(body)
}

export async function updateCustomer(id: number, payload: CustomerPayload): Promise<Customer> {
  const body: unknown = await requestJson<unknown>(
    `/api/customers/${id}`,
    {
      method: 'PUT',
      headers: jsonHeaders(),
      body: JSON.stringify(payload),
    },
    'Could not update customer.',
  )

  return parseCustomer(body)
}

export async function deleteCustomer(id: number): Promise<void> {
  await requestJson<unknown>(
    `/api/customers/${id}`,
    {
      method: 'DELETE',
      headers: authHeaders(),
    },
    'Could not delete customer.',
  )
}
