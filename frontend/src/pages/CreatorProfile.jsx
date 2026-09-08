import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchCreator } from '../api/content'
import ContentCard from '../components/ContentCard'
import { checkout } from '../api/payments'
import { useAuth } from '../hooks/useAuth'

export default function CreatorProfile() {
  const { id } = useParams()
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({ queryKey: ['creator', id], queryFn: () => fetchCreator(id) })
  if (isLoading) return <p className="empty-state">Loading creator…</p>
  if (isError || !data) return <p className="empty-state">Creator not found.</p>
  const { creator, tiers, content, collections = [], subscription } = data
  const membership = useMutation({
    mutationFn: checkout,
    onSuccess: (result) => {
      if (result.url) window.location.assign(result.url)
      else queryClient.invalidateQueries({ queryKey: ['creator', id] })
    },
  })
  return <section>
    <header className="content-card__body">
      <h1>{creator.display_name}</h1>
      <p>{creator.bio}</p>
      {creator.creator_profile?.category && <p>{creator.creator_profile.category}</p>}
    </header>
    <section>
      <h2>Memberships</h2>
      {tiers.map((tier) => <article key={tier.id} className="content-card__body"><h3>{tier.name} · ${tier.price}/month</h3><p>{tier.description}</p>{subscription?.tier_id === tier.id ? <span>Current plan</span> : <button className="btn btn--primary" disabled={!isAuthenticated || membership.isPending} onClick={() => membership.mutate(tier.id)}>{isAuthenticated ? 'Choose this tier' : 'Log in to subscribe'}</button>}</article>)}
      {membership.isError && <p className="form-error">{membership.error.response?.data?.detail || 'Unable to start checkout.'}</p>}
    </section>
    {!!collections.length && <section><h2>Collections</h2>{collections.map((collection) => <article className="content-card__body" key={collection.id}><h3><Link to={`/collections/${collection.id}`}>{collection.title}</Link></h3><p>{collection.description}</p><small>{collection.item_count} items</small></article>)}</section>}
    <section className="feed-column"><h2>Content</h2>{content.map((item) => <ContentCard key={item.id} item={item} />)}</section>
  </section>
}
