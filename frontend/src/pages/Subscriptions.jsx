import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchSubscriptions, updateSubscription } from '../api/subscriptions'
import { useAuth } from '../hooks/useAuth'

export default function Subscriptions() {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: fetchSubscriptions,
    enabled: isAuthenticated,
  })
  const mutation = useMutation({
    mutationFn: ({ id, action }) => updateSubscription(id, action),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  })

  if (!isAuthenticated) return <p className="empty-state"><Link to="/login">Log in</Link> to manage subscriptions.</p>
  if (isLoading) return <p className="empty-state">Loading subscriptions…</p>
  if (isError) return <p className="empty-state">Unable to load subscriptions.</p>

  return (
    <div className="page-narrow">
      <h1 className="page-heading">Your subscriptions</h1>

      {data.length === 0 ? (
        <p className="empty-state">You have no active subscriptions.</p>
      ) : (
        <div className="subscription-list">
          {data.map((subscription) => {
            const initial = subscription.creator.display_name?.[0]?.toUpperCase() ?? '?'
            const renewDate = new Date(subscription.current_period_end).toLocaleDateString()

            return (
              <article className="subscription-card" key={subscription.id}>
                <Link to={`/profile/${subscription.creator.id}`}>
                  {subscription.creator.avatar ? (
                    <img className="avatar avatar--sm avatar--image" src={subscription.creator.avatar} alt="" />
                  ) : (
                    <span className="avatar avatar--sm">{initial}</span>
                  )}
                </Link>

                <div className="subscription-card__info">
                  <Link to={`/profile/${subscription.creator.id}`} className="subscription-card__creator">
                    {subscription.creator.display_name}
                  </Link>
                  <p className="subscription-card__tier">{subscription.tier.name} · ${subscription.tier.price}/month</p>
                  <p className={`subscription-card__status ${subscription.cancel_at_period_end ? 'subscription-card__status--canceling' : ''}`}>
                    {subscription.cancel_at_period_end ? `Cancels on ${renewDate}` : `Renews ${renewDate}`}
                  </p>
                </div>

                <button
                  className="btn btn--ghost btn--sm"
                  disabled={mutation.isPending}
                  onClick={() => mutation.mutate({
                    id: subscription.id,
                    action: subscription.cancel_at_period_end ? 'renew' : 'cancel',
                  })}
                >
                  {subscription.cancel_at_period_end ? 'Resume' : 'Cancel'}
                </button>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}