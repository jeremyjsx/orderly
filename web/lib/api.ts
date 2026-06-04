import type { Cart, CartItem, Category, Order, OrderStatus, Paginated, Product, Token, User } from './types'

const BASE = 'http://localhost:8000/api/v1'

function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null }
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  }
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function refreshTokens(): Promise<string | null> {
  const { refresh } = getTokens()
  if (!refresh) return null
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) { clearTokens(); return null }
    const data: Token = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    clearTokens()
    return null
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const { access } = getTokens()
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  }
  if (!(init.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (access) headers['Authorization'] = `Bearer ${access}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 401 && retry) {
    const newAccess = await refreshTokens()
    if (newAccess) return apiFetch(path, init, false)
    throw new ApiError(401, 'Unauthorized')
  }

  if (res.status === 204) return undefined as T

  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail ?? detail } catch { /* */ }
    throw new ApiError(res.status, detail)
  }

  return res.json()
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

// Auth
export const auth = {
  register: (email: string, password: string) =>
    apiFetch<User>('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),

  login: async (email: string, password: string): Promise<{ user: User; tokens: Token }> => {
    const tokens = await apiFetch<Token>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setTokens(tokens.access_token, tokens.refresh_token)
    const user = await apiFetch<User>('/users/me')
    return { user, tokens }
  },

  logout: async () => {
    const { refresh } = getTokens()
    if (refresh) {
      await apiFetch('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refresh }) }).catch(() => {})
    }
    clearTokens()
  },

  me: () => apiFetch<User>('/users/me'),
}

// Products
export const products = {
  list: (params?: {
    offset?: number; limit?: number; category_id?: string
    active_only?: boolean; search?: string; min_price?: number; max_price?: number
  }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.category_id) q.set('category_id', params.category_id)
    if (params?.active_only) q.set('active_only', 'true')
    if (params?.search) q.set('search', params.search)
    if (params?.min_price !== undefined) q.set('min_price', String(params.min_price))
    if (params?.max_price !== undefined) q.set('max_price', String(params.max_price))
    return apiFetch<Paginated<Product>>(`/products/?${q}`)
  },
  get: (id: string) => apiFetch<Product>(`/products/${id}`),
  create: (body: { name: string; description: string; price: number; stock: number; category_id: string }) =>
    apiFetch<Product>('/products/', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: Partial<{ name: string; description: string; price: number; stock: number; category_id: string; is_active: boolean }>) =>
    apiFetch<Product>(`/products/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  remove: (id: string) => apiFetch<void>(`/products/${id}`, { method: 'DELETE' }),
  uploadImage: (id: string, file: File) => {
    const fd = new FormData(); fd.append('image', file)
    return apiFetch<Product>(`/products/${id}/image`, { method: 'PUT', body: fd })
  },
  deleteImage: (id: string) => apiFetch<Product>(`/products/${id}/image`, { method: 'DELETE' }),
}

// Categories
export const categories = {
  list: (params?: { offset?: number; limit?: number; active_only?: boolean; search?: string }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.active_only) q.set('active_only', 'true')
    if (params?.search) q.set('search', params.search)
    return apiFetch<Paginated<Category>>(`/categories/?${q}`)
  },
  get: (id: string) => apiFetch<Category>(`/categories/${id}`),
  create: (body: { name: string; description?: string; slug: string; is_active?: boolean }) =>
    apiFetch<Category>('/categories/', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: Partial<{ name: string; description: string; slug: string; is_active: boolean }>) =>
    apiFetch<Category>(`/categories/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  remove: (id: string) => apiFetch<void>(`/categories/${id}`, { method: 'DELETE' }),
  uploadImage: (id: string, file: File) => {
    const fd = new FormData(); fd.append('image', file)
    return apiFetch<Category>(`/categories/${id}/image`, { method: 'PUT', body: fd })
  },
}

// Cart
export const cart = {
  get: () => apiFetch<Cart>('/cart/me'),
  addItem: (product_id: string, quantity = 1) =>
    apiFetch<CartItem>('/cart/items', { method: 'POST', body: JSON.stringify({ product_id, quantity }) }),
  updateItem: (item_id: string, quantity: number) =>
    apiFetch<CartItem>(`/cart/items/${item_id}`, { method: 'PUT', body: JSON.stringify({ quantity }) }),
  removeItem: (item_id: string) => apiFetch<void>(`/cart/items/${item_id}`, { method: 'DELETE' }),
  clear: () => apiFetch<void>('/cart/', { method: 'DELETE' }),
}

// Orders
export const orders = {
  create: (shipping_address: {
    recipient_name: string; phone: string; street: string
    city: string; state: string; postal_code: string; country: string
  }) => apiFetch<Order>('/orders/', { method: 'POST', body: JSON.stringify({ shipping_address }) }),
  list: (params?: { offset?: number; limit?: number; status?: OrderStatus }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.status) q.set('status', params.status)
    return apiFetch<Paginated<Order>>(`/orders/?${q}`)
  },
  myOrders: (params?: { offset?: number; limit?: number; status?: OrderStatus }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    if (params?.status) q.set('status', params.status)
    return apiFetch<Paginated<Order>>(`/orders/me?${q}`)
  },
  available: (params?: { offset?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    return apiFetch<Paginated<Order>>(`/orders/available?${q}`)
  },
  myDeliveries: (params?: { offset?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    return apiFetch<Paginated<Order>>(`/orders/my-deliveries?${q}`)
  },
  get: (id: string) => apiFetch<Order>(`/orders/${id}`),
  assign: (id: string) => apiFetch<Order>(`/orders/${id}/assign`, { method: 'PATCH' }),
  deliver: (id: string) => apiFetch<Order>(`/orders/${id}/deliver`, { method: 'PATCH' }),
  cancel: (id: string) => apiFetch<Order>(`/orders/${id}/cancel`, { method: 'PATCH' }),
  updateStatus: (id: string, status: OrderStatus) =>
    apiFetch<Order>(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
}

// Users (admin)
export const users = {
  list: (params?: { offset?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.offset !== undefined) q.set('offset', String(params.offset))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    return apiFetch<Paginated<User>>(`/users/?${q}`)
  },
  get: (id: string) => apiFetch<User>(`/users/${id}`),
  update: (id: string, body: { email: string }) =>
    apiFetch<User>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  remove: (id: string) => apiFetch<void>(`/users/${id}`, { method: 'DELETE' }),
}

export function wsOrderUrl(orderId: string) {
  const { access } = getTokens()
  return `ws://localhost:8000/api/v1/orders/ws/${orderId}?token=${access}`
}
