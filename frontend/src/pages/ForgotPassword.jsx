import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { requestPasswordReset } from '../api/auth'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const mutation = useMutation({ mutationFn: () => requestPasswordReset(email) })

  if (mutation.isSuccess) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <h1 className="auth-title">Check your inbox</h1>
          <p className="auth-subtitle">
            If <strong>{email}</strong> is registered, we sent a link to reset your password.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1 className="auth-title">Forgot your password?</h1>
        <p className="auth-subtitle">Enter your email and we'll send you a reset link.</p>
        <form
          className="auth-form"
          onSubmit={(event) => {
            event.preventDefault()
            mutation.mutate()
          }}
        >
          <label>
            Email
            <input
              className="field-input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn btn--primary btn--block" disabled={mutation.isPending}>
            {mutation.isPending ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
        <p className="auth-footer">
          <Link to="/login">Back to log in</Link>
        </p>
      </div>
    </div>
  )
}
