import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Signup() {
  const { signup } = useAuth()
  const [form, setForm] = useState({ email: '', display_name: '', password: '' })
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signup(form)
      setSent(true)
    } catch (err) {
      const data = err.response?.data
      setError(data ? Object.values(data).flat().join(' ') : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  if (sent) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <h1 className="auth-title">Check your inbox</h1>
          <p className="auth-subtitle">We sent a verification link to <strong>{form.email}</strong>.</p>
          <p className="auth-footer">
            Didn't get it? <Link to="/resend-activation">Resend the activation email</Link>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1 className="auth-title">Create your account</h1>
        {error && <div className="form-error">{error}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Email
            <input className="field-input" type="email" name="email" value={form.email}
                   onChange={handleChange} required />
          </label>
          <label>Display name
            <input className="field-input" type="text" name="display_name" value={form.display_name}
                   onChange={handleChange} required />
          </label>
          <label>Password
            <input className="field-input" type="password" name="password" value={form.password}
                   onChange={handleChange} required minLength={8} />
          </label>
          <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Sign up'}
          </button>
        </form>
        <p className="auth-footer">Already have an account? <Link to="/login">Log in</Link></p>
      </div>
    </div>
  )
}