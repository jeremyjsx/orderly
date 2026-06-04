'use client'

import Image from 'next/image'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { cart, products } from '../../../../lib/api'
import type { Product } from '../../../../lib/types'
import { useAuth } from '../../../../lib/auth-context'
import { Badge, Button, Card, Spinner, formatPrice } from '../../../../components/ui'

export default function ProductPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)

  useEffect(() => {
    products.get(String(params.id))
      .then(setProduct)
      .catch(() => router.push('/shop'))
      .finally(() => setLoading(false))
  }, [params.id, router])

  const addToCart = async () => {
    if (!user) { router.push('/auth/login'); return }
    setAdding(true)
    try {
      await cart.addItem(product!.id, qty)
      setAdded(true)
      setTimeout(() => setAdded(false), 2000)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to add to cart')
    } finally {
      setAdding(false)
    }
  }

  if (loading) return (
    <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  )
  if (!product) return null

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to shop
      </button>

      <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
        {/* Image */}
        <div className="aspect-square bg-zinc-800 rounded-2xl overflow-hidden relative border border-zinc-800">
          {product.image_url ? (
            <Image src={product.image_url} alt={product.name} fill className="object-cover" />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-20 h-20 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex flex-col">
          <div className="flex items-start justify-between gap-4 mb-4">
            <h1 className="text-2xl font-bold text-zinc-100">{product.name}</h1>
            {!product.is_active && <Badge variant="red">Inactive</Badge>}
          </div>

          <p className="text-3xl font-bold text-emerald-400 mb-6">{formatPrice(product.price)}</p>

          <p className="text-zinc-400 text-sm leading-relaxed mb-6">{product.description}</p>

          <Card className="p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">In stock</span>
              <span className={`text-sm font-medium ${product.stock > 5 ? 'text-emerald-400' : product.stock > 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                {product.stock > 0 ? `${product.stock} units` : 'Out of stock'}
              </span>
            </div>
          </Card>

          {product.stock > 0 && product.is_active && (
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-lg">
                <button
                  onClick={() => setQty(q => Math.max(1, q - 1))}
                  className="w-9 h-9 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition-colors"
                >
                  −
                </button>
                <span className="w-8 text-center text-sm font-medium text-zinc-100">{qty}</span>
                <button
                  onClick={() => setQty(q => Math.min(product.stock, q + 1))}
                  className="w-9 h-9 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition-colors"
                >
                  +
                </button>
              </div>

              <Button
                onClick={addToCart}
                loading={adding}
                className="flex-1"
                size="lg"
              >
                {added ? '✓ Added to cart' : 'Add to cart'}
              </Button>
            </div>
          )}

          <Button variant="secondary" size="lg" onClick={() => router.push('/cart')}>
            View cart
          </Button>
        </div>
      </div>
    </div>
  )
}
