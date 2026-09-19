// 后端 API 客户端（axios）
// 开发环境走 Vite 代理 → http://127.0.0.1:8001；可用 VITE_API_BASE 覆盖
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE || ''

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000
})

// 请求拦截器：自动携带令牌
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('sg-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 时清除本地登录态并跳转登录页
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('sg-token')
      localStorage.removeItem('sg-user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
    }
    return Promise.reject(err)
  }
)

export const api = {
  // ---- 认证 ----
  async login(username, password) {
    return (await client.post('/api/auth/login', { username, password })).data
  },
  async register(payload) {
    return (await client.post('/api/auth/register', payload)).data
  },
  async me() {
    return (await client.get('/api/auth/me')).data
  },
  async users() {
    return (await client.get('/api/users')).data
  },
  async createUser(payload) {
    return (await client.post('/api/users', payload)).data
  },
  async updateUser(id, payload) {
    return (await client.patch(`/api/users/${id}`, payload)).data
  },
  // ---- 诉求 ----
  async submitAppeal(payload) {
    return (await client.post('/api/appeals', payload)).data
  },
  async myAppeals() {
    return (await client.get('/api/appeals/my')).data
  },
  async appeals(limit = 50) {
    return (await client.get('/api/appeals', { params: { limit } })).data
  },
  async overdue(days = 3) {
    return (await client.get('/api/overdue', { params: { days } })).data
  },
  // ---- 数据 ----
  async health() {
    return (await client.get('/api/health')).data
  },
  async dashboardStats() {
    return (await client.get('/api/dashboard/stats')).data
  },
  async kpi() {
    return (await client.get('/api/kpi')).data
  },
  async trend(days = 7) {
    return (await client.get('/api/trend', { params: { days } })).data
  },
  async topItems(top = 5) {
    return (await client.get('/api/top-items', { params: { top } })).data
  },
  async regionVolume() {
    return (await client.get('/api/region-volume')).data
  },
  async caseCategories() {
    return (await client.get('/api/case-categories')).data
  },
  async serviceCategories() {
    return (await client.get('/api/service-categories')).data
  },
  async departmentRanking() {
    return (await client.get('/api/department-ranking')).data
  },
  async cases(params) {
    return (await client.get('/api/cases', { params })).data
  },
  async logs(params) {
    return (await client.get('/api/logs', { params })).data
  },
  async quality() {
    return (await client.get('/api/quality')).data
  },
  async serviceGuides() {
    return (await client.get('/api/service-guides')).data
  },
  async forecast(params = {}) {
    return (await client.get('/api/forecast', { params })).data
  },
  async anomalies(params = {}) {
    return (await client.get('/api/anomalies', { params })).data
  },
  // ---- 诉求工单处置 ----
  async workOrders(params) {
    return (await client.get('/api/work-orders', { params })).data
  },
  async workOrderSummary(params = {}) {
    return (await client.get('/api/work-orders/summary', { params })).data
  },
  async workOrderOverdue(params = {}) {
    return (await client.get('/api/work-orders/overdue', { params })).data
  },
  async updateWorkOrder(id, payload) {
    return (await client.patch(`/api/work-orders/${id}`, payload)).data
  }
}
