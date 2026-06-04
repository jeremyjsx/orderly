'use client'

import { useEffect, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { orders } from '../../../lib/api'
import type { Order, OrderStatus } from '../../../lib/types'
import { Button, Card, Empty, OrderStatusBadge, Spinner, formatPrice } from '../../../components/ui'

const ALL_STATUSES: OrderStatus[] = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

export default function AdminOrdersPage() {
  const [items, setItems] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<OrderStatus | ''>('')
  const [offset, setOffset] = useState(0)
  const [updating, setUpdating] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const limit = 20

  const load = () => {
    setLoading(true)
    orders.list({ status: statusFilter || undefined, offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [statusFilter, offset])

  const updateStatus = async (orderId: string, status: OrderStatus) => {
    setUpdating(orderId)
    try {
      const updated = await orders.updateStatus(orderId, status)
      setItems(prev => prev.map(o => o.id === orderId ? updated : o))
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to update')
    } finally {
      setUpdating(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Orders</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} total</p>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <button
          onClick={() => { setStatusFilter(''); setOffset(0) }}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            !statusFilter
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'text-zinc-400 hover:text-zinc-100 border border-zinc-800'
          }`}
        >
          All
        </button>
        {ALL_STATUSES.map(s => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setOffset(0) }}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              statusFilter === s
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'text-zinc-400 hover:text-zinc-100 border border-zinc-800'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <Empty title="No orders found" />
      ) : (
        <>
          <Card>
            <div className="divide-y divide-zinc-800">
              {items.map(order => (
                <div key={order.id}>
                  <div
                    className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-zinc-800/40 transition-colors"
                    onClick={() => setExpandedId(expandedId === order.id ? null : order.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono text-zinc-100">#{order.id.slice(0, 8).toUpperCase()}</p>
                      <p className="text-xs text-zinc-500">
                        {new Date(order.created_at).toLocaleDateString()} · {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <OrderStatusBadge status={order.status} />
                      <span className="text-sm font-medium text-emerald-400 w-20 text-right">{formatPrice(order.total)}</span>
                      <ChevronDown className={`w-4 h-4 text-zinc-500 transition-transform ${expandedId === order.id ? 'rotate-180' : ''}`} />
                    </div>
                  </div>

                  {expandedId === order.id && (
                    <div className="px-4 pb-4 bg-zinc-950/60">
                      <div className="grid sm:grid-cols-2 gap-4 pt-3">
                        <div>
                          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Items</p>
                          {order.items.map(item => (
                            <p key={item.id} className="text-xs text-zinc-400">
                              {item.product?.name ?? 'Product'} × {item.quantity} = {formatPrice(item.subtotal)}
                            </p>
                          ))}
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Shipping</p>
                          {order.shipping_address ? (
                            <div className="text-xs text-zinc-400">
                              <p>{order.shipping_address.recipient_name}</p>
                              <p>{order.shipping_address.street}</p>
                              <p>{order.shipping_address.city}, {order.shipping_address.state}</p>
                            </div>
                          ) : <p className="text-xs text-zinc-500">No address</p>}
                        </div>
                      </div>

                      {order.status !== 'delivered' && order.status !== 'cancelled' && (
                        <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center gap-3">
                          <span className="text-xs text-zinc-500">Move to:</span>
                          {ALL_STATUSES.filter(s => s !== order.status && s !== 'cancelled').map(s => (
                            <button
                              key={s}
                              onClick={() => updateStatus(order.id, s)}
                              disabled={updating === order.id}
                              className="px-2 py-1 rounded text-xs text-zinc-400 border border-zinc-700 hover:border-emerald-500/40 hover:text-emerald-400 transition-colors disabled:opacity-40"
                            >
                              {s}
                            </button>
                          ))}
                          {updating === order.id && <Spinner size="sm" />}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>

          {total > limit && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))}>Previous</Button>
              <span className="text-xs text-zinc-500">{Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}</span>
              <Button variant="secondary" size="sm" disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)}>Next</Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
