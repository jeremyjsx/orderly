'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Package } from 'lucide-react'
import { useAuth } from '../lib/auth-context'
import { Button } from './ui'

export function Nav() {
  const { user, logout, isLoading } = useAuth()
  const router = useRouter()
  const path = usePathname()

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const shopLinks = [
    { href: '/shop', label: 'Shop' },
    { href: '/cart', label: 'Cart' },
    { href: '/orders', label: 'Orders' },
  ]
  const adminLinks = [
    { href: '/admin', label: 'Dashboard' },
    { href: '/admin/products', label: 'Products' },
    { href: '/admin/categories', label: 'Categories' },
    { href: '/admin/orders', label: 'Orders' },
    { href: '/admin/users', label: 'Users' },
  ]
  const driverLinks = [
    { href: '/driver', label: 'Dashboard' },
    { href: '/driver/available', label: 'Available' },
    { href: '/driver/deliveries', label: 'My Deliveries' },
  ]

  const links =
    user?.role === 'ADMIN' ? adminLinks :
    user?.role === 'DRIVER' ? driverLinks :
    user ? shopLinks :
    [{ href: '/shop', label: 'Shop' }]

  const roleColor: Record<string, string> = {
    ADMIN: 'text-violet-400',
    DRIVER: 'text-sky-400',
    USER: 'text-emerald-400',
  }

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-sm">
      <nav className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="w-6 h-6 rounded-lg bg-emerald-600 flex items-center justify-center">
            <Package className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
          </div>
          <span className="text-sm font-semibold text-zinc-100 tracking-tight">Orderly</span>
        </Link>

        <div className="flex items-center gap-1 flex-1">
          {links.map(({ href, label }) => {
            const active = path === href || (href !== '/' && path.startsWith(href))
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  active
                    ? 'text-emerald-400 bg-emerald-500/10'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                {label}
              </Link>
            )
          })}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {!isLoading && (
            user ? (
              <div className="flex items-center gap-3">
                <span className={`text-xs font-mono ${roleColor[user.role] ?? 'text-zinc-400'}`}>
                  {user.role}
                </span>
                <span className="text-xs text-zinc-500 hidden sm:block">{user.email}</span>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Sign out
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/auth/login">
                  <Button variant="ghost" size="sm">Sign in</Button>
                </Link>
                <Link href="/auth/register">
                  <Button variant="primary" size="sm">Get started</Button>
                </Link>
              </div>
            )
          )}
        </div>
      </nav>
    </header>
  )
}
