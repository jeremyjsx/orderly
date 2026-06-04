'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { categories, products } from '../../../../lib/api'
import type { Category } from '../../../../lib/types'
import { Button, Card, Input, Select, Spinner, Textarea } from '../../../../components/ui'

export default function NewProductPage() {
  const router = useRouter()
  const [cats, setCats] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    name: '', description: '', price: '', stock: '', category_id: '',
  })

  useEffect(() => {
    categories.list({ limit: 100 }).then(r => setCats(r.items)).catch(() => {})
  }, [])

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const handleImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!form.category_id) { setError('Please select a category'); return }
    setLoading(true)
    try {
      const product = await products.create({
        name: form.name,
        description: form.description,
        price: parseFloat(form.price),
        stock: parseInt(form.stock),
        category_id: form.category_id,
      })
      if (imageFile) {
        await products.uploadImage(product.id, imageFile)
      }
      router.push('/admin/products')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create product')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to products
      </button>

      <h1 className="text-2xl font-bold text-zinc-100 mb-8">Add product</h1>

      <form onSubmit={submit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 space-y-4">
              <h2 className="text-sm font-semibold text-zinc-100">Product details</h2>
              <Input label="Name" value={form.name} onChange={set('name')} required placeholder="e.g. Wireless Headphones" />
              <Textarea label="Description" value={form.description} onChange={set('description')} required placeholder="Product description..." rows={3} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Price ($)" type="number" step="0.01" min="0.01" value={form.price} onChange={set('price')} required placeholder="9.99" />
                <Input label="Stock" type="number" min="1" value={form.stock} onChange={set('stock')} required placeholder="100" />
              </div>
              <Select label="Category" value={form.category_id} onChange={set('category_id')} required>
                <option value="">Select category</option>
                {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Card>

            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">{error}</div>
            )}
          </div>

          {/* Image */}
          <div className="space-y-4">
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4">Product image</h2>
              <div
                className="aspect-square rounded-xl bg-zinc-800 border border-dashed border-zinc-700 flex flex-col items-center justify-center gap-3 overflow-hidden relative cursor-pointer hover:border-emerald-500/30 transition-colors"
                onClick={() => document.getElementById('image-input')?.click()}
              >
                {imagePreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={imagePreview} alt="Preview" className="absolute inset-0 w-full h-full object-cover" />
                ) : (
                  <>
                    <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <p className="text-xs text-zinc-500">Click to upload</p>
                  </>
                )}
              </div>
              <input id="image-input" type="file" accept="image/*" className="hidden" onChange={handleImage} />
            </Card>

            <Button type="submit" className="w-full" size="lg" loading={loading}>
              Create product
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}
