import { useCallback, useEffect, useState } from 'react'

import { DashboardPage } from './components/DashboardPage'
import { LoginPage } from './components/LoginPage'
import { RegisterPage } from './components/RegisterPage'
import { clearStoredToken, getStoredToken } from './lib/auth'
import './App.css'

type View = 'login' | 'register' | 'dashboard'

const VIEW_HASHES: Record<View, string> = {
  login: '#/login',
  register: '#/register',
  dashboard: '#/dashboard',
}

function viewFromHash(hash: string, hasToken: boolean): View {
  if (hash === VIEW_HASHES.register) return 'register'
  if (hash === VIEW_HASHES.dashboard || (hash === '' && hasToken)) return 'dashboard'
  return 'login'
}

function readInitialView(): View {
  return viewFromHash(window.location.hash, getStoredToken() !== null)
}

function App() {
  const [view, setView] = useState<View>(readInitialView)
  const [authNotice, setAuthNotice] = useState<string | null>(null)

  const navigate = useCallback((next: View) => {
    window.location.hash = VIEW_HASHES[next]
    setView(next)
  }, [])

  useEffect(() => {
    const syncViewFromHash = () => {
      const hasToken = getStoredToken() !== null
      const hash = window.location.hash

      if (!hasToken && hash === VIEW_HASHES.dashboard) {
        window.location.hash = VIEW_HASHES.login
        setView('login')
        return
      }

      setView(viewFromHash(hash, hasToken))
    }

    syncViewFromHash()
    window.addEventListener('hashchange', syncViewFromHash)
    return () => window.removeEventListener('hashchange', syncViewFromHash)
  }, [])

  const handleLoginSuccess = useCallback(() => {
    setAuthNotice(null)
    navigate('dashboard')
  }, [navigate])

  const handleSessionEnd = useCallback(() => {
    clearStoredToken()
    setAuthNotice(null)
    navigate('login')
  }, [navigate])

  const handleRegisterSuccess = useCallback(() => {
    setAuthNotice('Account created successfully')
    navigate('login')
  }, [navigate])

  const handleNavigateToRegister = useCallback(() => {
    setAuthNotice(null)
    navigate('register')
  }, [navigate])

  const handleNavigateToLogin = useCallback(() => {
    setAuthNotice(null)
    navigate('login')
  }, [navigate])

  const handleDismissNotice = useCallback(() => {
    setAuthNotice(null)
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            ES
          </span>
          <span>Ecommerce SaaS</span>
        </div>
        {view === 'dashboard' && (
          <button type="button" className="ghost-button" onClick={handleSessionEnd}>
            Log out
          </button>
        )}
      </header>

      <main className="app-main">
        {view === 'login' ? (
          <LoginPage
            onSuccess={handleLoginSuccess}
            onNavigateToRegister={handleNavigateToRegister}
            notice={authNotice}
            onDismissNotice={handleDismissNotice}
          />
        ) : view === 'register' ? (
          <RegisterPage
            onSuccess={handleRegisterSuccess}
            onNavigateToLogin={handleNavigateToLogin}
          />
        ) : (
          <DashboardPage onUnauthorized={handleSessionEnd} />
        )}
      </main>
    </div>
  )
}

export default App
