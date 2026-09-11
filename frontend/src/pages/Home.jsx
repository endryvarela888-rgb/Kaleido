import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchFeed, fetchCategories } from '../api/content'
import { fetchDiscoverCreators } from '../api/users'
import ContentCard from '../components/ContentCard'

export default function Home() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')

  const { data: feed, isLoading, isError } = useQuery({
    queryKey: ['feed', query, category],
    queryFn: () => fetchFeed({ q: query, category }),
  })
  const { data: categories = [] } = useQuery({ queryKey: ['categories'], queryFn: fetchCategories })
  const { data: discoverCreators = [] } = useQuery({ queryKey: ['discover-creators'], queryFn: fetchDiscoverCreators })

  return (
    <div className="feed-layout">
      <section className="feed-column">
        <form className="search-bar" onSubmit={(event) => event.preventDefault()}>
          <svg className="search-icon" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
            <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search creators…" />
          <select className="search-filter" value={category} onChange={(event) => setCategory(event.target.value)} aria-label="Filter by category">
            <option value="">All categories</option>
            {categories.map((item) => <option key={item.id} value={item.slug}>{item.name}</option>)}
          </select>
        </form>
        {isLoading && <p className="empty-state">Loading feed…</p>}
        {isError && <p className="empty-state">Couldn't load the feed.</p>}
        {feed?.results?.map((item) => (
          <ContentCard key={item.id} item={item} />
        ))}
        {feed?.results?.length === 0 && <p className="empty-state">Nothing here yet.</p>}
      </section>
      <aside className="discover-column">
        <h2 className="discover-heading">Discover creators</h2>
        {discoverCreators.map((creator) => (
          <Link to={`/profile/${creator.id}`} key={creator.id} className="creator-mini-card">
            {creator.avatar ? (
              <img className="avatar avatar--sm avatar--image" src={creator.avatar} alt={creator.display_name} />
            ) : (
              <span className="avatar avatar--sm">{creator.display_name?.[0]?.toUpperCase()}</span>
            )}
            <div>
              <p className="creator-mini-card__name">{creator.display_name}</p>
              {creator.creator_profile?.category && (
                <p className="creator-mini-card__category">{creator.creator_profile.category}</p>
              )}
            </div>
          </Link>
        ))}
        {discoverCreators.length === 0 && <p className="empty-state">No creators to discover yet.</p>}
      </aside>
    </div>
  )
}

