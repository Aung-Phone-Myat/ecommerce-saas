import { useState } from 'react'
import type { FormEvent } from 'react'

import { getErrorMessage, registerUser } from '../lib/auth'

interface RegisterPageProps {
  onSuccess: () => void
  onNavigateToLogin: () => void
}

interface RegistrationForm {
  username: string
  email: string
  password: string
  confirmPassword: string
}

const USERNAME_PATTERN = /^[A-Za-z0-9_.-]+$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validateForm(form: RegistrationForm): string | null {
  const username = form.username.trim()
  const email = form.email.trim()

  if (!username || !email || !form.password || !form.confirmPassword) {
    return 'Fill in all fields.'
  }
  if (username.length < 3 || username.length > 50) {
    return 'Username must be between 3 and 50 characters.'
  }
  if (!USERNAME_PATTERN.test(username)) {
    return 'Username may only contain letters, numbers, dots, underscores, and hyphens.'
  }
  if (!EMAIL_PATTERN.test(email)) {
    return 'Enter a valid email address.'
  }
  if (form.password.length < 8 || form.password.length > 128) {
    return 'Password must be between 8 and 128 characters.'
  }
  if (form.password !== form.confirmPassword) {
    return 'Passwords do not match.'
  }
  return null
}

export function RegisterPage({ onSuccess, onNavigateToLogin }: RegisterPageProps) {
  const [form, setForm] = useState<RegistrationForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(field: keyof RegistrationForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const validationError = validateForm(form)
    if (validationError !== null) {
      setError(validationError)
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      await registerUser({
        username: form.username.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
      })
      onSuccess()
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Unable to create account.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-card">
      <p className="eyebrow">Ecommerce SaaS</p>
      <h1>Create your account</h1>
      <p className="subtitle">Sign up to start managing your store and orders.</p>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="field" htmlFor="register-username">
          <span>Username</span>
          <input
            id="register-username"
            name="username"
            type="text"
            autoComplete="username"
            placeholder="jane_doe"
            value={form.username}
            onChange={(event) => updateField('username', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor="register-email">
          <span>Email</span>
          <input
            id="register-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="jane@example.com"
            value={form.email}
            onChange={(event) => updateField('email', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor="register-password">
          <span>Password</span>
          <input
            id="register-password"
            name="password"
            type="password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
            value={form.password}
            onChange={(event) => updateField('password', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor="register-confirm-password">
          <span>Confirm Password</span>
          <input
            id="register-confirm-password"
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            placeholder="Repeat your password"
            value={form.confirmPassword}
            onChange={(event) => updateField('confirmPassword', event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        {error !== null && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Sign up'}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account?{' '}
        <button
          type="button"
          className="auth-link"
          onClick={onNavigateToLogin}
          disabled={isSubmitting}
        >
          Login
        </button>
      </p>
    </section>
  )
}
