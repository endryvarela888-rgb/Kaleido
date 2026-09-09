import { NavLink } from 'react-router-dom'

export default function Sidebar({ open, onClose }) {
  return (
    <>
      <div className={`sidebar-overlay ${open ? 'is-open' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'is-open' : ''}`}>
        <div className="sidebar-brand">
          <span className="sigil-mark" aria-hidden="true">
            <svg viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="17" stroke="currentColor" strokeWidth="1.5" />
              <path d="M20 6L20 34M8 20L32 20M11 11L29 29M29 11L11 29" stroke="currentColor" strokeWidth="1" />
              <circle cx="20" cy="20" r="4" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </span>
          <span className="brand-name">Kaleido</span>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" className="sidebar-link" onClick={onClose}>Home</NavLink>
          <NavLink to="/subscriptions" className="sidebar-link" onClick={onClose}>Subscriptions</NavLink>
          <NavLink to="/history" className="sidebar-link" onClick={onClose}>History</NavLink>
          <NavLink to="/saved" className="sidebar-link" onClick={onClose}>Saved for later</NavLink>
        </nav>
      </aside>
    </>
  )
}