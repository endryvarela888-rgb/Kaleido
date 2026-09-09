import client from './client'

export async function fetchDiscoverCreators() {
  const { data } = await client.get('/users/creators/discover/')
  return data
}