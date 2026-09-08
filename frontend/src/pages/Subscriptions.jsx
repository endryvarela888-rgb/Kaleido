import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchSubscriptions, updateSubscription } from '../api/subscriptions'
import { useAuth } from '../hooks/useAuth'

export default function Subscriptions() {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const { data = [], isLoading, isError } = useQuery({ queryKey: ['subscriptions'], queryFn: fetchSubscriptions, enabled: isAuthenticated })
  const mutation = useMutation({ mutationFn: ({ id, action }) => updateSubscription(id, action), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }) })
  if (!isAuthenticated) return <p className="empty-state"><Link to="/login">Log in</Link> to manage subscriptions.</p>
  if (isLoading) return <p className="empty-state">Loading subscriptions…</p>
  if (isError) return <p className="empty-state">Unable to load subscriptions.</p>
  if (!data.length) return <p className="empty-state">You have no active subscriptions.</p>
  return <section><h1>Your subscriptions</h1>{data.map((subscription) => <article className="content-card__body" key={subscription.id}>
    <h2><Link to={`/profile/${subscription.creator.id}`}>{subscription.creator.display_name}</Link></h2>
    <p>{subscription.tier.name} · ${subscription.tier.price}/month</p>
    <p>Renews {new Date(subscription.current_period_end).toLocaleDateString()}</p>
    <button className="btn btn--ghost" disabled={mutation.isPending} onClick={() => mutation.mutate({ id: subscription.id, action: subscription.cancel_at_period_end ? 'renew' : 'cancel' })}>{subscription.cancel_at_period_end ? 'Resume subscription' : 'Cancel at period end'}</button>
  </article>)}</section>
}
