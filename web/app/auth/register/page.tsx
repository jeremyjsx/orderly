'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Package } from 'lucide-react'
import { useAuth } from '../../../lib/auth-context'
import { Button, Input } from '../../../components/ui'

export default function RegisterPage() {
  const { register, user } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) router.replace('/shop')
  }, [user, router])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    setLoading(true)
    try {
      await register(email, password)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center">
              <Package className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-semibold text-zinc-100">Orderly</span>
          </Link>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
          <h1 className="text-xl font-semibold text-zinc-100 mb-1">Create account</h1>
          <p className="text-sm text-zinc-500 mb-6">Start shopping in seconds</p>

          <form onSubmit={submit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
            <Input
              label="Password"
              type="password"
              placeholder="Min 8 characters"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />

            {error && (
              <div className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" loading={loading} size="lg">
              Create account
            </Button>
          </form>

          <p className="text-center text-xs text-zinc-500 mt-6">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-emerald-400 hover:text-emerald-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
