'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { ChevronLeft } from 'lucide-react'
import { orders, wsOrderUrl } from '../../../../lib/api'
import type { LocationUpdate, Order } from '../../../../lib/types'
import { useAuth } from '../../../../lib/auth-context'
import { Button, Card, OrderStatusBadge, Spinner, formatPrice } from '../../../../components/ui'

const DeliveryMap = dynamic(() => import('../../../../components/delivery-map'), { ssr: false })

interface WsMessage {
  type: string
  [key: string]: unknown
}

export default function OrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { user, isLoading } = useAuth()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [driverLocation, setDriverLocation] = useState<LocationUpdate | null>(null)
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const [events, setEvents] = useState<string[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const [cancelling, setCancelling] = useState(false)

  const addEvent = (msg: string) => setEvents(e => [msg, ...e].slice(0, 10))

  useEffect(() => {
    if (isLoading) return
    if (!user) { router.push('/auth/login'); return }
    orders.get(String(params.id))
      .then(setOrder)
      .catch(() => router.push('/orders'))
      .finally(() => setLoading(false))
  }, [params.id, user, isLoading, router])

  useEffect(() => {
    if (!order || !user) return
    if (!['processing', 'shipped'].includes(order.status)) return

    const ws = new WebSocket(wsOrderUrl(order.id))
    wsRef.current = ws
    setWsStatus('connecting')

    ws.onopen = () => { setWsStatus('connected'); addEvent('Connected to live tracking') }
    ws.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data)
        switch (msg.type) {
          case 'location_update':
            setDriverLocation({ latitude: msg.latitude as number, longitude: msg.longitude as number, timestamp: msg.timestamp as string })
            addEvent('Driver location updated')
            break
          case 'order_status_updated':
            addEvent(`Status → ${msg.status}`)
            setOrder(o => o ? { ...o, status: msg.status as Order['status'] } : o)
            break
          case 'driver_assigned':
            addEvent('Driver assigned to your order')
            setOrder(o => o ? { ...o, driver_id: msg.driver_id as string } : o)
            break
          case 'order_delivered':
            addEvent('Order delivered!')
            setOrder(o => o ? { ...o, status: 'delivered' } : o)
            break
          case 'order_cancelled':
            addEvent('Order cancelled')
            setOrder(o => o ? { ...o, status: 'cancelled' } : o)
            break
        }
      } catch { /* */ }
    }
    ws.onclose = () => { setWsStatus('disconnected'); addEvent('Disconnected from tracking') }
    ws.onerror = () => setWsStatus('disconnected')

    return () => { ws.close() }
  }, [order?.id, order?.status, user])

  const cancelOrder = async () => {
    if (!confirm('Cancel this order?')) return
    setCancelling(true)
    try {
      const updated = await orders.cancel(order!.id)
      setOrder(updated)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Cannot cancel order')
    } finally {
      setCancelling(false)
    }
  }

  if (loading || isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!order) return null

  const steps = ['pending', 'processing', 'shipped', 'delivered'] as const
  const stepIdx = steps.indexOf(order.status as typeof steps[number])

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <ChevronLeft className="w-4 h-4" />
        Back to orders
      </button>

      <div className="flex items-start justify-between mb-8 gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-zinc-100">Order #{order.id.slice(0, 8).toUpperCase()}</h1>
            <OrderStatusBadge status={order.status} />
          </div>
          <p className="text-sm text-zinc-500 mt-1">{new Date(order.created_at).toLocaleString()}</p>
        </div>
        {order.status === 'pending' && (
          <Button variant="danger" size="sm" onClick={cancelOrder} loading={cancelling}>
            Cancel order
          </Button>
        )}
      </div>

      {/* Progress */}
      {order.status !== 'cancelled' && (
        <Card className="p-5 mb-6">
          <div className="flex items-center">
            {steps.map((step, i) => (
              <div key={step} className="flex items-center flex-1 last:flex-none">
                <div className="flex flex-col items-center gap-1">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    i <= stepIdx ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-500 border border-zinc-700'
                  }`}>
                    {i < stepIdx ? '✓' : i + 1}
                  </div>
                  <span className={`text-[10px] whitespace-nowrap capitalize ${i <= stepIdx ? 'text-emerald-400' : 'text-zinc-600'}`}>
                    {step}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`h-0.5 flex-1 mx-2 mb-4 transition-all ${i < stepIdx ? 'bg-emerald-600' : 'bg-zinc-800'}`} />
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">

          {/* Live tracking */}
          {(order.status === 'processing' || order.status === 'shipped') && (
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-zinc-100">Live tracking</h2>
                <div className="flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    wsStatus === 'connected' ? 'bg-emerald-400 animate-pulse' :
                    wsStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-zinc-600'
                  }`} />
                  <span className="text-xs font-mono text-zinc-500">{wsStatus.toUpperCase()}</span>
                </div>
              </div>

              <div className="h-56 rounded-xl border border-zinc-800 overflow-hidden relative">
                {driverLocation ? (
                  <>
                    <DeliveryMap lat={driverLocation.latitude} lng={driverLocation.longitude} />
                    <div className="absolute top-2 right-2 z-[1000] bg-black/70 backdrop-blur-sm rounded-lg px-2 py-1">
                      <p className="text-[10px] font-mono text-emerald-400">LIVE</p>
                    </div>
                  </>
                ) : (
                  <div className="h-full bg-zinc-900/60 flex flex-col items-center justify-center gap-2">
                    <div className="w-8 h-8 rounded-full border border-zinc-700 flex items-center justify-center">
                      <svg className="w-4 h-4 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <p className="text-xs text-zinc-500">Waiting for driver location…</p>
                  </div>
                )}
              </div>

              {events.length > 0 && (
                <div className="mt-3 space-y-1">
                  {events.slice(0, 3).map((e, i) => (
                    <p key={i} className={`text-xs font-mono ${i === 0 ? 'text-emerald-400' : 'text-zinc-600'}`}>
                      › {e}
                    </p>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* Items */}
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-zinc-100 mb-4">Items</h2>
            <div className="space-y-3">
              {order.items.map(item => (
                <div key={item.id} className="flex justify-between items-center text-sm">
                  <div>
                    <p className="text-zinc-100">{item.product?.name ?? 'Product'}</p>
                    <p className="text-xs text-zinc-500">{formatPrice(item.price)} × {item.quantity}</p>
                  </div>
                  <span className="text-emerald-400 font-medium">{formatPrice(item.subtotal)}</span>
                </div>
              ))}
              <div className="border-t border-zinc-800 pt-3 flex justify-between">
                <span className="font-semibold text-zinc-100">Total</span>
                <span className="font-bold text-emerald-400">{formatPrice(order.total)}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {order.shipping_address && (
            <Card className="p-4">
              <h3 className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Shipping to</h3>
              <p className="text-sm text-zinc-100 font-medium">{order.shipping_address.recipient_name}</p>
              <p className="text-xs text-zinc-400 mt-1">{order.shipping_address.phone}</p>
              <p className="text-xs text-zinc-400 mt-0.5">{order.shipping_address.street}</p>
              <p className="text-xs text-zinc-400">{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
              <p className="text-xs text-zinc-400">{order.shipping_address.country}</p>
            </Card>
          )}

          <Card className="p-4">
            <h3 className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Order details</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Order ID</span>
                <span className="font-mono text-zinc-400">{order.id.slice(0, 8)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Placed</span>
                <span className="text-zinc-400">{new Date(order.created_at).toLocaleDateString()}</span>
              </div>
              {order.driver_id && (
                <div className="flex justify-between">
                  <span className="text-zinc-500">Driver</span>
                  <span className="font-mono text-zinc-400">{order.driver_id.slice(0, 8)}</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
