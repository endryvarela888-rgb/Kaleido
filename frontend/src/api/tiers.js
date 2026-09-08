import client from './client'

export async function fetchTiers() {
  const { data } = await client.get('/creator/tiers/')
  return data
}

export async function createTier(payload) {
  const { data } = await client.post('/creator/tiers/', payload)
  return data
}

export async function deleteTier(id) {
  await client.delete(`/creator/tiers/${id}/`)
}
