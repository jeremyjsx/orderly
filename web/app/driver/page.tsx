'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ClipboardCheck, MapPin, ChevronRight } from 'lucide-react'
import { orders } from '../../lib/api'
import { Card, OrderStatusBadge, Spinner, formatPrice } from '../../components/ui'
import type { Order } from '../../lib/types'

export default function DriverDashboard() {
  const [available, setAvailable] = useState(0)
  const [myDeliveries, setMyDeliveries] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      orders.available({ limit: 1 }),
      orders.myDeliveries({ limit: 5 }),
    ]).then(([avail, mine]) => {
      setAvailable(avail.total)
      setMyDeliveries(mine.items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  const active = myDeliveries.filter(o => o.status === 'processing' || o.status === 'shipped')
  const completed = myDeliveries.filter(o => o.status === 'delivered')

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">Driver Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-1">Manage your deliveries</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Available orders', value: available, color: 'text-emerald-400' },
          { label: 'Active deliveries', value: active.length, color: 'text-sky-400' },
          { label: 'Completed today', value: completed.length, color: 'text-emerald-400' },
        ].map(({ label, value, color }) => (
          <Card key={label} className="p-4">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-zinc-500 mt-1">{label}</p>
          </Card>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <Link href="/driver/available">
          <Card className="p-5 hover:border-sky-700/40 transition-all group">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center">
                <ClipboardCheck className="w-4 h-4 text-sky-400" />
              </div>
              <span className="text-sm font-medium text-zinc-100 group-hover:text-sky-400 transition-colors">Pick up orders</span>
            </div>
            <p className="text-xs text-zinc-500">{available} orders ready for pickup</p>
          </Card>
        </Link>

        <Link href="/driver/deliveries">
          <Card className="p-5 hover:border-sky-700/40 transition-all group">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-sky-400" />
              </div>
              <span className="text-sm font-medium text-zinc-100 group-hover:text-sky-400 transition-colors">My deliveries</span>
            </div>
            <p className="text-xs text-zinc-500">{myDeliveries.length} total deliveries</p>
          </Card>
        </Link>
      </div>

      {active.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 mb-4">Active deliveries</h2>
          <div className="space-y-3">
            {active.map(order => (
              <Link key={order.id} href={`/driver/delivery/${order.id}`}>
                <Card className="p-4 hover:border-zinc-700 transition-all group">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-mono text-zinc-100 group-hover:text-sky-400 transition-colors">
                        #{order.id.slice(0, 8).toUpperCase()}
                      </p>
                      <p className="text-xs text-zinc-500 mt-0.5">
                        {order.shipping_address?.city}, {order.shipping_address?.state}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <OrderStatusBadge status={order.status} />
                      <span className="text-sm font-medium text-sky-400">{formatPrice(order.total)}</span>
                      <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
