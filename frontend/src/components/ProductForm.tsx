import { useId, useState } from 'react'
import type { FormEvent } from 'react'

import type { Product, ProductPayload } from '../lib/products'

interface ProductFormProps {
  initialProduct?: Product | null
  isSubmitting: boolean
  error: string | null
  submitLabel: string
  onSubmit: (payload: ProductPayload) => Promise<void> | void
  onCancel?: () => void
}

interface FormValues {
  name: string
  description: string
  price: string
  stockQuantity: string
}

const PRICE_PATTERN = /^\d+(\.\d{1,2})?$/

function valuesFromProduct(product: Product | null | undefined): FormValues {
  return {
    name: product?.name ?? '',
    description: product?.description ?? '',
    price: product?.price ?? '',
    stockQuantity: product ? String(product.stock_quantity) : '0',
  }
}

function validate(values: FormValues): string | null {
  if (!values.name.trim()) {
    return 'Enter a product name.'
  }
  if (!PRICE_PATTERN.test(values.price.trim())) {
    return 'Price must be a non-negative number with up to 2 decimal places.'
  }

  const stock = Number(values.stockQuantity)
  if (!Number.isInteger(stock) || stock < 0) {
    return 'Stock quantity must be a non-negative whole number.'
  }
  return null
}

export function ProductForm({
  initialProduct,
  isSubmitting,
  error,
  submitLabel,
  onSubmit,
  onCancel,
}: ProductFormProps) {
  const fieldId = useId()
  const [values, setValues] = useState<FormValues>(() => valuesFromProduct(initialProduct))
  const [validationError, setValidationError] = useState<string | null>(null)

  function updateField(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const problem = validate(values)
    if (problem !== null) {
      setValidationError(problem)
      return
    }

    setValidationError(null)
    await onSubmit({
      name: values.name.trim(),
      description: values.description.trim() || null,
      price: values.price.trim(),
      stock_quantity: Number(values.stockQuantity),
    })
  }

  const displayedError = validationError ?? error

  return (
    <form className="product-form" onSubmit={handleSubmit}>
      <div className="product-form__grid">
        <label className="field" htmlFor={`${fieldId}-name`}>
          <span>Name</span>
          <input
            id={`${fieldId}-name`}
            name="name"
            type="text"
            placeholder="Wireless Mouse"
            value={values.name}
            onChange={(event) => updateField('name', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor={`${fieldId}-price`}>
          <span>Price</span>
          <input
            id={`${fieldId}-price`}
            name="price"
            type="text"
            inputMode="decimal"
            placeholder="19.99"
            value={values.price}
            onChange={(event) => updateField('price', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field field--full" htmlFor={`${fieldId}-description`}>
          <span>Description</span>
          <textarea
            id={`${fieldId}-description`}
            name="description"
            rows={3}
            placeholder="Optional product details"
            value={values.description}
            onChange={(event) => updateField('description', event.target.value)}
            disabled={isSubmitting}
          />
        </label>

        <label className="field" htmlFor={`${fieldId}-stock`}>
          <span>Stock Quantity</span>
          <input
            id={`${fieldId}-stock`}
            name="stockQuantity"
            type="number"
            min="0"
            step="1"
            value={values.stockQuantity}
            onChange={(event) => updateField('stockQuantity', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>
      </div>

      {displayedError !== null && (
        <p className="form-error" role="alert">
          {displayedError}
        </p>
      )}

      <div className="product-form__actions">
        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            className="secondary-button"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
