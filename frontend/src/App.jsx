import { useAuth } from './context/AuthContext'
import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './components/Landing'
import AuthScreen from './components/AuthScreen'
import Dashboard from './components/Dashboard'

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route
        path="/"
        element={user ? <Dashboard /> : <Landing />}
      />
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <AuthScreen initialTab="login" />}
      />
      <Route
        path="/signup"
        element={user ? <Navigate to="/" replace /> : <AuthScreen initialTab="signup" />}
      />
      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  )
}
