import { Outlet } from 'react-router-dom'
import { useEffect, useRef } from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

export default function Layout() {
  const particleFieldRef = useRef(null)

  useEffect(() => {
    const field = particleFieldRef.current
    if (!field || field.childElementCount > 0) return

    const COUNT = 28
    for (let i = 0; i < COUNT; i++) {
      const p = document.createElement('span')
      p.className = 'particle'
      p.style.left = `${Math.random() * 100}%`
      p.style.animationDuration = `${12 + Math.random() * 14}s`
      p.style.animationDelay = `${Math.random() * 12}s`
      p.style.opacity = `${0.3 + Math.random() * 0.4}`
      field.appendChild(p)
    }
  }, [])

  return (
    <>
      <div className="particle-field" ref={particleFieldRef}></div>
      <Sidebar />
      <Navbar />
      <main className="page-main">
        <Outlet />
      </main>
    </>
  )
}