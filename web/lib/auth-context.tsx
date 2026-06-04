'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { auth } from './api'
import type { Role, User } from './types'

const normalize = (u: User): User => ({ ...u, role: u.role.toUpperCase() as Role })

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (email: string, password: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  register: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setIsLoading(false); return }
    auth.me()
      .then(u => setUser(normalize(u)))
      .catch(() => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token') })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { user } = await auth.login(email, password)
    setUser(normalize(user))
  }, [])

  const logout = useCallback(async () => {
    await auth.logout()
    setUser(null)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await auth.register(email, password)
    const { user } = await auth.login(email, password)
    setUser(normalize(user))
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
