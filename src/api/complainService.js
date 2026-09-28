import axios from 'axios'
import toast from 'react-hot-toast'

export const USE_MOCK_DATA = false
export const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
const STORE = 'cms_complaints'
const seed = [
  { id: 105, title: 'Street lights not working on Lake Road', description: 'Several lights have been out for over a week, making the road unsafe at night.', category: 'electricity', location: 'Lake Road, Ward 12', image: '', status: 'Progress', created_at: '2025-06-18T09:20:00Z', user_email: 'demo@example.com' },
  { id: 104, title: 'Water leak near the community park', description: 'A pipe is leaking continuously beside the north entrance.', category: 'water', location: 'North Park entrance', image: '', status: 'Complete', created_at: '2025-06-17T15:00:00Z', user_email: 'user@example.com' },
  { id: 103, title: 'Pothole needs repair', description: 'Large pothole in the left lane is causing traffic and damage.', category: 'road', location: 'Central Avenue', image: '', status: 'Pending', created_at: '2025-06-16T11:30:00Z', user_email: 'demo@example.com' },
  { id: 102, title: 'Garbage collection missed', description: 'Household waste has not been collected for three days.', category: 'garbage', location: 'Block C, Green View', image: '', status: 'Pending', created_at: '2025-06-15T08:45:00Z', user_email: 'user@example.com' },
  { id: 101, title: 'Slow internet at public library', description: 'The public Wi-Fi has been unavailable since yesterday.', category: 'internet', location: 'Public Library', image: '', status: 'Complete', created_at: '2025-06-14T12:00:00Z', user_email: 'demo@example.com' },
]
const load = () => { let rows = JSON.parse(localStorage.getItem(STORE) || 'null'); if (!rows) { rows = seed; localStorage.setItem(STORE, JSON.stringify(rows)) } return rows }
const save = rows => localStorage.setItem(STORE, JSON.stringify(rows))
export const api = axios.create({ baseURL: BASE_URL })
// [BACKEND_GAP: RESPONSE_SHAPES] Confirm list endpoints return a bare array (or adapt here if FastAPI wraps results in a `data` field).
api.interceptors.request.use(config => { const token = localStorage.getItem('access_token'); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
api.interceptors.response.use(r => r, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_data')
    localStorage.removeItem('user')
    window.dispatchEvent(new Event('cms:auth-invalid'))
    toast.error('Your session expired. Please sign in again.')
  }
  if (error.response?.status === 403) toast('Admin permission required', { icon: '⚠️' })
  if (error.response?.status === 422) { const detail = error.response.data?.detail; const message = Array.isArray(detail) ? detail.map(e => `${e.loc?.at(-1) || 'Field'}: ${e.msg}`).join(', ') : 'Please check the submitted information.'; toast.error(message) }
  return Promise.reject(error)
})
const mockDelay = () => new Promise(resolve => setTimeout(resolve, 180))
const call = async (request, mock) => USE_MOCK_DATA ? (await mockDelay(), mock()) : (await request()).data
export const complainService = {
  getMe: () => api.get('/me').then(r => r.data),
  register: body => api.post('/create_user', { ...body, role: 'user' }).then(r => r.data),
  createAdmin: body => api.post('/create_user', { ...body, role: 'admin' }).then(r => r.data),
  login: body => api.post('/User_Login', new URLSearchParams({ username: body.email, password: body.password }), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }).then(r => r.data),
  // [BACKEND_GAP: PUBLIC_COMPLAINT_SHAPE] Verify whether GET / returns all public complaint fields used by the cards.
  getPublic: () => call(() => api.get('/'), load),
  getMine: () => call(() => api.get('/ComplainList'), () => load().filter(c => c.user_email === (JSON.parse(localStorage.getItem('user') || '{}').email || 'demo@example.com'))),
  getAll: () => call(() => api.get('/admin/allcomplain'), load),
  search: id => call(() => api.get(`/admin_search_complain/${id}`), () => load().filter(c => String(c.id) === String(id))),
  filter: category => call(() => api.get('/admin_filter_category/', { params: { category } }), () => load().filter(c => c.category === category)),
  create: body => call(() => api.post('/complain_create', body), () => { const rows = load(); const item = { ...body, id: Math.max(0, ...rows.map(c => Number(c.id))) + 1, status: 'Pending', created_at: new Date().toISOString(), user_email: JSON.parse(localStorage.getItem('user') || '{}').email || 'demo@example.com' }; save([item, ...rows]); return item }),
  // [BACKEND_GAP: ADMIN_UPDATE] Confirm this missing CRUD endpoint and request/response contract with the backend developer.
  update: (id, body) => call(() => api.put(`/complain_update/${id}`, body), () => { const rows = load().map(c => String(c.id) === String(id) ? { ...c, ...body } : c); save(rows); return rows.find(c => String(c.id) === String(id)) }),
  // [BACKEND_GAP: ADMIN_DELETE] Confirm this missing CRUD endpoint and its authorization behavior.
  remove: id => call(() => api.delete(`/complain_delete/${id}`), () => { save(load().filter(c => String(c.id) !== String(id))); return { message: 'Deleted' } }),
  setStatus: (id, status) => call(() => api.put(status === 'Complete' ? `/admin_status_complete/${id}` : `/admin_status_progress/${id}`), () => { const rows = load().map(c => String(c.id) === String(id) ? { ...c, status } : c); save(rows); return rows.find(c => String(c.id) === String(id)) }),
  editUser: body => call(() => api.put('/edituser', body), () => { const user = { ...JSON.parse(localStorage.getItem('user') || '{}'), ...body }; localStorage.setItem('user', JSON.stringify(user)); return user }),
  changePassword: body => call(() => api.put('/passwordchange', body), () => ({ message: 'Password updated' })),
  // [BACKEND_GAP: FORGOT_PASSWORD] Add the endpoint and confirm accepted fields and reset flow.
  forgotPassword: body => call(() => api.post('/forgot_password', body), () => ({ message: 'If the account exists, reset instructions are ready.' })),
}
