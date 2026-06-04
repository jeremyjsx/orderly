'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { categories } from '../../../lib/api'
import type { Category } from '../../../lib/types'
import { Badge, Button, Card, Empty, Spinner } from '../../../components/ui'

export default function AdminCategoriesPage() {
  const [items, setItems] = useState<Category[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    categories.list({ limit: 50 })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete category "${name}"?`)) return
    setDeleting(id)
    try {
      await categories.remove(id)
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
          <h1 className="text-2xl font-bold text-zinc-100">Categories</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} total</p>
        </div>
        <Link href="/admin/categories/new">
          <Button>+ Add category</Button>
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-4">
          <Empty title="No categories" description="Create your first category" />
          <Link href="/admin/categories/new"><Button>Add category</Button></Link>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map(cat => (
            <Card key={cat.id} className="p-4 hover:border-zinc-700 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-zinc-100">{cat.name}</p>
                    {cat.is_active ? <Badge variant="green">Active</Badge> : <Badge variant="red">Inactive</Badge>}
                  </div>
                  <p className="text-xs font-mono text-zinc-500">{cat.slug}</p>
                  {cat.description && <p className="text-xs text-zinc-500 mt-1 truncate">{cat.description}</p>}
                </div>
                {cat.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={cat.image_url} alt={cat.name} className="w-12 h-12 rounded-lg object-cover ml-3 shrink-0" />
                )}
              </div>
              <div className="flex gap-2 mt-4">
                <Link href={`/admin/categories/${cat.id}`} className="flex-1">
                  <Button variant="secondary" size="sm" className="w-full">Edit</Button>
                </Link>
                <Button
                  variant="danger"
                  size="sm"
                  loading={deleting === cat.id}
                  onClick={() => handleDelete(cat.id, cat.name)}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
