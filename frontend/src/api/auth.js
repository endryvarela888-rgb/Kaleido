import client, { setTokens, clearTokens } from './client'

export async function login(email, password) {
  const { data } = await client.post('/users/token/', { email, password })
  setTokens(data)
  return data
}

export async function signup(payload) {
  const { data } = await client.post('/users/signup/', payload)
  return data
}

export async function fetchMe() {
  const { data } = await client.get('/users/me/')
  return data
}

export function logout() {
  clearTokens()
}

export async function updateMe(payload) {
  const { data } = await client.patch('/users/me/', payload)
  return data
}

export async function becomeCreator() {
  const { data } = await client.post('/users/me/become-creator/')
  return data
}

export async function changePassword(payload) {
  const { data } = await client.post('/users/me/change-password/', payload)
  return data
}

export async function resendActivation(email) {
  const { data } = await client.post('/users/resend-activation/', { email })
  return data
}

export async function activateAccount(uid, token) {
  const { data } = await client.post('/users/activate/', { uid, token })
  // Same shape as login(): the activation endpoint logs the user straight
  // in, so the returned access/refresh pair needs to land in storage too.
  setTokens(data)
  return data
}

export async function requestPasswordReset(email) {
  const { data } = await client.post('/users/password-reset/', { email })
  return data
}

export async function confirmPasswordReset(uid, token, newPassword) {
  const { data } = await client.post('/users/password-reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
  })
  return data
}
