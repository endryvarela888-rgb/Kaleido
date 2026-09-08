import { useAuth } from '../hooks/useAuth'
import { Link } from 'react-router-dom'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="topbar">
      <Link className="brand-name" to="/">Kaleido</Link>
      <div className="topbar-right">
        {user && (
          <>
            <span className="avatar avatar--sm">{user.display_name?.[0]?.toUpperCase()}</span>
            <Link className="btn btn--ghost" to="/settings">Settings</Link>
            <button className="btn btn--ghost" onClick={logout}>Log out</button>
          </>
        )}
        {!user && <Link className="btn btn--ghost" to="/login">Log in</Link>}
      </div>
    </header>
  )
}
