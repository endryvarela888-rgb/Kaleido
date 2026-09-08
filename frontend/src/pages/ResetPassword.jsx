import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { confirmPasswordReset } from '../api/auth'

export default function ResetPassword() {
  const { uid, token } = useParams()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formError, setFormError] = useState('')

  const mutation = useMutation({
    mutationFn: () => confirmPasswordReset(uid, token, password),
    onError: (error) => {
      const data = error.response?.data
      setFormError(data ? Object.values(data).flat().join(' ') : 'This reset link is invalid or has expired.')
    },
  })

  function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    if (password !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }
    mutation.mutate()
  }

  if (mutation.isSuccess) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <h1 className="auth-title">Password updated</h1>
          <p className="auth-subtitle">You can now log in with your new password.</p>
          <Link className="btn btn--primary btn--block" to="/login">
            Go to log in
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1 className="auth-title">Choose a new password</h1>
        {formError && <div className="form-error">{formError}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            New password
            <input
              className="field-input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
          <label>
            Confirm new password
            <input
              className="field-input"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
          <button type="submit" className="btn btn--primary btn--block" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : 'Reset password'}
          </button>
        </form>
        <p className="auth-footer">
          <Link to="/login">Back to log in</Link>
        </p>
      </div>
    </div>
  )
}
