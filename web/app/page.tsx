'use client'

import Link from 'next/link'
import {
  Search,
  ShoppingCart,
  MapPin,
  Zap,
  CheckCircle,
  Truck,
  Package,
  Star,
  ArrowRight,
  LayoutDashboard,
  Smartphone,
  Shirt,
  Home,
  BookOpen,
} from 'lucide-react'
import { useAuth } from '../lib/auth-context'

const features = [
  {
    icon: Search,
    title: 'Browse & Discover',
    description: 'Explore thousands of products across all categories with powerful search and filters.',
  },
  {
    icon: ShoppingCart,
    title: 'Easy Checkout',
    description: 'Add items to your cart and check out in seconds with a streamlined, secure flow.',
  },
  {
    icon: MapPin,
    title: 'Real-time Tracking',
    description: 'Follow your order from dispatch to your door with live location updates.',
  },
  {
    icon: Zap,
    title: 'Fast Delivery',
    description: 'Our driver network ensures your orders arrive quickly, wherever you are.',
  },
]

const categories = [
  { icon: Smartphone, label: 'Electronics', count: '2,400+ items' },
  { icon: Shirt, label: 'Clothing', count: '5,100+ items' },
  { icon: Home, label: 'Home & Garden', count: '3,700+ items' },
  { icon: BookOpen, label: 'Books & Media', count: '8,900+ items' },
]

const steps = [
  { n: '01', title: 'Browse & add to cart', body: 'Explore products by category or search. Add what you want with one click.' },
  { n: '02', title: 'Checkout securely', body: 'Review your cart, enter your address, and confirm your order in seconds.' },
  { n: '03', title: 'Track your delivery', body: 'Watch your order move in real time — from our warehouse to your front door.' },
]

const driverPerks = [
  'Flexible hours — work when you want',
  'Live order map with turn-by-turn navigation',
  'Instant earnings per delivery',
]

