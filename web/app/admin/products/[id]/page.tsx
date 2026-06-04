'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { categories, products } from '../../../../lib/api'
import type { Category, Product } from '../../../../lib/types'
import { Button, Card, Input, Select, Spinner, Textarea } from '../../../../components/ui'

export default function EditProductPage() {
  const params = useParams()
  const router = useRouter()
  const [product, setProduct] = useState<Product | null>(null)
  const [cats, setCats] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  const [form, setForm] = useState({
    name: '', description: '', price: '', stock: '', category_id: '', is_active: true,
  })

  useEffect(() => {
    Promise.all([
      products.get(String(params.id)),
      categories.list({ limit: 100 }),
    ]).then(([p, c]) => {
      setProduct(p)
      setCats(c.items)
      setForm({
        name: p.name,
        description: p.description,
        price: String(p.price),
        stock: String(p.stock),
        category_id: p.category_id,
        is_active: p.is_active,
      })
    }).catch(() => router.push('/admin/products'))
      .finally(() => setLoading(false))
  }, [params.id, router])

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value
    setForm(f => ({ ...f, [field]: value }))
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await products.update(product!.id, {
        name: form.name,
        description: form.description,
        price: parseFloat(form.price),
        stock: parseInt(form.stock),
        category_id: form.category_id,
        is_active: form.is_active,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !product) return
    setUploadingImage(true)
    try {
      const updated = await products.uploadImage(product.id, file)
      setProduct(updated)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Image upload failed')
    } finally {
      setUploadingImage(false)
    }
  }

  const removeImage = async () => {
    if (!product?.image_url || !confirm('Remove product image?')) return
    setUploadingImage(true)
    try {
      const updated = await products.deleteImage(product.id)
      setProduct(updated)
    } catch { /* */ } finally {
      setUploadingImage(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!product) return null

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to products
      </button>

      <h1 className="text-2xl font-bold text-zinc-100 mb-8">Edit product</h1>

      <form onSubmit={submit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 space-y-4">
              <Input label="Name" value={form.name} onChange={set('name')} required />
              <Textarea label="Description" value={form.description} onChange={set('description')} required rows={3} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Price ($)" type="number" step="0.01" min="0.01" value={form.price} onChange={set('price')} required />
                <Input label="Stock" type="number" min="0" value={form.stock} onChange={set('stock')} required />
              </div>
              <Select label="Category" value={form.category_id} onChange={set('category_id')} required>
                {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
              <label className="flex items-center gap-3 cursor-pointer">
                <div
                  className={`w-9 h-5 rounded-full transition-colors relative ${form.is_active ? 'bg-emerald-600' : 'bg-zinc-700'}`}
                  onClick={() => setForm(f => ({ ...f, is_active: !f.is_active }))}
                >
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${form.is_active ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
                <span className="text-sm text-zinc-400">Active (visible to customers)</span>
              </label>
            </Card>

            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">{error}</div>
            )}

            <Button type="submit" size="lg" loading={saving}>
              {saved ? '✓ Saved' : 'Save changes'}
            </Button>
          </div>

          {/* Image */}
          <div className="space-y-4">
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4">Product image</h2>
              <div className="aspect-square rounded-xl bg-zinc-800 border border-dashed border-zinc-700 overflow-hidden relative">
                {product.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                {uploadingImage && (
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                    <Spinner />
                  </div>
                )}
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  type="button"
                  onClick={() => document.getElementById('img-upload')?.click()}
                  className="flex-1 py-2 text-xs text-zinc-400 border border-zinc-700 rounded-lg hover:border-zinc-600 hover:text-zinc-100 transition-colors"
                >
                  {product.image_url ? 'Replace' : 'Upload'}
                </button>
                {product.image_url && (
                  <button
                    type="button"
                    onClick={removeImage}
                    className="flex-1 py-2 text-xs text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/10 transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
              <input id="img-upload" type="file" accept="image/*" className="hidden" onChange={handleImage} />
            </Card>
          </div>
        </div>
      </form>
    </div>
  )
}
