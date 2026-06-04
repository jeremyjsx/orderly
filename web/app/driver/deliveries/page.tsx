'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { orders } from '../../../lib/api'
import type { Order } from '../../../lib/types'
import { Button, Card, Empty, OrderStatusBadge, Spinner, formatPrice } from '../../../components/ui'

export default function MyDeliveriesPage() {
  const [items, setItems] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const limit = 20

  useEffect(() => {
    setLoading(true)
    orders.myDeliveries({ offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [offset])

  const active = items.filter(o => o.status === 'processing' || o.status === 'shipped')
  const others = items.filter(o => o.status !== 'processing' && o.status !== 'shipped')

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">My Deliveries</h1>
        <p className="text-sm text-zinc-500 mt-1">{total} total</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-4">
          <Empty title="No deliveries yet" description="Accept orders from the Available tab" />
          <Link href="/driver/available"><Button>Browse available orders</Button></Link>
        </div>
      ) : (
        <div className="space-y-6">
          {active.length > 0 && (
            <div>
              <h2 className="text-xs text-zinc-500 uppercase tracking-wider mb-3">In progress</h2>
              <div className="space-y-3">
                {active.map(order => (
                  <Link key={order.id} href={`/driver/delivery/${order.id}`}>
                    <Card className="p-4 border-sky-800/30 hover:border-sky-700/50 transition-all group">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="text-sm font-mono font-medium text-zinc-100 group-hover:text-sky-400 transition-colors">
                            #{order.id.slice(0, 8).toUpperCase()}
                          </p>
                          <p className="text-xs text-zinc-500 mt-0.5">
                            {order.shipping_address?.city}, {order.shipping_address?.state}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
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

          {others.length > 0 && (
            <div>
              <h2 className="text-xs text-zinc-500 uppercase tracking-wider mb-3">History</h2>
              <Card>
                <div className="divide-y divide-zinc-800">
                  {others.map(order => (
                    <div key={order.id} className="flex items-center justify-between px-4 py-3">
                      <div>
                        <p className="text-sm font-mono text-zinc-100">#{order.id.slice(0, 8).toUpperCase()}</p>
                        <p className="text-xs text-zinc-500">{new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <OrderStatusBadge status={order.status} />
                        <span className="text-sm font-medium text-zinc-400">{formatPrice(order.total)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {total > limit && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))}>Previous</Button>
              <span className="text-xs text-zinc-500">{Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}</span>
              <Button variant="secondary" size="sm" disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)}>Next</Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
