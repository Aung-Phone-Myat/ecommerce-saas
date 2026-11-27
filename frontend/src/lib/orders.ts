import { ApiError, getStoredToken, requestJson } from './auth'

export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'completed' | 'cancelled'

const ORDER_STATUSES: OrderStatus[] = ['pending', 'paid', 'shipped', 'completed', 'cancelled']

export interface OrderCustomerSummary {
  id: number
  name: string
  email: string | null
  phone: string | null
  address: string | null
}

export interface OrderProductSummary {
  id: number
  name: string
  description: string | null
  price: string
  stock_quantity: number
}

export interface OrderItemRead {
  id: number
  product_id: number
  product: OrderProductSummary
  quantity: number
  price_at_time_of_purchase: string
  line_total: string
}

export interface Order {
  id: number
  customer_id: number
  customer: OrderCustomerSummary
  owner_id: number
  status: OrderStatus
  total_amount: string
  items: OrderItemRead[]
  created_at: string
  updated_at: string
}

export interface OrderItemPayload {
  product_id: number
  quantity: number
}

export interface OrderCreatePayload {
  customer_id: number
  items: OrderItemPayload[]
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

function invalid(label: string): never {
  throw new ApiError(200, `The server returned an invalid ${label}.`)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object'
}

function readString(value: unknown, label: string): string {
  if (typeof value !== 'string') invalid(label)
  return value
}

function readNumber(value: unknown, label: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) invalid(label)
  return value
}

function readOptionalString(value: unknown, label: string): string | null {
  if (value === null) return null
  return readString(value, label)
}

function readDecimal(value: unknown, label: string): string {
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  return invalid(label)
}

function parseCustomerSummary(value: unknown): OrderCustomerSummary {
  if (!isRecord(value)) invalid('order customer.')

  return {
    id: readNumber(value.id, 'order customer id'),
    name: readString(value.name, 'order customer name'),
    email: readOptionalString(value.email, 'order customer email'),
    phone: readOptionalString(value.phone, 'order customer phone'),
    address: readOptionalString(value.address, 'order customer address'),
  }
}

function parseProductSummary(value: unknown): OrderProductSummary {
  if (!isRecord(value)) invalid('order product.')

  return {
    id: readNumber(value.id, 'order product id'),
    name: readString(value.name, 'order product name'),
    description: readOptionalString(value.description, 'order product description'),
    price: readDecimal(value.price, 'order product price'),
    stock_quantity: readNumber(value.stock_quantity, 'order product stock'),
  }
}

function parseOrderItem(value: unknown): OrderItemRead {
  if (!isRecord(value)) invalid('order item.')

  return {
    id: readNumber(value.id, 'order item id'),
    product_id: readNumber(value.product_id, 'order item product id'),
    product: parseProductSummary(value.product),
    quantity: readNumber(value.quantity, 'order item quantity'),
    price_at_time_of_purchase: readDecimal(
      value.price_at_time_of_purchase,
      'order item purchase price',
    ),
    line_total: readDecimal(value.line_total, 'order item total'),
  }
}

function parseOrder(value: unknown): Order {
  if (!isRecord(value)) invalid('order.')

  const status = value.status
  if (typeof status !== 'string' || !ORDER_STATUSES.includes(status as OrderStatus)) {
    invalid('order status')
  }
  if (!Array.isArray(value.items)) invalid('order item list.')

  return {
    id: readNumber(value.id, 'order id'),
    customer_id: readNumber(value.customer_id, 'order customer id'),
    customer: parseCustomerSummary(value.customer),
    owner_id: readNumber(value.owner_id, 'order owner id'),
    status: status as OrderStatus,
    total_amount: readDecimal(value.total_amount, 'order total'),
    items: value.items.map(parseOrderItem),
    created_at: readString(value.created_at, 'order creation date'),
    updated_at: readString(value.updated_at, 'order update date'),
  }
}

export async function getOrders(): Promise<Order[]> {
  const body: unknown = await requestJson<unknown>(
    '/api/orders',
    {
      method: 'GET',
      headers: authHeaders(),
    },
    'Could not load orders.',
  )

  if (!Array.isArray(body)) {
    throw new ApiError(200, 'The server returned an invalid order list.')
  }
  return body.map(parseOrder)
}

export async function createOrder(payload: OrderCreatePayload): Promise<Order> {
  const body: unknown = await requestJson<unknown>(
    '/api/orders',
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify(payload),
    },
    'Could not create order.',
  )

  return parseOrder(body)
}

export async function updateOrderStatus(id: number, status: OrderStatus): Promise<Order> {
  const body: unknown = await requestJson<unknown>(
    `/api/orders/${id}/status`,
    {
      method: 'PUT',
      headers: jsonHeaders(),
      body: JSON.stringify({ status }),
    },
    'Could not update order status.',
  )

  return parseOrder(body)
}
