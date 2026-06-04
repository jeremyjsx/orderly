'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ImageIcon } from 'lucide-react'
import { cart as cartApi } from '../../../lib/api'
import type { Cart } from '../../../lib/types'
import { useAuth } from '../../../lib/auth-context'
import { Button, Card, Empty, Spinner, formatPrice } from '../../../components/ui'

export default function CartPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [data, setData] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)

  useEffect(() => {
    if (isLoading) return
    if (!user) { router.push('/auth/login'); return }
    cartApi.get().then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [user, isLoading, router])

  const updateQty = async (itemId: string, qty: number) => {
    setUpdating(itemId)
    try {
      if (qty === 0) {
        await cartApi.removeItem(itemId)
      } else {
        await cartApi.updateItem(itemId, qty)
      }
      const updated = await cartApi.get()
      setData(updated)
    } catch { /* */ } finally {
      setUpdating(null)
    }
  }

  const clearCart = async () => {
    if (!confirm('Clear all items from cart?')) return
    await cartApi.clear()
    const updated = await cartApi.get()
    setData(updated)
  }

  if (loading || isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  const items = data?.items ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Cart</h1>
          <p className="text-sm text-zinc-500 mt-1">{items.length} item{items.length !== 1 ? 's' : ''}</p>
        </div>
        {items.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearCart}>Clear cart</Button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-6">
          <Empty title="Your cart is empty" description="Add some products to get started" />
          <Link href="/shop"><Button variant="primary">Browse products</Button></Link>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-3">
            {items.map(item => (
              <Card key={item.id} className="p-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-zinc-800 rounded-lg overflow-hidden relative shrink-0">
                    {item.product.image_url ? (
                      <Image src={item.product.image_url} alt={item.product.name} fill className="object-cover" />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <ImageIcon className="w-6 h-6 text-zinc-700" />
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-100 truncate">{item.product.name}</p>
                    <p className="text-xs text-zinc-500">{formatPrice(item.product.price)} each</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-lg">
                      <button
                        onClick={() => updateQty(item.id, item.quantity - 1)}
                        disabled={updating === item.id}
                        className="w-8 h-8 flex items-center justify-center text-zinc-400 hover:text-zinc-100 disabled:opacity-40 transition-colors"
                      >
                        −
                      </button>
                      <span className="w-6 text-center text-sm font-medium text-zinc-100">
                        {updating === item.id ? '…' : item.quantity}
                      </span>
                      <button
                        onClick={() => updateQty(item.id, item.quantity + 1)}
                        disabled={updating === item.id}
                        className="w-8 h-8 flex items-center justify-center text-zinc-400 hover:text-zinc-100 disabled:opacity-40 transition-colors"
                      >
                        +
                      </button>
                    </div>

                    <span className="text-sm font-semibold text-emerald-400 w-16 text-right">
                      {formatPrice(item.subtotal)}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div>
            <Card className="p-5 sticky top-20">
              <h3 className="text-sm font-semibold text-zinc-100 mb-4">Order summary</h3>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Subtotal ({data?.totals.total_quantity} items)</span>
                  <span className="text-zinc-100">{formatPrice(data?.totals.subtotal ?? 0)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Shipping</span>
                  <span className="text-emerald-400">Free</span>
                </div>
              </div>

              <div className="border-t border-zinc-800 pt-4 mb-5">
                <div className="flex justify-between">
                  <span className="font-semibold text-zinc-100">Total</span>
                  <span className="font-bold text-emerald-400 text-lg">{formatPrice(data?.totals.grand_total ?? 0)}</span>
                </div>
              </div>

              <Button className="w-full" size="lg" onClick={() => router.push('/checkout')}>
                Checkout →
              </Button>

              <Link href="/shop" className="block mt-3">
                <Button variant="ghost" className="w-full" size="sm">Continue shopping</Button>
              </Link>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
