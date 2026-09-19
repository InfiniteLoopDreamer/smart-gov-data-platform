// 认证状态工具：令牌与用户信息存 localStorage，提供统一的读写入口
const TOKEN_KEY = 'sg-token'
const USER_KEY = 'sg-user'

export const auth = {
  get token() {
    return localStorage.getItem(TOKEN_KEY) || ''
  },
  get user() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  },
  get isLoggedIn() {
    return !!this.token
  },
  get role() {
    return this.user?.role || 'user'
  },
  get isAdmin() {
    return this.role === 'admin'
  },
  get isStaff() {
    return this.role === 'staff'
  },
  get department() {
    return this.user?.department || ''
  },
  get name() {
    return this.user?.name || this.user?.username || '用户'
  },
  get username() {
    return this.user?.username || ''
  },
  set(token, user) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
}
