'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Package, LayoutDashboard, Box, Tag, ClipboardList, Users, LogOut } from 'lucide-react'
import { useAuth } from '../../lib/auth-context'
import { Spinner } from '../../components/ui'

const links = [
  { href: '/admin', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { href: '/admin/products', label: 'Products', icon: Box },
  { href: '/admin/categories', label: 'Categories', icon: Tag },
  { href: '/admin/orders', label: 'Orders', icon: ClipboardList },
  { href: '/admin/users', label: 'Users', icon: Users },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth()
  const router = useRouter()
  const path = usePathname()

  useEffect(() => {
    if (!isLoading && (!user || user.role !== 'ADMIN')) {
      router.replace('/auth/login')
    }
  }, [user, isLoading, router])

  if (isLoading || !user) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  )

  return (
    <div className="min-h-screen bg-zinc-950 flex">
      <aside className="w-56 shrink-0 border-r border-zinc-800 flex flex-col h-screen sticky top-0">
        <div className="px-4 py-5 border-b border-zinc-800">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-600 flex items-center justify-center">
              <Package className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-sm font-semibold text-zinc-100 leading-none">Orderly</p>
              <p className="text-[10px] text-violet-400 leading-none mt-0.5 uppercase tracking-wider">Admin</p>
            </div>
          </Link>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-0.5">
          {links.map(({ href, label, icon: Icon, exact }) => {
            const active = exact ? path === href : path.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-violet-500/10 text-violet-400'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="px-3 py-4 border-t border-zinc-800">
          <p className="text-xs text-zinc-500 truncate px-2 mb-2">{user.email}</p>
          <button
            onClick={() => { logout(); router.push('/') }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/5 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <main className="p-8">{children}</main>
      </div>
    </div>
  )
}
