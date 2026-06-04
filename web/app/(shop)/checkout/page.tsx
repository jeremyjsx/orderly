'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { MapPin } from 'lucide-react'
import { cart as cartApi, orders } from '../../../lib/api'
import type { Cart } from '../../../lib/types'
import { useAuth } from '../../../lib/auth-context'
import { Button, Card, Input, Spinner, formatPrice } from '../../../components/ui'

interface AddressForm {
  recipient_name: string
  phone: string
  street: string
  city: string
  state: string
  postal_code: string
  country: string
}

const empty: AddressForm = {
  recipient_name: '', phone: '', street: '', city: '',
  state: '', postal_code: '', country: 'USA',
}

export default function CheckoutPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [cartData, setCartData] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<AddressForm>(empty)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isLoading) return
    if (!user) { router.push('/auth/login'); return }
    cartApi.get()
      .then(d => {
        if (!d.items.length) router.push('/cart')
        setCartData(d)
      })
      .catch(() => router.push('/cart'))
      .finally(() => setLoading(false))
  }, [user, isLoading, router])

  const set = (field: keyof AddressForm) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const order = await orders.create(form)
      router.push(`/orders/${order.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to place order')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-100 mb-8">Checkout</h1>

      <form onSubmit={submit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6">
              <h2 className="text-sm font-semibold text-zinc-100 mb-5 flex items-center gap-2">
                <div className="w-5 h-5 rounded bg-emerald-500/10 flex items-center justify-center">
                  <MapPin className="w-3 h-3 text-emerald-400" />
                </div>
                Shipping address
              </h2>

              <div className="grid sm:grid-cols-2 gap-4">
                <Input label="Recipient name" value={form.recipient_name} onChange={set('recipient_name')} required placeholder="John Doe" />
                <Input label="Phone" value={form.phone} onChange={set('phone')} required placeholder="+1 234 567 8900" />
                <Input label="Street address" value={form.street} onChange={set('street')} required placeholder="123 Main Street" className="sm:col-span-2" />
                <Input label="City" value={form.city} onChange={set('city')} required placeholder="New York" />
                <Input label="State" value={form.state} onChange={set('state')} required placeholder="NY" />
                <Input label="Postal code" value={form.postal_code} onChange={set('postal_code')} required placeholder="10001" />
                <Input label="Country" value={form.country} onChange={set('country')} required placeholder="USA" />
              </div>
            </Card>

            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>

          <div>
            <Card className="p-5 sticky top-20">
              <h3 className="text-sm font-semibold text-zinc-100 mb-4">Order summary</h3>

              <div className="space-y-2 mb-4 text-sm">
                {cartData?.items.map(item => (
                  <div key={item.id} className="flex justify-between">
                    <span className="text-zinc-400 truncate max-w-[60%]">{item.product.name} ×{item.quantity}</span>
                    <span className="text-zinc-100">{formatPrice(item.subtotal)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t border-zinc-800 pt-4 mb-5">
                <div className="flex justify-between">
                  <span className="font-semibold text-zinc-100">Total</span>
                  <span className="font-bold text-emerald-400 text-lg">{formatPrice(cartData?.totals.grand_total ?? 0)}</span>
                </div>
              </div>

              <Button type="submit" className="w-full" size="lg" loading={submitting}>
                Place order →
              </Button>
            </Card>
          </div>
        </div>
      </form>
    </div>
  )
}
