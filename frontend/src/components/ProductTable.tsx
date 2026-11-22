import type { Product } from '../lib/products'

interface ProductTableProps {
  products: Product[]
  isMutating: boolean
  onEdit: (product: Product) => void
  onDelete: (productId: number) => void
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatPrice(value: string): string {
  const amount = Number(value)
  return Number.isFinite(amount) ? priceFormatter.format(amount) : value
}

export function ProductTable({ products, isMutating, onEdit, onDelete }: ProductTableProps) {
  if (products.length === 0) {
    return (
      <div className="empty-state">
        <p className="muted">No products yet. Add your first product to get started.</p>
      </div>
    )
  }

  return (
    <div className="product-table-wrapper">
      <table className="product-table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Price</th>
            <th scope="col">Stock Quantity</th>
            <th scope="col">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td>
                <span className="product-name">{product.name}</span>
                {product.description !== null && (
                  <span className="product-description">{product.description}</span>
                )}
              </td>
              <td className="product-price">{formatPrice(product.price)}</td>
              <td>
                <span
                  className={`product-stock${
                    product.stock_quantity === 0 ? ' product-stock--empty' : ''
                  }`}
                >
                  {product.stock_quantity}
                </span>
              </td>
              <td className="product-actions">
                <button
                  type="button"
                  className="table-button"
                  onClick={() => onEdit(product)}
                  disabled={isMutating}
                  aria-label={`Edit ${product.name}`}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="table-button table-button--danger"
                  onClick={() => onDelete(product.id)}
                  disabled={isMutating}
                  aria-label={`Delete ${product.name}`}
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