export default function LandingPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">

      {/* ── Header ── */}
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between sticky top-0 z-50 bg-zinc-950/95 backdrop-blur-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center">
            <Package className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="text-base font-bold tracking-tight">Orderly</span>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          <Link href="/shop" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors px-3 py-1.5 rounded-lg hover:bg-zinc-800/60">Shop</Link>
          <a href="#features" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors px-3 py-1.5 rounded-lg hover:bg-zinc-800/60">Features</a>
          <a href="#deliver" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors px-3 py-1.5 rounded-lg hover:bg-zinc-800/60">Deliver with us</a>
        </nav>

        <div className="flex items-center gap-2">
          {!user ? (
            <>
              <Link href="/auth/login" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors px-3 py-1.5">
                Sign in
              </Link>
              <Link href="/auth/register" className="text-sm px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium hover:bg-emerald-500 transition-colors">
                Get started
              </Link>
            </>
          ) : user.role === 'ADMIN' || user.role === 'DRIVER' ? (
            <Link href={user.role === 'ADMIN' ? '/admin' : '/driver'}
              className="flex items-center gap-1.5 text-sm text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </Link>
          ) : (
            <div className="flex items-center gap-3">
              <Link href="/shop" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">Shop</Link>
              <Link href="/orders" className="text-sm text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                My orders
              </Link>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1">

        {/* ── Hero ── */}
        <section className="max-w-5xl mx-auto px-4 sm:px-6 pt-20 pb-24 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-800/50 text-emerald-400 text-xs font-medium mb-8">
            <Star className="w-3.5 h-3.5" fill="currentColor" />
            Fast. Reliable. Real-time.
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05] mb-6">
            Shop smart,{' '}
            <span className="text-emerald-400">deliver fast</span>
          </h1>

          <p className="text-xl text-zinc-400 leading-relaxed mb-10 max-w-xl mx-auto">
            Discover thousands of products, check out in seconds, and track your delivery in real time — all in one place.
          </p>

          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="/shop">
              <button className="flex items-center gap-2 px-7 py-3.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-500 transition-colors">
                Start Shopping
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            {!user && (
              <Link href="/auth/register">
                <button className="px-7 py-3.5 rounded-xl bg-zinc-900 border border-zinc-700 text-zinc-300 text-sm font-medium hover:border-zinc-600 hover:text-zinc-100 transition-colors">
                  Create free account
                </button>
              </Link>
            )}
          </div>

          {/* Stats */}
          <div className="flex items-center justify-center gap-10 mt-16 flex-wrap">
            {[
              { value: '10k+', label: 'Products' },
              { value: '99.9%', label: 'Uptime' },
              { value: '<1 min', label: 'Avg. checkout' },
              { value: 'Live', label: 'Order tracking' },
            ].map(({ value, label }) => (
              <div key={label} className="text-center">
                <div className="text-2xl font-bold text-zinc-100">{value}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Categories ── */}
        <section className="border-y border-zinc-800 bg-zinc-900/40 py-16">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {categories.map(({ icon: Icon, label, count }) => (
                <Link href="/shop" key={label}>
                  <div className="group bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-emerald-700/50 hover:bg-zinc-800/60 transition-all text-center cursor-pointer">
                    <div className="w-10 h-10 rounded-lg bg-emerald-950/80 border border-emerald-800/40 text-emerald-400 flex items-center justify-center mx-auto mb-4">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="text-sm font-semibold text-zinc-200 group-hover:text-emerald-400 transition-colors">{label}</div>
                    <div className="text-xs text-zinc-500 mt-1">{count}</div>
                  </div>
                </Link>
              ))}
            </div>
            <div className="text-center mt-6">
              <Link href="/shop" className="text-sm text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Browse all categories →
              </Link>
            </div>
          </div>
        </section>

        {/* ── Features ── */}
        <section id="features" className="max-w-5xl mx-auto px-4 sm:px-6 py-24">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold mb-3">
              Everything you need, nothing you don't
            </h2>
            <p className="text-zinc-400 max-w-md mx-auto">
              A seamless shopping experience built for speed, transparency, and convenience.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
                <div className="w-10 h-10 rounded-lg bg-emerald-950/80 border border-emerald-800/50 text-emerald-400 flex items-center justify-center mb-5">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold text-zinc-100 mb-2">{title}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── How it works ── */}
        <section className="bg-zinc-900/40 border-y border-zinc-800 py-24">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <h2 className="text-3xl font-bold mb-14">How it works</h2>
            <div className="grid sm:grid-cols-3 gap-10">
              {steps.map(({ n, title, body }) => (
                <div key={n}>
                  <div className="text-5xl font-bold text-emerald-900/60 mb-4 select-none">{n}</div>
                  <h3 className="text-base font-semibold text-zinc-100 mb-2">{title}</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">{body}</p>
                </div>
              ))}
            </div>
            <div className="mt-14">
              <Link href={user ? '/shop' : '/auth/register'}>
                <button className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-500 transition-colors">
                  {user ? 'Continue shopping' : 'Get started for free'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </Link>
            </div>
          </div>
        </section>

        {/* ── Deliver with us ── */}
        <section id="deliver" className="max-w-5xl mx-auto px-4 sm:px-6 py-24">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
            <div className="px-8 py-14 sm:px-14 grid sm:grid-cols-2 gap-10 items-center">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-950/60 border border-sky-800/50 text-sky-400 text-xs font-medium mb-6">
                  <Truck className="w-3.5 h-3.5" />
                  Driver program
                </div>
                <h2 className="text-3xl font-bold mb-3">Earn by delivering</h2>
                <p className="text-zinc-400 leading-relaxed mb-6">
                  Join our driver network and earn on your own schedule. Accept orders nearby, use live GPS to navigate, and get paid fast.
                </p>
                <ul className="space-y-3 mb-8">
                  {driverPerks.map(perk => (
                    <li key={perk} className="flex items-start gap-2.5 text-sm text-zinc-400">
                      <CheckCircle className="w-4 h-4 text-sky-500 mt-0.5 shrink-0" />
                      {perk}
                    </li>
                  ))}
                </ul>
                <Link href="/auth/login">
                  <button className="flex items-center gap-2 px-6 py-3 rounded-xl border border-sky-800/60 text-sky-400 text-sm font-semibold hover:bg-sky-950/40 transition-colors">
                    Apply to deliver
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </Link>
              </div>

              <div className="hidden sm:flex items-center justify-center">
                <div className="w-44 h-44 rounded-full bg-sky-950/30 border border-sky-800/30 flex items-center justify-center">
                  <div className="w-24 h-24 rounded-full bg-sky-950/60 border border-sky-800/50 flex items-center justify-center">
                    <Truck className="w-10 h-10 text-sky-500" strokeWidth={1.5} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-zinc-800 px-6 py-8">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-emerald-600 flex items-center justify-center">
              <Package className="w-3 h-3 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-semibold">Orderly</span>
            <span className="text-sm text-zinc-500">— Fast, reliable e-commerce.</span>
          </div>
          <div className="flex items-center gap-5 text-sm text-zinc-500">
            <Link href="/shop" className="hover:text-zinc-300 transition-colors">Shop</Link>
            <Link href="/auth/login" className="hover:text-zinc-300 transition-colors">Sign in</Link>
            <Link href="/auth/register" className="hover:text-zinc-300 transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
