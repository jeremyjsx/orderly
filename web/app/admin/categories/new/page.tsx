'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { categories } from '../../../../lib/api'
import { Button, Card, Input, Textarea } from '../../../../components/ui'

export default function NewCategoryPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', description: '', slug: '', is_active: true })

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    setForm(f => ({ ...f, name, slug }))
  }

  const handleImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const cat = await categories.create({
        name: form.name,
        description: form.description || undefined,
        slug: form.slug,
        is_active: form.is_active,
      })
      if (imageFile) await categories.uploadImage(cat.id, imageFile)
      router.push('/admin/categories')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to categories
      </button>
      <h1 className="text-2xl font-bold text-zinc-100 mb-8">Add category</h1>

      <form onSubmit={submit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 space-y-4">
              <Input label="Name" value={form.name} onChange={handleNameChange} required placeholder="e.g. Electronics" />
              <Input label="Slug" value={form.slug} onChange={set('slug')} required placeholder="e.g. electronics" />
              <Textarea label="Description (optional)" value={form.description} onChange={set('description')} rows={3} />
              <label className="flex items-center gap-3 cursor-pointer">
                <div
                  className={`w-9 h-5 rounded-full transition-colors relative ${form.is_active ? 'bg-emerald-600' : 'bg-zinc-700'}`}
                  onClick={() => setForm(f => ({ ...f, is_active: !f.is_active }))}
                >
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${form.is_active ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
                <span className="text-sm text-zinc-400">Active</span>
              </label>
            </Card>
            {error && <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">{error}</div>}
          </div>

          <div className="space-y-4">
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4">Image (optional)</h2>
              <div
                className="aspect-square rounded-xl bg-zinc-800 border border-dashed border-zinc-700 flex flex-col items-center justify-center gap-2 overflow-hidden relative cursor-pointer hover:border-emerald-500/30 transition-colors"
                onClick={() => document.getElementById('cat-img')?.click()}
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
              <input id="cat-img" type="file" accept="image/*" className="hidden" onChange={handleImage} />
            </Card>
            <Button type="submit" className="w-full" size="lg" loading={loading}>Create category</Button>
          </div>
        </div>
      </form>
    </div>
  )
}
