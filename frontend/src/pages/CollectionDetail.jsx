import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchCollection } from '../api/content'
import ContentCard from '../components/ContentCard'

export default function CollectionDetail() {
  const { id } = useParams()
  const { data, isLoading, isError } = useQuery({ queryKey: ['collection', id], queryFn: () => fetchCollection(id) })
  if (isLoading) return <p className="empty-state">Loading collection…</p>
  if (isError || !data) return <p className="empty-state">Collection not found.</p>
  return <section className="feed-column"><header className="content-card__body"><h1>{data.collection.title}</h1><p>{data.collection.description}</p><Link to={`/profile/${data.collection.creator.id}`}>{data.collection.creator.display_name}</Link></header>{data.content.map((item) => <ContentCard key={item.id} item={item} />)}</section>
}
