'use client'

import { useEffect, useState } from 'react'
import { orders } from '../../../lib/api'
import type { Order } from '../../../lib/types'
import { Button, Card, Empty, Spinner, formatPrice } from '../../../components/ui'

export default function AvailableOrdersPage() {
  const [items, setItems] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [assigning, setAssigning] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 20

  const load = () => {
    setLoading(true)
    orders.available({ offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [offset])

  const assign = async (orderId: string) => {
    setAssigning(orderId)
    try {
      await orders.assign(orderId)
      load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to assign order')
    } finally {
      setAssigning(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Available Orders</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} orders waiting for pickup</p>
        </div>
        <Button variant="secondary" size="sm" onClick={load}>Refresh</Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <Empty title="No orders available" description="Check back soon for new deliveries" />
      ) : (
        <>
          <div className="space-y-3">
            {items.map(order => (
              <Card key={order.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-mono font-medium text-zinc-100">
                        #{order.id.slice(0, 8).toUpperCase()}
                      </p>
                      <span className="text-xs text-zinc-600">·</span>
                      <span className="text-xs text-zinc-500">{new Date(order.created_at).toLocaleDateString()}</span>
                    </div>

                    {order.shipping_address && (
                      <div className="mb-3">
                        <p className="text-xs text-zinc-300">{order.shipping_address.recipient_name}</p>
                        <p className="text-xs text-zinc-500">{order.shipping_address.street}</p>
                        <p className="text-xs text-zinc-500">
                          {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-4">
                      <span className="text-xs text-zinc-500">{order.items.length} item{order.items.length !== 1 ? 's' : ''}</span>
                      <span className="text-sm font-semibold text-sky-400">{formatPrice(order.total)}</span>
                    </div>
                  </div>

                  <Button
                    onClick={() => assign(order.id)}
                    loading={assigning === order.id}
                    size="sm"
                    className="shrink-0"
                  >
                    Accept delivery
                  </Button>
                </div>
              </Card>
            ))}
          </div>

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
