'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { categories } from '../../../../lib/api'
import type { Category } from '../../../../lib/types'
import { Button, Card, Input, Spinner, Textarea } from '../../../../components/ui'

export default function EditCategoryPage() {
  const params = useParams()
  const router = useRouter()
  const [cat, setCat] = useState<Category | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', slug: '', is_active: true })

  useEffect(() => {
    categories.get(String(params.id))
      .then(c => {
        setCat(c)
        setForm({ name: c.name, description: c.description ?? '', slug: c.slug, is_active: c.is_active })
      })
      .catch(() => router.push('/admin/categories'))
      .finally(() => setLoading(false))
  }, [params.id, router])

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await categories.update(cat!.id, form)
      setSaved(true); setTimeout(() => setSaved(false), 2000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !cat) return
    setUploadingImage(true)
    try { const updated = await categories.uploadImage(cat.id, file); setCat(updated) }
    catch (err: unknown) { alert(err instanceof Error ? err.message : 'Upload failed') }
    finally { setUploadingImage(false) }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!cat) return null

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-8 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to categories
      </button>
      <h1 className="text-2xl font-bold text-zinc-100 mb-8">Edit category</h1>

      <form onSubmit={submit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 space-y-4">
              <Input label="Name" value={form.name} onChange={set('name')} required />
              <Input label="Slug" value={form.slug} onChange={set('slug')} required />
              <Textarea label="Description" value={form.description} onChange={set('description')} rows={3} />
              <label className="flex items-center gap-3 cursor-pointer">
                <div className={`w-9 h-5 rounded-full transition-colors relative ${form.is_active ? 'bg-emerald-600' : 'bg-zinc-700'}`}
                  onClick={() => setForm(f => ({ ...f, is_active: !f.is_active }))}>
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${form.is_active ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
                <span className="text-sm text-zinc-400">Active</span>
              </label>
            </Card>
            {error && <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">{error}</div>}
            <Button type="submit" size="lg" loading={saving}>{saved ? '✓ Saved' : 'Save changes'}</Button>
          </div>

          <div>
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-zinc-100 mb-4">Image</h2>
              <div className="aspect-square rounded-xl bg-zinc-800 border border-dashed border-zinc-700 overflow-hidden relative cursor-pointer"
                onClick={() => document.getElementById('cat-edit-img')?.click()}>
                {cat.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={cat.image_url} alt={cat.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                )}
                {uploadingImage && <div className="absolute inset-0 bg-black/60 flex items-center justify-center"><Spinner /></div>}
              </div>
              <input id="cat-edit-img" type="file" accept="image/*" className="hidden" onChange={handleImage} />
            </Card>
          </div>
        </div>
      </form>
    </div>
  )
}
