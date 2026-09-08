import { createContext, useContext, useEffect, useState } from 'react'
import * as authApi from '../api/auth'
import { getTokens } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On first load, if there's a token saved from a previous session,
  // try to restore who's logged in before rendering protected routes.
  useEffect(() => {
    const { access } = getTokens()
    if (!access) {
      setLoading(false)
      return
    }
    authApi
      .fetchMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function login(email, password) {
    await authApi.login(email, password)
    const me = await authApi.fetchMe()
    setUser(me)
    return me
  }

  // Activation exchanges the emailed token for a JWT pair and returns the
  // user in the same call, so unlike login() there's no need for a
  // separate fetchMe() round trip.
  async function activate(uid, token) {
    const { user: activatedUser } = await authApi.activateAccount(uid, token)
    setUser(activatedUser)
    return activatedUser
  }

  function logout() {
    authApi.logout()
    setUser(null)
  }

  async function signup(payload) {
    return authApi.signup(payload)
  }

  const value = { user, loading, login, logout, signup, activate, isAuthenticated: !!user }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}