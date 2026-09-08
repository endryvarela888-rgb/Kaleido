import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { becomeCreator, changePassword, updateMe } from '../api/auth'
import { useAuth } from '../hooks/useAuth'

export default function Settings() {
  const { user, isAuthenticated, logout } = useAuth()
  const [profile, setProfile] = useState({ display_name: user?.display_name || '', bio: user?.bio || '' })
  const [password, setPassword] = useState({ old_password: '', new_password: '' })
  const [message, setMessage] = useState('')
  const update = useMutation({ mutationFn: () => updateMe(profile), onSuccess: () => setMessage('Profile updated.') })
  const creator = useMutation({ mutationFn: becomeCreator, onSuccess: () => window.location.reload() })
  const passwordUpdate = useMutation({ mutationFn: () => changePassword(password), onSuccess: () => { setMessage('Password updated. Log in again to continue.'); logout() } })
  if (!isAuthenticated) return <p className="empty-state">Log in to manage your account.</p>
  return <section><h1>Account settings</h1>{message && <p>{message}</p>}
    <form className="content-card__body auth-form" onSubmit={(event) => { event.preventDefault(); update.mutate() }}><h2>Profile</h2><input className="field-input" value={profile.display_name} onChange={(event) => setProfile({ ...profile, display_name: event.target.value })} required /><textarea className="field-input" value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} /><button className="btn btn--primary" disabled={update.isPending}>Save profile</button></form>
    {!user.is_creator && <section className="content-card__body"><h2>Become a creator</h2><button className="btn btn--primary" disabled={creator.isPending} onClick={() => creator.mutate()}>Activate creator tools</button></section>}
    <form className="content-card__body auth-form" onSubmit={(event) => { event.preventDefault(); passwordUpdate.mutate() }}><h2>Change password</h2><input className="field-input" type="password" placeholder="Current password" required onChange={(event) => setPassword({ ...password, old_password: event.target.value })} /><input className="field-input" type="password" placeholder="New password" minLength="8" required onChange={(event) => setPassword({ ...password, new_password: event.target.value })} /><button className="btn btn--ghost">Change password</button>{passwordUpdate.isError && <p className="form-error">Unable to change the password.</p>}</form>
  </section>
}
