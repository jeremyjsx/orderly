'use client'

import { type ButtonHTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes, forwardRef } from 'react'
import { Inbox } from 'lucide-react'

// Button
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, children, className = '', disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center gap-2 font-medium transition-colors rounded-lg cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed select-none'
    const variants = {
      primary: 'bg-emerald-600 text-white hover:bg-emerald-500 active:scale-[0.98]',
      secondary: 'bg-zinc-800 text-zinc-100 border border-zinc-700 hover:border-zinc-600 hover:bg-zinc-700/60 active:scale-[0.98]',
      ghost: 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 active:scale-[0.98]',
      danger: 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 active:scale-[0.98]',
    }
    const sizes = {
      sm: 'text-xs px-3 py-1.5 h-7',
      md: 'text-sm px-4 py-2 h-9',
      lg: 'text-sm px-5 py-2.5 h-10',
    }
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-0.5 h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'

// Input
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs text-zinc-400 uppercase tracking-wider">{label}</label>}
      <input
        ref={ref}
        className={`h-9 px-3 bg-zinc-900 border ${error ? 'border-red-500/50' : 'border-zinc-700'} rounded-lg text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-emerald-500 transition-colors ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
)
Input.displayName = 'Input'

// Textarea
interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = '', ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs text-zinc-400 uppercase tracking-wider">{label}</label>}
      <textarea
        ref={ref}
        className={`px-3 py-2 bg-zinc-900 border ${error ? 'border-red-500/50' : 'border-zinc-700'} rounded-lg text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-emerald-500 transition-colors resize-none ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
)
Textarea.displayName = 'Textarea'

// Select
export function Select({
  label, error, children, className = '', ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string; error?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs text-zinc-400 uppercase tracking-wider">{label}</label>}
      <select
        className={`h-9 px-3 bg-zinc-900 border ${error ? 'border-red-500/50' : 'border-zinc-700'} rounded-lg text-sm text-zinc-100 outline-none focus:border-emerald-500 transition-colors appearance-none cursor-pointer ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
}

// Card
export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-zinc-900 border border-zinc-800 rounded-xl ${className}`}>
      {children}
    </div>
  )
}

// Badge
type BadgeVariant = 'default' | 'green' | 'yellow' | 'red' | 'blue' | 'purple'
export function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: BadgeVariant }) {
  const styles: Record<BadgeVariant, string> = {
    default: 'bg-zinc-800 text-zinc-400',
    green: 'bg-emerald-500/10 text-emerald-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
    red: 'bg-red-500/10 text-red-400',
    blue: 'bg-blue-500/10 text-blue-400',
    purple: 'bg-purple-500/10 text-purple-400',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${styles[variant]}`}>
      {children}
    </span>
  )
}

// Status badge for orders
export function OrderStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; variant: BadgeVariant }> = {
    pending: { label: 'Pending', variant: 'yellow' },
    processing: { label: 'Processing', variant: 'blue' },
    shipped: { label: 'Shipped', variant: 'purple' },
    delivered: { label: 'Delivered', variant: 'green' },
    cancelled: { label: 'Cancelled', variant: 'red' },
  }
  const config = map[status] ?? { label: status, variant: 'default' as BadgeVariant }
  return <Badge variant={config.variant}>{config.label}</Badge>
}

// Spinner
export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const s = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }
  return (
    <svg className={`animate-spin text-emerald-400 ${s[size]}`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

// Empty state
export function Empty({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
        <Inbox className="w-5 h-5 text-zinc-500" />
      </div>
      <p className="text-sm font-medium text-zinc-400">{title}</p>
      {description && <p className="text-xs text-zinc-500 mt-1">{description}</p>}
    </div>
  )
}

// Price formatter
export function formatPrice(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}
