'use client'

import { useEffect, useState } from 'react'
import { users } from '../../../lib/api'
import type { User } from '../../../lib/types'
import { Badge, Button, Card, Empty, Spinner } from '../../../components/ui'
import { useAuth } from '../../../lib/auth-context'

export default function AdminUsersPage() {
  const { user: me } = useAuth()
  const [items, setItems] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [deleting, setDeleting] = useState<string | null>(null)
  const limit = 20

  const load = () => {
    setLoading(true)
    users.list({ offset, limit })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [offset])

  const handleDelete = async (id: string, email: string) => {
    if (!confirm(`Delete user "${email}"? This cannot be undone.`)) return
    setDeleting(id)
    try {
      await users.remove(id)
      load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete')
    } finally {
      setDeleting(null)
    }
  }

  const roleVariant = (role: string) => {
    if (role === 'ADMIN') return 'purple' as const
    if (role === 'DRIVER') return 'blue' as const
    return 'green' as const
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Users</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} registered</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : items.length === 0 ? (
        <Empty title="No users found" />
      ) : (
        <>
          <Card>
            <div className="divide-y divide-zinc-800">
              {items.map(user => (
                <div key={user.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
                    <span className="text-xs font-medium text-zinc-400">
                      {user.email[0].toUpperCase()}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-zinc-100 truncate">
                      {user.email}
                      {user.id === me?.id && <span className="ml-2 text-xs text-zinc-500">(you)</span>}
                    </p>
                    <p className="text-xs font-mono text-zinc-500">{user.id.slice(0, 8)}</p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <Badge variant={roleVariant(user.role)}>{user.role}</Badge>
                    {user.id !== me?.id && (
                      <Button
                        variant="danger"
                        size="sm"
                        loading={deleting === user.id}
                        onClick={() => handleDelete(user.id, user.email)}
                      >
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {total > limit && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))}>Previous</Button>
              <span className="text-xs text-zinc-500">{Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}</span>
              <Button variant="secondary" size="sm" disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)}>Next</Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
