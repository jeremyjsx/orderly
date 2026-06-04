'use client'

import { useParams, useRouter } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { orders, wsOrderUrl } from '../../../../lib/api'
import type { Order } from '../../../../lib/types'
import { useAuth } from '../../../../lib/auth-context'
import { Button, Card, OrderStatusBadge, Spinner, formatPrice } from '../../../../components/ui'

const DeliveryMap = dynamic(() => import('../../../../components/delivery-map'), { ssr: false })

export default function ActiveDeliveryPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [delivering, setDelivering] = useState(false)
  const [wsStatus, setWsStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const [locationSharing, setLocationSharing] = useState(false)
  const [lastLocation, setLastLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [locationError, setLocationError] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const watchIdRef = useRef<number | null>(null)

  useEffect(() => {
    orders.get(String(params.id))
      .then(setOrder)
      .catch(() => router.push('/driver/deliveries'))
      .finally(() => setLoading(false))
  }, [params.id, router])

  const connectWs = useCallback(() => {
    if (!order) return
    const ws = new WebSocket(wsOrderUrl(order.id))
    wsRef.current = ws
    setWsStatus('connecting')
    ws.onopen = () => setWsStatus('connected')
    ws.onerror = () => setWsStatus('error')
    ws.onclose = () => setWsStatus('idle')
  }, [order])

  const disconnectWs = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setWsStatus('idle')
  }, [])

  const sendLocation = useCallback((lat: number, lng: number) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({
      latitude: lat,
      longitude: lng,
      timestamp: new Date().toISOString(),
    }))
    setLastLocation({ lat, lng })
  }, [])

  const startSharing = () => {
    setLocationError('')
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported by this browser')
      return
    }
    connectWs()
    setLocationSharing(true)

    watchIdRef.current = navigator.geolocation.watchPosition(
      pos => sendLocation(pos.coords.latitude, pos.coords.longitude),
      err => {
        const msg: Record<number, string> = {
          1: 'Permission denied — allow location access in your browser settings and try again.',
          2: 'Position unavailable — enable location services in Windows Settings → Privacy & Security → Location.',
          3: 'Request timed out — check your connection and try again.',
        }
        setLocationError(msg[err.code] ?? `Location error (code ${err.code})`)
        setLocationSharing(false)
        stopSharing()
      },
      { enableHighAccuracy: false, maximumAge: 10000, timeout: 15000 }
    )
  }

  const stopSharing = () => {
    setLocationSharing(false)
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    disconnectWs()
  }

  useEffect(() => {
    return () => {
      stopSharing()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const markDelivered = async () => {
    if (!confirm('Mark this order as delivered?')) return
    setDelivering(true)
    stopSharing()
    try {
      const updated = await orders.deliver(order!.id)
      setOrder(updated)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to mark delivered')
    } finally {
      setDelivering(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!order) return null

  const isActive = order.status === 'processing' || order.status === 'shipped'

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to deliveries
      </button>

      <div className="flex items-start justify-between mb-8 gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-zinc-100">Order #{order.id.slice(0, 8).toUpperCase()}</h1>
            <OrderStatusBadge status={order.status} />
          </div>
          <p className="text-sm text-zinc-500 mt-1">{formatPrice(order.total)}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* GPS control */}
        <div className="space-y-4">
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-zinc-100 mb-4">Location sharing</h2>

            {/* Status indicator */}
            <div className="flex items-center gap-3 mb-5 p-3 bg-zinc-900/60 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                wsStatus === 'connected' ? 'bg-emerald-400 animate-pulse' :
                wsStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' :
                wsStatus === 'error' ? 'bg-red-400' : 'bg-zinc-600'
              }`} />
              <div>
                <p className="text-xs font-mono text-zinc-100">
                  {wsStatus === 'connected' ? 'BROADCASTING' :
                   wsStatus === 'connecting' ? 'CONNECTING...' :
                   wsStatus === 'error' ? 'CONNECTION ERROR' : 'OFFLINE'}
                </p>
                {lastLocation && (
                  <p className="text-[10px] font-mono text-zinc-500 mt-0.5">
                    {lastLocation.lat.toFixed(5)}, {lastLocation.lng.toFixed(5)}
                  </p>
                )}
              </div>
            </div>

            {/* Map */}
            <div className="h-56 rounded-xl border border-zinc-800 overflow-hidden relative mb-4">
              {lastLocation ? (
                <>
                  <DeliveryMap lat={lastLocation.lat} lng={lastLocation.lng} />
                  <div className="absolute top-2 right-2 z-[1000] bg-black/70 backdrop-blur-sm rounded-lg px-2 py-1">
                    <p className="text-[10px] font-mono text-emerald-400">LIVE</p>
                  </div>
                </>
              ) : (
                <div className="h-full bg-zinc-900/60 flex items-center justify-center">
                  <p className="text-xs text-zinc-500">Start sharing to see location</p>
                </div>
              )}
            </div>

            {locationError && (
              <div className="mb-4 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {locationError}
              </div>
            )}

            {isActive && (
              locationSharing ? (
                <Button variant="danger" className="w-full" size="lg" onClick={stopSharing}>
                  Stop sharing location
                </Button>
              ) : (
                <Button className="w-full" size="lg" onClick={startSharing}>
                  Start sharing location
                </Button>
              )
            )}
          </Card>

          {isActive && (
            <Button variant="secondary" className="w-full" size="lg" loading={delivering} onClick={markDelivered}>
              ✓ Mark as delivered
            </Button>
          )}
        </div>

        {/* Order details */}
        <div className="space-y-4">
          {order.shipping_address && (
            <Card className="p-5">
              <h3 className="text-xs text-zinc-500 uppercase tracking-wider font-mono mb-3">Deliver to</h3>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-400/10 flex items-center justify-center mt-0.5 shrink-0">
                  <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-zinc-100">{order.shipping_address.recipient_name}</p>
                  <p className="text-xs text-zinc-400 mt-0.5">{order.shipping_address.phone}</p>
                  <p className="text-xs text-zinc-400 mt-1">{order.shipping_address.street}</p>
                  <p className="text-xs text-zinc-400">
                    {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}
                  </p>
                </div>
              </div>
            </Card>
          )}

          <Card className="p-5">
            <h3 className="text-xs text-zinc-500 uppercase tracking-wider font-mono mb-3">Package contents</h3>
            <div className="space-y-2">
              {order.items.map(item => (
                <div key={item.id} className="flex justify-between text-sm">
                  <span className="text-zinc-400">{item.product?.name ?? 'Item'} ×{item.quantity}</span>
                  <span className="text-zinc-500">{formatPrice(item.subtotal)}</span>
                </div>
              ))}
              <div className="border-t border-zinc-800 pt-2 flex justify-between text-sm">
                <span className="font-medium text-zinc-100">Total value</span>
                <span className="font-semibold text-emerald-400">{formatPrice(order.total)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
