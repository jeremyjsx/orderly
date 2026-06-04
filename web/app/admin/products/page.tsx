'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ImageIcon } from 'lucide-react'
import { products } from '../../../lib/api'
import type { Product } from '../../../lib/types'
import { Badge, Button, Card, Empty, Input, Spinner, formatPrice } from '../../../components/ui'

export default function AdminProductsPage() {
  const [items, setItems] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [deleting, setDeleting] = useState<string | null>(null)
  const limit = 20

  const load = () => {
    setLoading(true)
    products.list({ search: search || undefined, offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [search, offset])

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return
    setDeleting(id)
    try {
      await products.remove(id)
      load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Products</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} total</p>
        </div>
        <Link href="/admin/products/new">
          <Button>+ Add product</Button>
        </Link>
      </div>

      <div className="mb-5">
        <Input
          placeholder="Search products..."
          value={search}
          onChange={e => { setSearch(e.target.value); setOffset(0) }}
          className="w-72"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-4">
          <Empty title="No products" description="Create your first product" />
          <Link href="/admin/products/new"><Button>Add product</Button></Link>
        </div>
      ) : (
        <>
          <Card>
            <div className="divide-y divide-zinc-800">
              {items.map(product => (
                <div key={product.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="w-10 h-10 rounded-lg bg-zinc-800 overflow-hidden relative shrink-0">
                    {product.image_url ? (
                      <Image src={product.image_url} alt={product.name} fill className="object-cover" />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <ImageIcon className="w-4 h-4 text-zinc-600" />
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-100 truncate">{product.name}</p>
                    <p className="text-xs text-zinc-500 truncate">{product.description}</p>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <span className="text-sm font-medium text-emerald-400">{formatPrice(product.price)}</span>
                    <span className="text-xs text-zinc-500 w-16 text-right">{product.stock} stock</span>
                    {product.is_active ? (
                      <Badge variant="green">Active</Badge>
                    ) : (
                      <Badge variant="red">Inactive</Badge>
                    )}
                    <div className="flex items-center gap-1">
                      <Link href={`/admin/products/${product.id}`}>
                        <Button variant="ghost" size="sm">Edit</Button>
                      </Link>
                      <Button
                        variant="danger"
                        size="sm"
                        loading={deleting === product.id}
                        onClick={() => handleDelete(product.id, product.name)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
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
