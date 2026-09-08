import client from './client'

export async function fetchSubscriptions() {
  const { data } = await client.get('/subscriptions/')
  return data
}

export async function updateSubscription(id, action) {
  const { data } = await client.post(`/subscriptions/${id}/${action}/`)
  return data
}
