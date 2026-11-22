import { useState } from 'react'
import type { FormEvent } from 'react'

import { ApiError, getErrorMessage, login, setStoredToken } from '../lib/auth'

interface LoginPageProps {
  onSuccess: () => void
  onNavigateToRegister: () => void
  notice: string | null
  onDismissNotice: () => void
}

export function LoginPage({
  onSuccess,
  onNavigateToRegister,
  notice,
  onDismissNotice,
}: LoginPageProps) {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedIdentifier = identifier.trim()

    if (!normalizedIdentifier || !password) {
      setError('Enter your email or username and password.')
      return
    }

    onDismissNotice()
    setError(null)
    setIsSubmitting(true)

    try {
      const token = await login(normalizedIdentifier, password)
      setStoredToken(token)
      onSuccess()
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Invalid email or password')
      } else {
        setError(getErrorMessage(err))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-card">
      <p className="eyebrow">Ecommerce SaaS</p>
      <h1>Welcome back</h1>
      <p className="subtitle">Sign in to manage your store and orders.</p>

      {notice !== null && (
        <p className="form-success" role="status">
          {notice}
        </p>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="field" htmlFor="identifier">
          <span>Email or Username</span>
          <input
            id="identifier"
            name="identifier"
            type="text"
            autoComplete="username"
            placeholder="you@example.com or username"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field" htmlFor="password">
          <span>Password</span>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
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
          {isSubmitting ? 'Signing in…' : 'Login'}
        </button>
      </form>

      <p className="auth-switch">
        Don&apos;t have an account?{' '}
        <button
          type="button"
          className="auth-link"
          onClick={onNavigateToRegister}
          disabled={isSubmitting}
        >
          Sign up
        </button>
      </p>
    </section>
  )
}
