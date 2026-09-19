// 路由配置：管理员=政府端，普通用户=群众端
import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/Layout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/home',
    children: [
      // ---- 政府端（管理员）----
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/dashboard/Home.vue'),
        meta: { title: '政府看板', icon: 'DataAnalysis', roles: ['admin'] }
      },
      {
        path: 'case',
        name: 'CaseManagement',
        component: () => import('@/views/case/CaseManagement.vue'),
        meta: { title: '诉求工单处置', icon: 'Document', roles: ['admin', 'staff'] }
      },
      {
        path: 'supervision',
        name: 'Supervision',
        component: () => import('@/views/supervision/Supervision.vue'),
        meta: { title: '督办考核', icon: 'Warning', roles: ['admin'] }
      },
      {
          path: 'reports',
          name: 'StatisticalReports',
          component: () => import('@/views/reports/StatisticalReports.vue'),
          meta: { title: '统计报表', roles: ['admin'] }
        },
        {
          path: 'overview-total',
          name: 'DataOverview',
          component: () => import('@/views/overview/DataOverview.vue'),
          meta: { title: '数据总览', roles: ['admin'] }
        },
        {
          path: 'overview-trend',
          name: 'TrendAnalysis',
          component: () => import('@/views/overview/TrendAnalysis.vue'),
          meta: { title: '趋势分析', roles: ['admin'] }
        },
        {
          path: 'progress',
          name: 'ProgressQuery',
          component: () => import('@/views/overview/ProgressQuery.vue'),
          meta: { title: '进度查询', roles: ['admin'] }
        },
      {
        path: 'cleaning',
        name: 'DataCleaning',
        component: () => import('@/views/cleaning/DataCleaning.vue'),
        meta: { title: '数据质量', icon: 'Brush', roles: ['admin'] }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/system/UserManagement.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin'] }
      },
      {
        path: 'logs',
        name: 'AuditLog',
        component: () => import('@/views/system/AuditLog.vue'),
        meta: { title: '操作日志', icon: 'Memo', roles: ['admin'] }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/settings/SystemSettings.vue'),
        meta: { title: '系统设置', icon: 'Setting', roles: ['admin'] }
      },
      // ---- 群众端（普通用户）----
      {
        path: 'citizen',
        name: 'CitizenHome',
        component: () => import('@/views/citizen/CitizenHome.vue'),
        meta: { title: '首页', icon: 'HomeFilled', roles: ['user'] }
      },
      {
        path: 'appeal',
        name: 'Appeal',
        component: () => import('@/views/citizen/Appeal.vue'),
        meta: { title: '诉求服务', icon: 'ChatDotRound', roles: ['admin', 'user'] }
      },
      {
        path: 'guide',
        name: 'ServiceGuide',
        component: () => import('@/views/citizen/ServiceGuide.vue'),
        meta: { title: '办事指南', icon: 'Notebook', roles: ['admin', 'staff', 'user'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 各角色的默认首页
const ROLE_HOME = { admin: '/home', staff: '/case', user: '/citizen' }

router.beforeEach((to, _from, next) => {
  if (to.path === '/login') {
    next()
    return
  }
  let token = ''
  let role = 'user'
  try {
    token = localStorage.getItem('sg-token') || ''
    role = JSON.parse(localStorage.getItem('sg-user') || '{}').role || 'user'
  } catch {
    token = ''
  }
  if (!token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  if (to.meta.roles && !to.meta.roles.includes(role)) {
    next({ path: ROLE_HOME[role] || '/home', query: { denied: '1' } })
    return
  }
  next()
})

export default router
