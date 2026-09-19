<template>
  <header class="header-bar">
    <div class="header-left">
      <button class="menu-toggle" type="button" aria-label="打开导航菜单" @click="emit('toggle-menu')">
        <MenuIcon :size="22" />
      </button>
      <div class="emblem">
        <svg viewBox="0 0 100 100" class="emblem-svg">
          <defs>
            <linearGradient id="emblemGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#FFD700" />
              <stop offset="100%" stop-color="#FF8C00" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="45" fill="none" stroke="url(#emblemGradient)" stroke-width="3" />
          <path d="M20,70 L20,55 L35,55 L35,70 Z" fill="url(#emblemGradient)" />
          <path d="M40,70 L40,50 L60,50 L60,70 Z" fill="url(#emblemGradient)" opacity="0.9" />
          <path d="M65,70 L65,55 L80,55 L80,70 Z" fill="url(#emblemGradient)" />
          <path d="M48,40 L48,30 L52,30 L52,40 Z" fill="url(#emblemGradient)" />
          <circle cx="50" cy="28" r="3" fill="url(#emblemGradient)" />
        </svg>
      </div>
      <div class="title-block">
        <h1 class="main-title">智慧政务数据分析平台</h1>
        <p class="sub-title">数据赋能政务 · 智慧服务民生</p>
      </div>
    </div>

    <div class="header-right">
      <div class="weather-widget">
        <Database :size="18" color="#FFD700" />
        <span>NYC 311</span>
        <span class="weather-status">公开数据</span>
      </div>
      <div class="datetime-widget">
        <span class="date">{{ currentDate }}</span>
        <span class="time">{{ currentTime }}</span>
      </div>
      <el-popover placement="bottom" :width="300" trigger="click">
        <template #reference>
          <el-badge :value="notificationCount" :max="9" :hidden="notificationCount === 0" class="notification-badge">
            <button class="icon-btn" type="button" aria-label="通知">
              <BellIcon :size="18" />
            </button>
          </el-badge>
        </template>
        <div class="notice-pop">{{ noticeText }}</div>
      </el-popover>
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-profile">
          <el-avatar :size="36" :class="['profile-avatar', { admin: auth.isAdmin }]">
            <UserRoundIcon v-if="auth.isAdmin" :size="20" />
            <BuildingIcon v-else-if="auth.isStaff" :size="20" />
            <UserRoundIcon v-else :size="20" />
          </el-avatar>
          <div class="user-info">
            <span class="username">{{ displayName }}</span>
            <span class="role">{{ displayRole }}</span>
          </div>
          <ChevronDownIcon :size="14" />
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="settings">系统设置（演示）</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { auth } from '@/auth'
import { api } from '@/api'
import {
  Bell as BellIcon,
  ChevronDown as ChevronDownIcon,
  Database,
  Menu as MenuIcon,
  Building2 as BuildingIcon,
  UserRound as UserRoundIcon
} from 'lucide-vue-next'

const emit = defineEmits(['toggle-menu'])

const router = useRouter()
const notificationCount = ref(0)
const currentTime = ref('')
const currentDate = ref('')
let timer = null

const displayName = computed(() => auth.name)
const displayRole = computed(() => {
  if (auth.isAdmin || !auth.user) return '超级管理员 · 紧急介入'
  if (auth.isStaff) return auth.department || '部门人员'
  return '群众用户'
})
const noticeText = computed(() => {
  if (auth.isAdmin) return `${notificationCount.value} 条紧急工单待介入`
  if (auth.isStaff) return `${notificationCount.value} 条本部门工单待处理`
  return '暂无待处理事项'
})

function updateDateTime() {
  const now = new Date()
  const p = (n) => String(n).padStart(2, '0')
  currentDate.value = `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`
  currentTime.value = `${p(now.getHours())}:${p(now.getMinutes())}:${p(now.getSeconds())}`
}

function handleCommand(command) {
  if (command === 'logout') {
    auth.clear()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'settings') {
    router.push('/settings')
  }
}

onMounted(async () => {
  updateDateTime()
  timer = setInterval(updateDateTime, 1000)
  if (auth.isAdmin || auth.isStaff) {
    try {
      const data = await api.workOrders({ limit: 1000 })
      const pending = auth.isAdmin
        ? data.filter((item) => item.priority === '紧急' && item.status !== '已办结')
        : data.filter((item) => item.status !== '已办结')
      notificationCount.value = Math.min(pending.length, 99)
    } catch {
      notificationCount.value = 0
    }
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  width: 100%;
  height: 100%;
  min-width: 0;
  padding: 0 24px;
  box-sizing: border-box;
  overflow: visible;
  background: linear-gradient(100deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 95, 0.78) 100%);
}

.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 9px;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  gap: 14px;
  min-width: 0;
}

.emblem {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(255, 215, 0, 0.55);
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.emblem-svg {
  width: 34px;
  height: 34px;
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.main-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
  white-space: nowrap;
  line-height: 1.2;
}

.sub-title {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
  white-space: nowrap;
  letter-spacing: 1px;
}

.header-right {
  gap: 16px;
  margin-left: auto;
}

.weather-widget,
.user-profile,
.icon-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
}

.weather-widget {
  padding: 7px 12px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.weather-status {
  font-weight: 500;
  opacity: 0.95;
}

.datetime-widget {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: #fff;
  line-height: 1.25;
  white-space: nowrap;
}

.date {
  font-size: 12px;
  opacity: 0.92;
}

.time {
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.icon-btn {
  padding: 8px;
  cursor: pointer;
  color: #fff;
}

.user-profile {
  padding: 4px 10px 4px 4px;
  cursor: pointer;
}

.profile-avatar {
  color: #dbeafe;
  background: linear-gradient(145deg, #2563eb, #1e3a8a);
  border: 1px solid rgba(255, 255, 255, 0.36);
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.28);
}

.profile-avatar.admin {
  color: #eff6ff;
  background: linear-gradient(145deg, #3b82f6, #1e40af);
  border-color: rgba(219, 234, 254, 0.6);
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.username {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.role {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
}

.notice-pop {
  font-size: 13px;
  color: #303133;
}

:deep(.el-badge__content) {
  background: #ff3b30;
  border: none;
}

@media (max-width: 1100px) {
  .main-title {
    font-size: 18px;
    letter-spacing: 1px;
  }
  .sub-title {
    font-size: 11px;
  }
  .header-bar {
    padding: 0 14px;
    gap: 12px;
  }
}

@media (max-width: 900px) {
  .menu-toggle { display: inline-flex; }
  .header-bar { padding: 0 12px; }
  .emblem { width: 40px; height: 40px; }
  .emblem-svg { width: 29px; height: 29px; }
  .weather-widget, .datetime-widget, .sub-title, .user-info { display: none; }
  .header-right { gap: 8px; }
  .user-profile { padding: 3px; border: 0; background: transparent; }
  .user-profile > :last-child { display: none; }
}

@media (max-width: 520px) {
  .main-title { font-size: 15px; letter-spacing: 0; }
  .header-left { gap: 8px; }
  .emblem { display: none; }
  .icon-btn { padding: 7px; }
}
</style>
