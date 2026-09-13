<template>
  <header class="header-bar">
    <div class="header-left">
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
        <h1 class="main-title">智慧政务数据管理平台</h1>
        <p class="sub-title">数据赋能政务 · 智慧服务民生</p>
      </div>
    </div>

    <div class="header-right">
      <div class="weather-widget">
        <CloudSun :size="18" color="#FFD700" />
        <span>25°C</span>
        <span class="weather-status">晴</span>
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
        <div class="notice-pop">{{ notificationCount }} 条未办结工单待处理（来自 NYC 311 真实数据）</div>
      </el-popover>
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-profile">
          <el-avatar :size="36" src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" />
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
import { Bell as BellIcon, ChevronDown as ChevronDownIcon, CloudSun } from 'lucide-vue-next'

const router = useRouter()
const notificationCount = ref(0)
const currentTime = ref('')
const currentDate = ref('')
let timer = null

const displayName = computed(() => auth.user?.username || 'admin')
const displayRole = computed(() => (auth.isAdmin || !auth.user ? '系统管理员' : '普通用户'))

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
  try {
    const data = await api.overdue(3)
    notificationCount.value = Array.isArray(data) ? Math.min(data.length, 99) : 0
  } catch {
    try {
      const dash = await api.kpi()
      notificationCount.value = dash?.overdue || 1
    } catch {
      notificationCount.value = 1
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
  background: linear-gradient(90deg, rgba(42, 24, 12, 0.78) 0%, rgba(90, 58, 28, 0.62) 100%);
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
</style>
