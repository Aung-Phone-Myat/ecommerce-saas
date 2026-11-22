import { useId, useRef, useState } from 'react'
import type { FormEvent } from 'react'

import type { Customer } from '../lib/customers'
import type { OrderCreatePayload } from '../lib/orders'
import type { Product } from '../lib/products'

interface OrderFormProps {
  customers: Customer[]
  products: Product[]
  areOptionsLoading: boolean
  isSubmitting: boolean
  error: string | null
  onSubmit: (payload: OrderCreatePayload) => Promise<boolean> | boolean
  onCancel: () => void
}

interface ItemRow {
  key: number
  productId: string
  quantity: string
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatCurrency(value: number): string {
  return priceFormatter.format(value)
}

function newRow(key: number): ItemRow {
  return { key, productId: '', quantity: '1' }
}

export function OrderForm({
  customers,
  products,
  areOptionsLoading,
  isSubmitting,
  error,
  onSubmit,
  onCancel,
}: OrderFormProps) {
  const fieldId = useId()
  const nextRowKey = useRef(2)
  const [customerId, setCustomerId] = useState('')
  const [rows, setRows] = useState<ItemRow[]>(() => [newRow(1)])
  const [validationError, setValidationError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const productsById = new Map(products.map((product) => [product.id, product]))
  const availableProducts = products.filter((product) => product.stock_quantity > 0)

  function updateRow(key: number, changes: Partial<ItemRow>) {
    setSuccess(false)
    setRows((current) =>
      current.map((row) => (row.key === key ? { ...row, ...changes } : row)),
    )
  }

  function addRow() {
    setSuccess(false)
    setRows((current) => [...current, newRow(nextRowKey.current)])
    nextRowKey.current += 1
  }

  function removeRow(key: number) {
    setSuccess(false)
    setRows((current) => current.filter((row) => row.key !== key))
  }

  function resetForm() {
    setCustomerId('')
    setRows([newRow(1)])
    nextRowKey.current = 2
    setValidationError(null)
    setSuccess(true)
  }

  const estimatedTotal = rows.reduce((sum, row) => {
    const product = productsById.get(Number(row.productId))
    const quantity = Number(row.quantity)
    if (product === undefined || !Number.isInteger(quantity) || quantity <= 0) return sum
    return sum + Number(product.price) * quantity
  }, 0)

  function validate(): string | null {
    if (customerId === '') {
      return 'Select a customer.'
    }
    if (rows.length === 0 || rows.some((row) => row.productId === '')) {
      return 'Select a product for every item row.'
    }
    for (const row of rows) {
      const quantity = Number(row.quantity)
      if (!Number.isInteger(quantity) || quantity <= 0) {
        return 'Each quantity must be a positive whole number.'
      }

      const product = productsById.get(Number(row.productId))
      if (product !== undefined && quantity > product.stock_quantity) {
        return `Only ${product.stock_quantity} units of ${product.name} are in stock.`
      }
    }
    return null
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSuccess(false)

    const problem = validate()
    if (problem !== null) {
      setValidationError(problem)
      return
    }

    setValidationError(null)
    const created = await onSubmit({
      customer_id: Number(customerId),
      items: rows.map((row) => ({
        product_id: Number(row.productId),
        quantity: Number(row.quantity),
      })),
    })

    if (created) {
      resetForm()
    }
  }

  const displayedError = validationError ?? error

  return (
    <form className="product-form" onSubmit={handleSubmit}>
      <div className="product-form__grid">
        <label className="field field--full" htmlFor={`${fieldId}-customer`}>
          <span>Customer</span>
          <select
            id={`${fieldId}-customer`}
            name="customerId"
            value={customerId}
            onChange={(event) => {
              setCustomerId(event.target.value)
              setSuccess(false)
            }}
            disabled={isSubmitting || areOptionsLoading}
            required
          >
            <option value="">{areOptionsLoading ? 'Loading customers…' : 'Select a customer'}</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="order-items">
        <div className="order-items__header">
          <h4>Products</h4>
          <button
            type="button"
            className="table-button"
            onClick={addRow}
            disabled={isSubmitting || availableProducts.length === 0}
          >
            Add Product
          </button>
        </div>

        {areOptionsLoading && <p className="muted">Loading products…</p>}
        {!areOptionsLoading && availableProducts.length === 0 && (
          <p className="muted">No products with stock available. Add a product first.</p>
        )}

        {rows.map((row, index) => {
          const selectedProduct = productsById.get(Number(row.productId))
          return (
            <div className="order-item-row" key={row.key}>
              <label className="field" htmlFor={`${fieldId}-product-${row.key}`}>
                <span>Product {index + 1}</span>
                <select
                  id={`${fieldId}-product-${row.key}`}
                  name={`productId-${row.key}`}
                  value={row.productId}
                  onChange={(event) => updateRow(row.key, { productId: event.target.value })}
                  disabled={isSubmitting || areOptionsLoading}
                  required
                >
                  <option value="">Select a product</option>
                  {availableProducts.map((product) => {
                    const selectedElsewhere = rows.some(
                      (other) => other.key !== row.key && other.productId === String(product.id),
                    )
                    return (
                      <option
                        key={product.id}
                        value={product.id}
                        disabled={selectedElsewhere}
                      >
                        {product.name} · {formatCurrency(Number(product.price))} (
                        {product.stock_quantity} in stock)
                      </option>
                    )
                  })}
                </select>
              </label>

              <label className="field order-item-row__quantity" htmlFor={`${fieldId}-qty-${row.key}`}>
                <span>Quantity</span>
                <input
                  id={`${fieldId}-qty-${row.key}`}
                  name={`quantity-${row.key}`}
                  type="number"
                  min="1"
                  max={selectedProduct?.stock_quantity}
                  step="1"
                  value={row.quantity}
                  onChange={(event) => updateRow(row.key, { quantity: event.target.value })}
                  disabled={isSubmitting}
                  required
                />
              </label>

              <button
                type="button"
                className="table-button table-button--danger order-item-row__remove"
                onClick={() => removeRow(row.key)}
                disabled={isSubmitting || rows.length === 1}
                aria-label={`Remove product ${index + 1}`}
              >
                Remove
              </button>
            </div>
          )
        })}
      </div>

      <div className="order-total">
        <span>Estimated total</span>
        <strong>{formatCurrency(estimatedTotal)}</strong>
      </div>

      {displayedError !== null && (
        <p className="form-error" role="alert">
          {displayedError}
        </p>
      )}
      {success && (
        <p className="form-success" role="status">
          Order created successfully.
        </p>
      )}

      <div className="product-form__actions">
        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating…' : 'Create Order'}
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
