import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  }
}

function setTokens({ access, refresh }) {
  if (access) localStorage.setItem('access_token', access)
  if (refresh) localStorage.setItem('refresh_token', refresh)
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// Attach the access token to every outgoing request automatically.
client.interceptors.request.use((config) => {
  const { access } = getTokens()
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

// If a 401 comes back, silently refresh the access token once and retry
// the original request — the user never notices their token expired.
let refreshPromise = null

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const { refresh } = getTokens()
      if (!refresh) {
        clearTokens()
        return Promise.reject(error)
      }
      try {
        // If several requests 401 at the same time, they all wait on the
        // SAME refresh call instead of firing a refresh each — avoids a
        // race where multiple refreshes rotate the token out from under
        // each other.
        if (!refreshPromise) {
          refreshPromise = axios
            .post('/api/users/token/refresh/', { refresh })
            .then((res) => {
              setTokens({ access: res.data.access })
              refreshPromise = null
              return res.data.access
            })
            .catch((err) => {
              refreshPromise = null
              throw err
            })
        }
        const newAccess = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${newAccess}`
        return client(originalRequest)
      } catch (refreshError) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export { getTokens, setTokens, clearTokens }
export default client