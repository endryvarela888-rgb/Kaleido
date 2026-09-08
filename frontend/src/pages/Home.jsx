import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchFeed, fetchCategories } from '../api/content'
import ContentCard from '../components/ContentCard'

export default function Home() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')

  const { data: feed, isLoading, isError } = useQuery({
    queryKey: ['feed', query, category],
    queryFn: () => fetchFeed({ q: query, category }),
  })
  const { data: categories = [] } = useQuery({ queryKey: ['categories'], queryFn: fetchCategories })

  return (
    <div className="feed-layout">
      <section className="feed-column">
        <form className="search-bar" onSubmit={(event) => event.preventDefault()}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search creators…" />
          <select value={category} onChange={(event) => setCategory(event.target.value)} aria-label="Filter by category">
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
        <h2 className="discover-heading">Explore categories</h2>
        {categories.map((item) => <button className="btn btn--ghost" key={item.id} onClick={() => setCategory(item.slug)}>{item.name}</button>)}
      </aside>
    </div>
  )
}
