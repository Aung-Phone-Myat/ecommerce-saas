import { ApiError, getStoredToken, requestJson } from './auth'

export interface Product {
  id: number
  name: string
  description: string | null
  price: string
  stock_quantity: number
  owner_id: number
  created_at: string
  updated_at: string
}

export interface ProductPayload {
  name: string
  description: string | null
  price: string
  stock_quantity: number
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

function parseProduct(value: unknown): Product {
  if (value === null || typeof value !== 'object') {
    throw new ApiError(200, 'The server returned an invalid product.')
  }

  const candidate = value as Record<string, unknown>
  const price = candidate.price
  const hasValidPrice = typeof price === 'string' || typeof price === 'number'

  if (
    typeof candidate.id !== 'number' ||
    typeof candidate.name !== 'string' ||
    (candidate.description !== null && typeof candidate.description !== 'string') ||
    !hasValidPrice ||
    typeof candidate.stock_quantity !== 'number' ||
    typeof candidate.owner_id !== 'number' ||
    typeof candidate.created_at !== 'string' ||
    typeof candidate.updated_at !== 'string'
  ) {
    throw new ApiError(200, 'The server returned an invalid product.')
  }

  return {
    id: candidate.id,
    name: candidate.name,
    description: candidate.description === null ? null : (candidate.description as string),
    price: typeof price === 'string' ? price : String(price),
    stock_quantity: candidate.stock_quantity,
    owner_id: candidate.owner_id,
    created_at: candidate.created_at,
    updated_at: candidate.updated_at,
  }
}

export async function listProducts(): Promise<Product[]> {
  const body: unknown = await requestJson<unknown>(
    '/api/products',
    {
      method: 'GET',
      headers: authHeaders(),
    },
    'Could not load products.',
  )

  if (!Array.isArray(body)) {
    throw new ApiError(200, 'The server returned an invalid product list.')
  }
  return body.map(parseProduct)
}

export async function createProduct(payload: ProductPayload): Promise<Product> {
  const body: unknown = await requestJson<unknown>(
    '/api/products',
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify(payload),
    },
    'Could not create product.',
  )

  return parseProduct(body)
}

export async function updateProduct(id: number, payload: ProductPayload): Promise<Product> {
  const body: unknown = await requestJson<unknown>(
    `/api/products/${id}`,
    {
      method: 'PUT',
      headers: jsonHeaders(),
      body: JSON.stringify(payload),
    },
    'Could not update product.',
  )

  return parseProduct(body)
}

export async function deleteProduct(id: number): Promise<void> {
  await requestJson<unknown>(
    `/api/products/${id}`,
    {
      method: 'DELETE',
      headers: authHeaders(),
    },
    'Could not delete product.',
  )
}
