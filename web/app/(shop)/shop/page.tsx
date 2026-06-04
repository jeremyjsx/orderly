'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ImageIcon } from 'lucide-react'
import { categories, products } from '../../../lib/api'
import type { Category, Product } from '../../../lib/types'
import { Badge, Button, Empty, Input, Spinner, formatPrice } from '../../../components/ui'

export default function ShopPage() {
  const [items, setItems] = useState<Product[]>([])
  const [cats, setCats] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const limit = 12

  useEffect(() => {
    categories.list({ active_only: true, limit: 50 })
      .then(r => setCats(r.items))
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    products.list({ active_only: true, search: search || undefined, category_id: categoryId || undefined, offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [search, categoryId, offset])

  const handleSearch = (v: string) => { setSearch(v); setOffset(0) }
  const handleCategory = (id: string) => { setCategoryId(id); setOffset(0) }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Products</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} items available</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-8">
        <Input
          placeholder="Search products..."
          value={search}
          onChange={e => handleSearch(e.target.value)}
          className="w-64"
        />
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => handleCategory('')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              !categoryId
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'text-zinc-400 hover:text-zinc-100 border border-zinc-800 hover:border-zinc-700'
            }`}
          >
            All
          </button>
          {cats.map(c => (
            <button
              key={c.id}
              onClick={() => handleCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                categoryId === c.id
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 border border-zinc-800 hover:border-zinc-700'
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <Empty title="No products found" description="Try adjusting your filters" />
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.map(product => (
              <Link key={product.id} href={`/shop/${product.id}`}>
                <div className="group bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-zinc-700 transition-all duration-200">
                  <div className="aspect-square bg-zinc-800 relative overflow-hidden">
                    {product.image_url ? (
                      <Image src={product.image_url} alt={product.name} fill className="object-cover group-hover:scale-105 transition-transform duration-300" />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <ImageIcon className="w-8 h-8 text-zinc-700" />
                      </div>
                    )}
                    {product.stock <= 5 && product.stock > 0 && (
                      <div className="absolute top-2 left-2">
                        <Badge variant="yellow">Low stock</Badge>
                      </div>
                    )}
                    {product.stock === 0 && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                        <Badge variant="red">Out of stock</Badge>
                      </div>
                    )}
                  </div>

                  <div className="p-3">
                    <p className="text-sm font-medium text-zinc-100 truncate group-hover:text-emerald-400 transition-colors">
                      {product.name}
                    </p>
                    <p className="text-sm font-semibold text-emerald-400 mt-1">{formatPrice(product.price)}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">{product.stock} in stock</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {total > limit && (
            <div className="flex items-center justify-center gap-3 mt-8">
              <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))}>
                Previous
              </Button>
              <span className="text-xs text-zinc-500">
                {Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}
              </span>
              <Button variant="secondary" size="sm" disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
