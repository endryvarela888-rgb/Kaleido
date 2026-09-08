import client from './client'

export async function checkout(tierId) {
  const { data } = await client.post(`/payments/checkout/${tierId}/`)
  return data
}
