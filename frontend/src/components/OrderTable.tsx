import type { Order } from '../lib/orders'

interface OrderTableProps {
  orders: Order[]
  isMutating: boolean
  onComplete: (order: Order) => void
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatCurrency(value: string): string {
  const amount = Number(value)
  return Number.isFinite(amount) ? priceFormatter.format(amount) : value
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function formatStatus(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function OrderTable({ orders, isMutating, onComplete }: OrderTableProps) {
  if (orders.length === 0) {
    return (
      <div className="empty-state">
        <p className="muted">No orders yet. Create your first order to get started.</p>
      </div>
    )
  }

  return (
    <div className="product-table-wrapper">
      <table className="product-table">
        <thead>
          <tr>
            <th scope="col">Order ID</th>
            <th scope="col">Customer Name</th>
            <th scope="col">Total Amount</th>
            <th scope="col">Status</th>
            <th scope="col">Date</th>
            <th scope="col">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td className="order-id">#{order.id}</td>
              <td>
                <span className="product-name">{order.customer.name}</span>
                <span className="product-description">{order.items.length} item(s)</span>
              </td>
              <td className="order-total-cell">{formatCurrency(order.total_amount)}</td>
              <td>
                <span className={`order-status order-status--${order.status}`}>
                  {formatStatus(order.status)}
                </span>
              </td>
              <td className="order-date">{formatDate(order.created_at)}</td>
              <td className="product-actions">
                {order.status === 'completed' ? (
                  <span className="muted">Done</span>
                ) : (
                  <button
                    type="button"
                    className="table-button"
                    onClick={() => onComplete(order)}
                    disabled={isMutating}
                    aria-label={`Mark order ${order.id} as completed`}
                  >
                    Mark as Completed
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
