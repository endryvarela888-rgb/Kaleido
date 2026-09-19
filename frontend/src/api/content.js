import client from './client'

export async function fetchFeed({ q = '', category = '' } = {}) {
  const { data } = await client.get('/content/feed/', { params: { q, category } })
  return data
}

export async function fetchCategories() {
  const { data } = await client.get('/content/categories/')
  return data
}

export async function fetchContent(id) {
  const { data } = await client.get(`/content/${id}/`)
  return data
}

export async function toggleLike(id) {
  const { data } = await client.post(`/content/${id}/like/`)
  return data
}

export async function fetchComments(id) {
  const { data } = await client.get(`/content/${id}/comments/`)
  return data
}

export async function createComment(id, body) {
  const { data } = await client.post(`/content/${id}/comments/`, { body })
  return data
}

export async function fetchCreator(id) {
  const { data } = await client.get(`/users/creators/${id}/`)
  return data
}

export async function fetchHistory() {
  const { data } = await client.get('/content/history/')
  return data
}

export async function fetchSaved() {
  const { data } = await client.get('/content/saved/')
  return data
}

export async function toggleSave(id) {
  const { data } = await client.post(`/content/${id}/save/`)
  return data
}

export async function fetchCreatorContent() {
  const { data } = await client.get('/content/creator/content/')
  return data
}

export async function createCreatorContent(payload) {
  const { data } = await client.post('/content/creator/content/', payload, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data
}

export async function deleteCreatorContent(id) {
  await client.delete(`/content/creator/content/${id}/`)
}

export async function updateCreatorContent(id, payload) {
  const { data } = await client.patch(`/content/creator/content/${id}/`, payload)
  return data
}

export async function fetchCreatorCollections() {
  const { data } = await client.get('/content/creator/collections/')
  return data
}

export async function createCreatorCollection(payload) {
  const { data } = await client.post('/content/creator/collections/', payload)
  return data
}

export async function deleteCreatorCollection(id) {
  await client.delete(`/content/creator/collections/${id}/`)
}

export async function updateCreatorCollection(id, payload) {
  const { data } = await client.patch(`/content/creator/collections/${id}/`, payload)
  return data
}

export async function fetchCollection(id) {
  const { data } = await client.get(`/content/collections/${id}/`)
  return data
}
