import { useCallback, useEffect, useState } from 'react'

import { getAnalyticsSummary } from '../lib/analytics'
import type { AnalyticsSummary } from '../lib/analytics'
import {
  ApiError,
  clearStoredToken,
  getCurrentUser,
  getErrorMessage,
  getStoredToken,
} from '../lib/auth'
import type { CurrentUser } from '../lib/auth'
import {
  createCustomer,
  deleteCustomer,
  listCustomers,
  updateCustomer,
} from '../lib/customers'
import type { Customer, CustomerPayload } from '../lib/customers'
import { createOrder, getOrders, updateOrderStatus } from '../lib/orders'
import type { Order, OrderCreatePayload } from '../lib/orders'
import { createProduct, deleteProduct, listProducts, updateProduct } from '../lib/products'
import type { Product, ProductPayload } from '../lib/products'
import { CustomerForm } from './CustomerForm'
import { CustomerTable } from './CustomerTable'
import { OrderForm } from './OrderForm'
import { OrderTable } from './OrderTable'
import { ProductForm } from './ProductForm'
import { ProductTable } from './ProductTable'
import { StatCard } from './StatCard'

type ActiveTab = 'products' | 'customers' | 'orders'

interface DashboardPageProps {
  onUnauthorized: () => void
}

function formatMemberSince(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatCurrency(value: string): string {
  const amount = Number(value)
  return Number.isFinite(amount) ? currencyFormatter.format(amount) : value
}

export function DashboardPage({ onUnauthorized }: DashboardPageProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('products')

  const [user, setUser] = useState<CurrentUser | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [isProfileLoading, setIsProfileLoading] = useState(true)
  const [profileRetryCount, setProfileRetryCount] = useState(0)

  const [products, setProducts] = useState<Product[]>([])
  const [productsError, setProductsError] = useState<string | null>(null)
  const [isProductsLoading, setIsProductsLoading] = useState(true)
  const [productsRetryCount, setProductsRetryCount] = useState(0)
  const [showProductForm, setShowProductForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [isProductMutating, setIsProductMutating] = useState(false)
  const [productMutationError, setProductMutationError] = useState<string | null>(null)

  const [customers, setCustomers] = useState<Customer[]>([])
  const [customersError, setCustomersError] = useState<string | null>(null)
  const [isCustomersLoading, setIsCustomersLoading] = useState(true)
  const [customersRetryCount, setCustomersRetryCount] = useState(0)
  const [showCustomerForm, setShowCustomerForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [isCustomerMutating, setIsCustomerMutating] = useState(false)
  const [customerMutationError, setCustomerMutationError] = useState<string | null>(null)

  const [orders, setOrders] = useState<Order[]>([])
  const [ordersError, setOrdersError] = useState<string | null>(null)
  const [isOrdersLoading, setIsOrdersLoading] = useState(true)
  const [ordersRetryCount, setOrdersRetryCount] = useState(0)
  const [showOrderForm, setShowOrderForm] = useState(false)
  const [isOrderMutating, setIsOrderMutating] = useState(false)
  const [orderMutationError, setOrderMutationError] = useState<string | null>(null)

  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(true)
  const [analyticsRetryCount, setAnalyticsRetryCount] = useState(0)

  const handleSessionExpired = useCallback(() => {
    clearStoredToken()
    onUnauthorized()
  }, [onUnauthorized])

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      handleSessionExpired()
      return
    }

    let cancelled = false

    getCurrentUser(token)
      .then((profile) => {
        if (!cancelled) setUser(profile)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          handleSessionExpired()
          return
        }
        setProfileError(getErrorMessage(err, 'Could not load your profile.'))
      })
      .finally(() => {
        if (!cancelled) setIsProfileLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [handleSessionExpired, profileRetryCount])

  useEffect(() => {
    let cancelled = false

    listProducts()
      .then((items) => {
        if (!cancelled) setProducts(items)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          handleSessionExpired()
          return
        }
        setProductsError(getErrorMessage(err, 'Could not load products.'))
      })
      .finally(() => {
        if (!cancelled) setIsProductsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [handleSessionExpired, productsRetryCount])

  useEffect(() => {
    let cancelled = false

    listCustomers()
      .then((items) => {
        if (!cancelled) setCustomers(items)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          handleSessionExpired()
          return
        }
        setCustomersError(getErrorMessage(err, 'Could not load customers.'))
      })
      .finally(() => {
        if (!cancelled) setIsCustomersLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [handleSessionExpired, customersRetryCount])

  useEffect(() => {
    let cancelled = false

    getOrders()
      .then((items) => {
        if (!cancelled) setOrders(items)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          handleSessionExpired()
          return
        }
        setOrdersError(getErrorMessage(err, 'Could not load orders.'))
      })
      .finally(() => {
        if (!cancelled) setIsOrdersLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [handleSessionExpired, ordersRetryCount])

  useEffect(() => {
    let cancelled = false

    getAnalyticsSummary()
      .then((summary) => {
        if (!cancelled) setAnalytics(summary)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          handleSessionExpired()
          return
        }
        setAnalyticsError(getErrorMessage(err, 'Could not load analytics.'))
      })
      .finally(() => {
        if (!cancelled) setIsAnalyticsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [handleSessionExpired, analyticsRetryCount])

  function refreshProducts() {
    setIsProductsLoading(true)
    setProductsError(null)
    setProductsRetryCount((count) => count + 1)
  }

  function refreshCustomers() {
    setIsCustomersLoading(true)
    setCustomersError(null)
    setCustomersRetryCount((count) => count + 1)
  }

  function refreshOrders() {
    setIsOrdersLoading(true)
    setOrdersError(null)
    setOrdersRetryCount((count) => count + 1)
  }

  function refreshAnalytics() {
    setIsAnalyticsLoading(true)
    setAnalyticsError(null)
    setAnalyticsRetryCount((count) => count + 1)
  }

  function handleProfileRetry() {
    setUser(null)
    setIsProfileLoading(true)
    setProfileError(null)
    setProfileRetryCount((count) => count + 1)
  }

  async function runMutation(
    setMutating: (value: boolean) => void,
    setError: (value: string | null) => void,
    action: () => Promise<unknown>,
    onSuccess: () => void,
    fallbackError: string,
  ) {
    setError(null)
    setMutating(true)

    try {
      await action()
      onSuccess()
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired()
        return
      }
      setError(getErrorMessage(err, fallbackError))
    } finally {
      setMutating(false)
    }
  }

  function handleCreateProduct(payload: ProductPayload) {
    return runMutation(
      setIsProductMutating,
      setProductMutationError,
      () => createProduct(payload),
      () => {
        setShowProductForm(false)
        refreshProducts()
        refreshAnalytics()
      },
      'Could not create product.',
    )
  }

  function handleUpdateProduct(id: number, payload: ProductPayload) {
    return runMutation(
      setIsProductMutating,
      setProductMutationError,
      () => updateProduct(id, payload),
      () => {
        setEditingProduct(null)
        refreshProducts()
        refreshAnalytics()
      },
      'Could not update product.',
    )
  }

  function handleDeleteProduct(id: number) {
    return runMutation(
      setIsProductMutating,
      setProductMutationError,
      () => deleteProduct(id),
      () => {
        setProducts((current) => current.filter((product) => product.id !== id))
        refreshAnalytics()
      },
      'Could not delete product.',
    )
  }

  function handleCreateCustomer(payload: CustomerPayload) {
    return runMutation(
      setIsCustomerMutating,
      setCustomerMutationError,
      () => createCustomer(payload),
      () => {
        setShowCustomerForm(false)
        refreshCustomers()
        refreshAnalytics()
      },
      'Could not create customer.',
    )
  }

  function handleUpdateCustomer(id: number, payload: CustomerPayload) {
    return runMutation(
      setIsCustomerMutating,
      setCustomerMutationError,
      () => updateCustomer(id, payload),
      () => {
        setEditingCustomer(null)
        refreshCustomers()
        refreshAnalytics()
      },
      'Could not update customer.',
    )
  }

  function handleDeleteCustomer(id: number) {
    return runMutation(
      setIsCustomerMutating,
      setCustomerMutationError,
      () => deleteCustomer(id),
      () => {
        setCustomers((current) => current.filter((customer) => customer.id !== id))
        refreshAnalytics()
      },
      'Could not delete customer.',
    )
  }

  async function runMutationWithResult(
    setMutating: (value: boolean) => void,
    setError: (value: string | null) => void,
    action: () => Promise<unknown>,
    onSuccess: () => void,
    fallbackError: string,
  ): Promise<boolean> {
    setError(null)
    setMutating(true)

    try {
      await action()
      onSuccess()
      return true
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        handleSessionExpired()
        return false
      }
      setError(getErrorMessage(err, fallbackError))
      return false
    } finally {
      setMutating(false)
    }
  }

  function handleCreateOrder(payload: OrderCreatePayload) {
    return runMutationWithResult(
      setIsOrderMutating,
      setOrderMutationError,
      () => createOrder(payload),
      () => {
        refreshOrders()
        refreshProducts()
        refreshAnalytics()
      },
      'Could not create order.',
    )
  }

  function handleCompleteOrder(order: Order) {
    return runMutation(
      setIsOrderMutating,
      setOrderMutationError,
      () => updateOrderStatus(order.id, 'completed'),
      () => {
        setOrders((current) =>
          current.map((item) => (item.id === order.id ? { ...item, status: 'completed' } : item)),
        )
        refreshAnalytics()
      },
      'Could not update order status.',
    )
  }

  const totalStock = products.reduce((sum, product) => sum + product.stock_quantity, 0)

  return (
    <section className="dashboard">
      <div className="dashboard-heading">
        <p className="eyebrow">Dashboard</p>
        <h1>{user ? `Welcome back, ${user.username}` : 'Welcome back'}</h1>
        <p className="subtitle">Manage your products, customers, and account.</p>
      </div>

      {isProfileLoading && (
        <div className="profile-card" aria-live="polite">
          <p className="muted">Loading your profile…</p>
        </div>
      )}

      {!isProfileLoading && profileError !== null && (
        <div className="profile-card profile-card--error" role="alert">
          <p>{profileError}</p>
          <button type="button" className="secondary-button" onClick={handleProfileRetry}>
            Try again
          </button>
        </div>
      )}

      {!isProfileLoading && profileError === null && user !== null && (
        <div className="profile-card">
          <div className="profile-card__title">
            <h2>Profile</h2>
            <span className="status-pill">Authenticated</span>
          </div>
          <dl className="profile-grid">
            <div>
              <dt>Username</dt>
              <dd>{user.username}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div>
              <dt>User ID</dt>
              <dd>{user.id}</dd>
            </div>
            <div>
              <dt>Member since</dt>
              <dd>{formatMemberSince(user.created_at)}</dd>
            </div>
          </dl>
        </div>
      )}

      <section className="overview-section" aria-labelledby="overview-heading">
        <div className="section-header">
          <div>
            <h2 id="overview-heading">Overview</h2>
            <p className="muted">A snapshot of your store's performance.</p>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={refreshAnalytics}
            disabled={isAnalyticsLoading}
          >
            {isAnalyticsLoading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {isAnalyticsLoading && analytics === null && (
          <div className="profile-card" aria-live="polite">
            <p className="muted">Loading overview…</p>
          </div>
        )}

        {!isAnalyticsLoading && analyticsError !== null && (
          <div className="profile-card profile-card--error" role="alert">
            <p>{analyticsError}</p>
            <button type="button" className="secondary-button" onClick={refreshAnalytics}>
              Try again
            </button>
          </div>
        )}

        {analytics !== null && analyticsError === null && (
          <div className="stats-grid">
            <StatCard
              label="Total Revenue"
              value={formatCurrency(analytics.total_revenue)}
              icon="revenue"
              hint="From completed orders"
              featured
            />
            <StatCard label="Total Orders" value={String(analytics.total_orders)} icon="orders" />
            <StatCard
              label="Total Customers"
              value={String(analytics.total_customers)}
              icon="customers"
            />
            <StatCard label="Total Products" value={String(analytics.total_products)} icon="products" />
            <StatCard
              label="Pending Orders"
              value={String(analytics.pending_orders)}
              icon="pending"
              hint="Awaiting completion"
              warning
            />
          </div>
        )}
      </section>

      <div className="dashboard-tabs" role="tablist" aria-label="Management sections">
        <button
          type="button"
          role="tab"
          id="tab-products"
          aria-controls="panel-products"
          aria-selected={activeTab === 'products'}
          className={`dashboard-tab${activeTab === 'products' ? ' dashboard-tab--active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          Products <span className="tab-count">{products.length}</span>
        </button>
        <button
          type="button"
          role="tab"
          id="tab-customers"
          aria-controls="panel-customers"
          aria-selected={activeTab === 'customers'}
          className={`dashboard-tab${activeTab === 'customers' ? ' dashboard-tab--active' : ''}`}
          onClick={() => setActiveTab('customers')}
        >
          Customers <span className="tab-count">{customers.length}</span>
        </button>
        <button
          type="button"
          role="tab"
          id="tab-orders"
          aria-controls="panel-orders"
          aria-selected={activeTab === 'orders'}
          className={`dashboard-tab${activeTab === 'orders' ? ' dashboard-tab--active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          Orders <span className="tab-count">{orders.length}</span>
        </button>
      </div>

      {activeTab === 'products' && (
        <section
          id="panel-products"
          role="tabpanel"
          aria-labelledby="tab-products"
          className="management-section"
        >
          <div className="section-header">
            <div>
              <h2>Products</h2>
              <p className="muted">
                {products.length} {products.length === 1 ? 'product' : 'products'} · {totalStock}{' '}
                units in stock
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              disabled={isProductMutating}
              onClick={() => {
                setEditingProduct(null)
                setShowProductForm((visible) => !visible)
              }}
            >
              {showProductForm ? 'Close form' : 'Add New Product'}
            </button>
          </div>

          {showProductForm && (
            <div className="product-form-card">
              <h3>Add New Product</h3>
              <ProductForm
                isSubmitting={isProductMutating}
                error={productMutationError}
                submitLabel="Add Product"
                onSubmit={handleCreateProduct}
                onCancel={() => setShowProductForm(false)}
              />
            </div>
          )}

          {editingProduct !== null && (
            <div className="product-form-card">
              <h3>Edit {editingProduct.name}</h3>
              <ProductForm
                key={editingProduct.id}
                initialProduct={editingProduct}
                isSubmitting={isProductMutating}
                error={productMutationError}
                submitLabel="Save Changes"
                onSubmit={(payload) => handleUpdateProduct(editingProduct.id, payload)}
                onCancel={() => setEditingProduct(null)}
              />
            </div>
          )}

          {!showProductForm && editingProduct === null && productMutationError !== null && (
            <p className="form-error" role="alert">
              {productMutationError}
            </p>
          )}

          {isProductsLoading && (
            <div className="profile-card" aria-live="polite">
              <p className="muted">Loading products…</p>
            </div>
          )}

          {!isProductsLoading && productsError !== null && (
            <div className="profile-card profile-card--error" role="alert">
              <p>{productsError}</p>
              <button type="button" className="secondary-button" onClick={refreshProducts}>
                Try again
              </button>
            </div>
          )}

          {!isProductsLoading && productsError === null && (
            <ProductTable
              products={products}
              isMutating={isProductMutating}
              onEdit={(product) => {
                setShowProductForm(false)
                setEditingProduct(product)
              }}
              onDelete={handleDeleteProduct}
            />
          )}
        </section>
      )}

      {activeTab === 'customers' && (
        <section
          id="panel-customers"
          role="tabpanel"
          aria-labelledby="tab-customers"
          className="management-section"
        >
          <div className="section-header">
            <div>
              <h2>Customers</h2>
              <p className="muted">
                {customers.length} {customers.length === 1 ? 'customer' : 'customers'} in your
                address book
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              disabled={isCustomerMutating}
              onClick={() => {
                setEditingCustomer(null)
                setShowCustomerForm((visible) => !visible)
              }}
            >
              {showCustomerForm ? 'Close form' : 'Add New Customer'}
            </button>
          </div>

          {showCustomerForm && (
            <div className="product-form-card">
              <h3>Add New Customer</h3>
              <CustomerForm
                isSubmitting={isCustomerMutating}
                error={customerMutationError}
                submitLabel="Add Customer"
                onSubmit={handleCreateCustomer}
                onCancel={() => setShowCustomerForm(false)}
              />
            </div>
          )}

          {editingCustomer !== null && (
            <div className="product-form-card">
              <h3>Edit {editingCustomer.name}</h3>
              <CustomerForm
                key={editingCustomer.id}
                initialCustomer={editingCustomer}
                isSubmitting={isCustomerMutating}
                error={customerMutationError}
                submitLabel="Save Changes"
                onSubmit={(payload) => handleUpdateCustomer(editingCustomer.id, payload)}
                onCancel={() => setEditingCustomer(null)}
              />
            </div>
          )}

          {!showCustomerForm && editingCustomer === null && customerMutationError !== null && (
            <p className="form-error" role="alert">
              {customerMutationError}
            </p>
          )}

          {isCustomersLoading && (
            <div className="profile-card" aria-live="polite">
              <p className="muted">Loading customers…</p>
            </div>
          )}

          {!isCustomersLoading && customersError !== null && (
            <div className="profile-card profile-card--error" role="alert">
              <p>{customersError}</p>
              <button type="button" className="secondary-button" onClick={refreshCustomers}>
                Try again
              </button>
            </div>
          )}

          {!isCustomersLoading && customersError === null && (
            <CustomerTable
              customers={customers}
              isMutating={isCustomerMutating}
              onEdit={(customer) => {
                setShowCustomerForm(false)
                setEditingCustomer(customer)
              }}
              onDelete={handleDeleteCustomer}
            />
          )}
        </section>
      )}

      {activeTab === 'orders' && (
        <section
          id="panel-orders"
          role="tabpanel"
          aria-labelledby="tab-orders"
          className="management-section"
        >
          <div className="section-header">
            <div>
              <h2>Orders</h2>
              <p className="muted">
                {orders.length} {orders.length === 1 ? 'order' : 'orders'} placed by your customers
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              disabled={isOrderMutating}
              onClick={() => {
                setOrderMutationError(null)
                setShowOrderForm((visible) => !visible)
              }}
            >
              {showOrderForm ? 'Close form' : 'Create Order'}
            </button>
          </div>

          {showOrderForm && (
            <div className="product-form-card">
              <h3>Create Order</h3>
              <OrderForm
                customers={customers}
                products={products}
                areOptionsLoading={isCustomersLoading || isProductsLoading}
                isSubmitting={isOrderMutating}
                error={orderMutationError}
                onSubmit={handleCreateOrder}
                onCancel={() => setShowOrderForm(false)}
              />
            </div>
          )}

          {!showOrderForm && orderMutationError !== null && (
            <p className="form-error" role="alert">
              {orderMutationError}
            </p>
          )}

          {isOrdersLoading && (
            <div className="profile-card" aria-live="polite">
              <p className="muted">Loading orders…</p>
            </div>
          )}

          {!isOrdersLoading && ordersError !== null && (
            <div className="profile-card profile-card--error" role="alert">
              <p>{ordersError}</p>
              <button type="button" className="secondary-button" onClick={refreshOrders}>
                Try again
              </button>
            </div>
          )}

          {!isOrdersLoading && ordersError === null && (
            <OrderTable
              orders={orders}
              isMutating={isOrderMutating}
              onComplete={handleCompleteOrder}
            />
          )}
        </section>
      )}
    </section>
  )
}
