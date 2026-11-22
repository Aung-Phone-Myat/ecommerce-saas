import type { Customer } from '../lib/customers'

interface CustomerTableProps {
  customers: Customer[]
  isMutating: boolean
  onEdit: (customer: Customer) => void
  onDelete: (customerId: number) => void
}

export function CustomerTable({ customers, isMutating, onEdit, onDelete }: CustomerTableProps) {
  if (customers.length === 0) {
    return (
      <div className="empty-state">
        <p className="muted">No customers yet. Add your first customer to get started.</p>
      </div>
    )
  }

  return (
    <div className="product-table-wrapper">
      <table className="product-table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Email</th>
            <th scope="col">Phone</th>
            <th scope="col">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={customer.id}>
              <td>
                <span className="product-name">{customer.name}</span>
                {customer.address !== null && (
                  <span className="product-description">{customer.address}</span>
                )}
              </td>
              <td>{customer.email ?? <span className="muted">—</span>}</td>
              <td>{customer.phone ?? <span className="muted">—</span>}</td>
              <td className="product-actions">
                <button
                  type="button"
                  className="table-button"
                  onClick={() => onEdit(customer)}
                  disabled={isMutating}
                  aria-label={`Edit ${customer.name}`}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="table-button table-button--danger"
                  onClick={() => onDelete(customer.id)}
                  disabled={isMutating}
                  aria-label={`Delete ${customer.name}`}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
