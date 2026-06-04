'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ClipboardList, ChevronRight } from 'lucide-react'
import { orders } from '../../../lib/api'
import type { Order } from '../../../lib/types'
import { useAuth } from '../../../lib/auth-context'
import { Button, Card, Empty, OrderStatusBadge, Spinner, formatPrice } from '../../../components/ui'

export default function OrdersPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [items, setItems] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const limit = 10

  useEffect(() => {
    if (isLoading) return
    if (!user) { router.push('/auth/login'); return }
    orders.myOrders({ offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user, isLoading, router, offset])

  if (loading || isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">My Orders</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} total orders</p>
        </div>
        <Link href="/shop"><Button variant="secondary">Continue shopping</Button></Link>
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-6">
          <Empty title="No orders yet" description="Place your first order to see it here" />
          <Link href="/shop"><Button>Shop now</Button></Link>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(order => (
            <Link key={order.id} href={`/orders/${order.id}`}>
              <Card className="p-4 hover:border-zinc-700 transition-all cursor-pointer group">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center shrink-0">
                      <ClipboardList className="w-5 h-5 text-zinc-500" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-zinc-100 group-hover:text-emerald-400 transition-colors">
                        Order #{order.id.slice(0, 8).toUpperCase()}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {new Date(order.created_at).toLocaleDateString()} · {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <OrderStatusBadge status={order.status} />
                    <span className="text-sm font-semibold text-emerald-400">{formatPrice(order.total)}</span>
                    <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                  </div>
                </div>
              </Card>
            </Link>
          ))}

          {total > limit && (
            <div className="flex items-center justify-center gap-3 mt-6">
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
