'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Box, ClipboardList, Users, DollarSign } from 'lucide-react'
import { orders, products, users } from '../../lib/api'
import { Card, OrderStatusBadge, Spinner, formatPrice } from '../../components/ui'
import type { Order } from '../../lib/types'

interface Stats {
  totalProducts: number
  totalOrders: number
  totalUsers: number
  revenue: number
}

const statCards = (stats: Stats) => [
  { label: 'Total Products', value: stats.totalProducts, href: '/admin/products', icon: Box, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  { label: 'Total Orders', value: stats.totalOrders, href: '/admin/orders', icon: ClipboardList, color: 'text-sky-400', bg: 'bg-sky-500/10' },
  { label: 'Registered Users', value: stats.totalUsers, href: '/admin/users', icon: Users, color: 'text-violet-400', bg: 'bg-violet-500/10' },
  { label: 'Revenue (recent)', value: formatPrice(stats.revenue), href: '/admin/orders', icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
]

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentOrders, setRecentOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      products.list({ limit: 1 }),
      orders.list({ limit: 5 }),
      users.list({ limit: 1 }),
    ]).then(([p, o, u]) => {
      const revenue = o.items.reduce((sum, ord) => sum + (ord.status !== 'cancelled' ? ord.total : 0), 0)
      setStats({ totalProducts: p.total, totalOrders: o.total, totalUsers: u.total, revenue })
      setRecentOrders(o.items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-1">Platform overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats && statCards(stats).map(({ label, value, href, icon: Icon, color, bg }) => (
          <Link key={label} href={href}>
            <Card className="p-4 hover:border-zinc-700 transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${bg} ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <p className="text-2xl font-bold text-zinc-100 group-hover:text-emerald-400 transition-colors">{value}</p>
              <p className="text-xs text-zinc-500 mt-1">{label}</p>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        {[
          { href: '/admin/products/new', label: 'Add Product', sub: 'Create a new product listing' },
          { href: '/admin/categories/new', label: 'Add Category', sub: 'Organize your catalog' },
          { href: '/admin/orders', label: 'View Orders', sub: 'Process pending orders' },
        ].map(({ href, label, sub }) => (
          <Link key={href} href={href}>
            <Card className="p-4 hover:border-violet-700/40 transition-all group">
              <p className="text-sm font-medium text-zinc-100 group-hover:text-violet-400 transition-colors">{label}</p>
              <p className="text-xs text-zinc-500 mt-1">{sub}</p>
            </Card>
          </Link>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-zinc-100">Recent orders</h2>
          <Link href="/admin/orders" className="text-xs text-emerald-400 hover:text-emerald-300">View all →</Link>
        </div>
        <Card>
          {recentOrders.length === 0 ? (
            <p className="text-sm text-zinc-500 text-center py-8">No orders yet</p>
          ) : (
            <div className="divide-y divide-zinc-800">
              {recentOrders.map(order => (
                <Link key={order.id} href="/admin/orders">
                  <div className="flex items-center justify-between px-4 py-3 hover:bg-zinc-800/50 transition-colors">
                    <div>
                      <p className="text-sm font-mono text-zinc-100">#{order.id.slice(0, 8).toUpperCase()}</p>
                      <p className="text-xs text-zinc-500">{new Date(order.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <OrderStatusBadge status={order.status} />
                      <span className="text-sm font-medium text-emerald-400">{formatPrice(order.total)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
