import axios from 'axios'

const client = axios.create({
  baseURL: 'http://127.0.0.1:8000',
})

// v1: token lives in localStorage -- simplest option for a single-machine,
// local-first demo. Trade-off (XSS exposure) is acceptable for now, same
// shortcut spirit as the rest of v1's auth (see backend/auth.py).
const TOKEN_KEY = 'rfp_sentinel_token'

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function login(email, password) {
  const { data } = await client.post('/auth/login', { email, password })
  return data.access_token
}

export async function uploadRfp(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/rfp/upload', form)
  return data
}

export async function getStatus(rfpId) {
  const { data } = await client.get(`/rfp/${rfpId}/status`)
  return data
}

export async function getCriteria(rfpId) {
  const { data } = await client.get(`/rfp/${rfpId}/criteria`)
  return data
}

export async function approveCriteria(rfpId, criteria) {
  const { data } = await client.post(`/rfp/${rfpId}/criteria/approve`, { criteria })
  return data
}

export { TOKEN_KEY }
export default client
