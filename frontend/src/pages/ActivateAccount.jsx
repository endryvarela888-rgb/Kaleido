import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ActivateAccount() {
  const { uid, token } = useParams()
  const { activate } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus] = useState('pending') // 'pending' | 'success' | 'error'
  const [error, setError] = useState('')
  // The activation token is single-use, and effects can run twice in dev
  // (React StrictMode) — without this guard the second run would hit the
  // API with an already-consumed token and show a false "invalid link".
  const hasRun = useRef(false)

  useEffect(() => {
    if (hasRun.current) return
    hasRun.current = true

    activate(uid, token)
      .then(() => {
        setStatus('success')
        setTimeout(() => navigate('/'), 1500)
      })
      .catch((requestError) => {
        setStatus('error')
        setError(requestError.response?.data?.detail || 'This activation link is invalid or has expired.')
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uid, token])

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        {status === 'pending' && (
          <>
            <h1 className="auth-title">Activating your account…</h1>
            <p className="auth-subtitle">Just a moment.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <h1 className="auth-title">You're all set!</h1>
            <p className="auth-subtitle">Your account is verified — taking you inside.</p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1 className="auth-title">Link invalid or expired</h1>
            <div className="form-error">{error}</div>
            <p className="auth-footer">
              <Link to="/resend-activation">Request a new activation link</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
