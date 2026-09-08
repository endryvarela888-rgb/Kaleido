import { useState } from 'react'
import { toggleLike } from '../api/content'
import { useAuth } from '../hooks/useAuth'

export default function LikeButton({ contentId, initialLiked, initialCount }) {
  const [liked, setLiked] = useState(initialLiked)
  const [count, setCount] = useState(initialCount)
  const [error, setError] = useState('')
  const { isAuthenticated } = useAuth()

  async function handleClick() {
    setError('')
    if (!isAuthenticated) {
      setError('Log in to like content.')
      return
    }
    try {
      const result = await toggleLike(contentId)
      setLiked(result.liked)
      setCount(result.count)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update the like.')
    }
  }

  return (
    <>
      <button className={`action-btn ${liked ? 'is-active' : ''}`} onClick={handleClick}>
        <svg viewBox="0 0 24 24" fill="none">
          <path
            d="M12 21s-7.5-4.6-10-9.3C.5 8 2 4.5 5.5 4c2-.3 3.7.6 4.9 2.2C11.6 4.6 13.3 3.7 15.3 4c3.5.5 5 4 3.5 7.7-2.5 4.7-10 9.3-10 9.3z"
            stroke="currentColor"
            strokeWidth="1.6"
          />
        </svg>
        <span className="action-count">{count}</span>
      </button>
      {error && <p className="form-error">{error}</p>}
    </>
  )
}