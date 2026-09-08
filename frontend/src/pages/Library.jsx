import { useQuery } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { fetchHistory, fetchSaved } from '../api/content'
import ContentCard from '../components/ContentCard'
import { useAuth } from '../hooks/useAuth'

export default function Library() {
  const { isAuthenticated } = useAuth()
  const saved = useLocation().pathname === '/saved'
  const query = useQuery({ queryKey: [saved ? 'saved' : 'history'], queryFn: saved ? fetchSaved : fetchHistory, enabled: isAuthenticated })
  if (!isAuthenticated) return <p className="empty-state"><Link to="/login">Log in</Link> to view your library.</p>
  if (query.isLoading) return <p className="empty-state">Loading…</p>
  if (query.isError) return <p className="empty-state">Unable to load your library.</p>
  const content = saved ? query.data.content : query.data
  return <section className="feed-column"><h1>{saved ? 'Saved for later' : 'Watch history'}</h1>{!content.length && <p className="empty-state">Nothing here yet.</p>}{content.map((item) => <ContentCard item={item} key={item.id} />)}</section>
}
