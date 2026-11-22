import { useId, useState } from 'react'
import type { FormEvent } from 'react'

import type { Customer, CustomerPayload } from '../lib/customers'

interface CustomerFormProps {
  initialCustomer?: Customer | null
  isSubmitting: boolean
  error: string | null
  submitLabel: string
  onSubmit: (payload: CustomerPayload) => Promise<void> | void
  onCancel?: () => void
}

interface FormValues {
  name: string
  email: string
  phone: string
  address: string
}

function valuesFromCustomer(customer: Customer | null | undefined): FormValues {
  return {
    name: customer?.name ?? '',
    email: customer?.email ?? '',
    phone: customer?.phone ?? '',
    address: customer?.address ?? '',
  }
}

export function CustomerForm({
  initialCustomer,
  isSubmitting,
  error,
  submitLabel,
  onSubmit,
  onCancel,
}: CustomerFormProps) {
  const fieldId = useId()
  const [values, setValues] = useState<FormValues>(() => valuesFromCustomer(initialCustomer))
  const [validationError, setValidationError] = useState<string | null>(null)

  function updateField(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!values.name.trim()) {
      setValidationError('Enter a customer name.')
      return
    }

    setValidationError(null)
    await onSubmit({
      name: values.name.trim(),
      email: values.email.trim() || null,
      phone: values.phone.trim() || null,
      address: values.address.trim() || null,
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
            placeholder="Acme Corp"
            maxLength={255}
            value={values.name}
            onChange={(event) => updateField('name', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor={`${fieldId}-email`}>
          <span>Email</span>
          <input
            id={`${fieldId}-email`}
            name="email"
            type="text"
            inputMode="email"
            placeholder="billing@acme.com"
            maxLength={255}
            value={values.email}
            onChange={(event) => updateField('email', event.target.value)}
            disabled={isSubmitting}
          />
        </label>

        <label className="field" htmlFor={`${fieldId}-phone`}>
          <span>Phone</span>
          <input
            id={`${fieldId}-phone`}
            name="phone"
            type="tel"
            placeholder="+1-555-0100"
            maxLength={50}
            value={values.phone}
            onChange={(event) => updateField('phone', event.target.value)}
            disabled={isSubmitting}
          />
        </label>

        <label className="field field--full" htmlFor={`${fieldId}-address`}>
          <span>Address</span>
          <textarea
            id={`${fieldId}-address`}
            name="address"
            rows={3}
            placeholder="Optional mailing address"
            maxLength={2000}
            value={values.address}
            onChange={(event) => updateField('address', event.target.value)}
            disabled={isSubmitting}
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
