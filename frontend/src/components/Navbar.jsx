import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false)
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  return (
    <header className="topbar">
      <button className="icon-btn" onClick={onMenuClick} aria-label="Open menu">
        <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
      </button>

      <Link className="brand-name" to="/">Kaleido</Link>

      <div className="topbar-right" ref={menuRef}>
        {user ? (
          <>
            <button className="avatar-btn" onClick={() => setMenuOpen((v) => !v)} aria-label="Open user menu">
              <span className="avatar avatar--sm">{user.display_name?.[0]?.toUpperCase()}</span>
            </button>
            <div className={`dropdown-menu ${menuOpen ? 'is-open' : ''}`}>
              <Link to={`/profile/${user.id}`} onClick={() => setMenuOpen(false)}>Profile</Link>
              {user.is_creator && (
                <Link to="/creator" onClick={() => setMenuOpen(false)}>Creator dashboard</Link>
              )}
              <Link to="/settings" onClick={() => setMenuOpen(false)}>Settings</Link>
              <button onClick={() => { setMenuOpen(false); logout() }}>Log out</button>
            </div>
          </>
        ) : (
          <Link className="btn btn--ghost" to="/login">Log in</Link>
        )}
      </div>
    </header>
  )
}