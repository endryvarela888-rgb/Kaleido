import client from './client'

export async function checkout(tierId) {
  const { data } = await client.post(`/payments/checkout/${tierId}/`)
  return data
}

export async function fetchStats() {
  const { data } = await client.get('/payments/creator/stats/')
  return data
}

export async function fetchPayouts() {
  const { data } = await client.get('/payments/creator/payouts/')
  return data
}

export async function connectPayouts() {
  const { data } = await client.post('/payments/creator/payouts/connect/')
  return data
}