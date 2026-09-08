import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <div className="page-main">Loading…</div>
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}