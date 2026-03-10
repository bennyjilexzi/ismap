import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const isAdmin = localStorage.getItem('isAdmin') === 'true'
    const username = localStorage.getItem('username')
    if (token && username) {
      setUser({ token, isAdmin, username })
    }
  }, [])

  const login = (data) => {
    const { token, is_admin, username } = data
    localStorage.setItem('token', token)
    localStorage.setItem('isAdmin', is_admin)
    localStorage.setItem('username', username)
    setUser({ token, isAdmin: is_admin, username })
  }

  const logout = () => {
    localStorage.clear()
    setUser(null)
    window.location.reload()
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
