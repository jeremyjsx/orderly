export type Role = 'USER' | 'ADMIN' | 'DRIVER'

export type OrderStatus =
  | 'pending'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'cancelled'

export interface User {
  id: string
  email: string
  role: Role
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Category {
  id: string
  name: string
  description: string | null
  slug: string
  is_active: boolean
  image_url: string | null
}

export interface Product {
  id: string
  name: string
  description: string
  price: number
  stock: number
  category_id: string
  image_url: string | null
  is_active: boolean
}

export interface CartItem {
  id: string
  quantity: number
  product: {
    id: string
    name: string
    price: number
    image_url: string | null
  }
  subtotal: number
}

export interface CartTotals {
  subtotal: number
  total_items: number
  total_quantity: number
  grand_total: number
}

export interface Cart {
  id: string
  user_id: string
  items: CartItem[]
  totals: CartTotals
}

export interface ShippingAddress {
  id: string
  recipient_name: string
  phone: string
  street: string
  city: string
  state: string
  postal_code: string
  country: string
}

export interface OrderItem {
  id: string
  product_id: string
  quantity: number
  price: number
  subtotal: number
  product: Product | null
}

export interface Order {
  id: string
  user_id: string
  status: OrderStatus
  total: number
  items: OrderItem[]
  shipping_address: ShippingAddress | null
  created_at: string
  updated_at: string
  driver_id: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
  offset: number
  limit: number
  has_more: boolean
}

export interface LocationUpdate {
  latitude: number
  longitude: number
  timestamp: string
}
