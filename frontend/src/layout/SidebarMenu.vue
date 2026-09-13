<template>
  <div class="sidebar">
    <nav class="sidebar-nav">
      <div v-for="menu in menuItems" :key="menu.index" class="nav-section">
        <div
          v-if="!menu.children"
          :class="['nav-item', { active: isActive(menu) }]"
          @click="handleMenuClick(menu)"
        >
          <component :is="menu.icon" :size="18" class="nav-icon" />
          <span class="nav-text">{{ menu.title }}</span>
          <ChevronRight :size="14" class="nav-arrow" />
        </div>

        <div v-else>
          <div
            :class="['nav-item', { active: isParentActive(menu) || expandedMenus.includes(menu.index) }]"
            @click="toggleSubMenu(menu)"
          >
            <component :is="menu.icon" :size="18" class="nav-icon" />
            <span class="nav-text">{{ menu.title }}</span>
            <ChevronRight
              :size="14"
              class="nav-arrow"
              :class="{ rotated: expandedMenus.includes(menu.index) }"
            />
          </div>
          <div v-show="expandedMenus.includes(menu.index)" class="sub-menu">
            <div
              v-for="child in menu.children"
              :key="child.path"
              :class="['nav-child', { active: route.path === child.path }]"
              @click="handleMenuClick(child)"
            >
              {{ child.title }}
            </div>
          </div>
        </div>
      </div>
    </nav>

    <div class="sidebar-footer" aria-hidden="true">
      <svg viewBox="0 0 240 140" class="palace-svg">
        <defs>
          <linearGradient id="palaceGold" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#E8C36A" stop-opacity="0.55" />
            <stop offset="100%" stop-color="#C48A2B" stop-opacity="0.18" />
          </linearGradient>
        </defs>
        <path
          d="M20 128 L40 108 L70 108 L90 88 L120 88 L150 88 L170 108 L200 108 L220 128"
          fill="none"
          stroke="url(#palaceGold)"
          stroke-width="1.6"
        />
        <path d="M48 128 V112 H72 V128" fill="none" stroke="#D4A017" stroke-opacity="0.35" />
        <path d="M98 128 V96 H142 V128" fill="none" stroke="#D4A017" stroke-opacity="0.45" />
        <path d="M168 128 V112 H192 V128" fill="none" stroke="#D4A017" stroke-opacity="0.35" />
        <path d="M88 88 L120 62 L152 88" fill="none" stroke="#E8C36A" stroke-opacity="0.5" />
        <rect x="112" y="70" width="16" height="18" fill="none" stroke="#E8C36A" stroke-opacity="0.45" />
        <path d="M70 108 H170" stroke="#E8C36A" stroke-opacity="0.25" />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Home,
  BarChart3,
  Building2,
  Database,
  TrendingUp,
  Monitor,
  Settings,
  ChevronRight
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const expandedMenus = ref([])

const menuItems = [
  { title: '首页', icon: Home, path: '/home', index: 'home' },
  {
    title: '数据概览',
    icon: BarChart3,
    index: 'data-overview',
    children: [
      { title: '数据总览', path: '/overview-total' },
      { title: '趋势分析', path: '/overview-trend' }
    ]
  },
  {
    title: '政务服务',
    icon: Building2,
    index: 'gov-service',
    children: [
      { title: '办事指南', path: '/guide' },
      { title: '在线办理', path: '/appeal' },
      { title: '进度查询', path: '/progress' },
      { title: '诉求工单', path: '/case' }
    ]
  },
  {
    title: '数据管理',
    icon: Database,
    index: 'data-manage',
    children: [
      { title: '数据质量', path: '/cleaning' }
    ]
  },
  {
    title: '业务分析',
    icon: TrendingUp,
    index: 'business-analysis',
    children: [
      { title: '统计报表', path: '/reports' },
      { title: '预测分析', path: '/overview-trend' },
      { title: '督办考核', path: '/supervision' }
    ]
  },
  { title: '可视化大屏', icon: Monitor, path: '/visualization', index: 'visualization' },
  {
    title: '系统管理',
    icon: Settings,
    index: 'system-manage',
    children: [
      { title: '用户管理', path: '/users' },
      { title: '操作日志', path: '/logs' }
    ]
  }
]

function isActive(menu) {
  return route.path === menu.path
}

function isParentActive(menu) {
  return menu.children?.some((c) => c.path === route.path)
}

function toggleSubMenu(menu) {
  const idx = expandedMenus.value.indexOf(menu.index)
  if (idx > -1) expandedMenus.value.splice(idx, 1)
  else expandedMenus.value.push(menu.index)
}

function handleMenuClick(menu) {
  if (menu.path) router.push(menu.path)
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(48, 30, 16, 0.88) 0%, rgba(28, 16, 8, 0.92) 100%),
    repeating-linear-gradient(
      90deg,
      #3b2414 0px,
      #4a301c 3px,
      #2a1a0e 6px,
      #3e2716 9px
    );
}

.sidebar::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 120%, rgba(196, 138, 43, 0.18), transparent 55%);
  pointer-events: none;
}

.sidebar-nav {
  flex: 1;
  padding: 18px 12px 8px;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.sidebar-nav::-webkit-scrollbar { width: 0; }

.nav-section { margin-bottom: 6px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  color: rgba(232, 214, 186, 0.78);
  cursor: pointer;
  transition: 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: linear-gradient(90deg, #E0A54A 0%, #C47A22 55%, #B86A18 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(196, 122, 34, 0.35);
}

.nav-icon { flex-shrink: 0; }
.nav-text { flex: 1; font-size: 14px; font-weight: 500; }
.nav-arrow { opacity: 0.55; transition: transform 0.2s; }
.nav-arrow.rotated { transform: rotate(90deg); }

.sub-menu { padding: 4px 0 6px; }

.nav-child {
  padding: 8px 14px 8px 44px;
  color: rgba(232, 214, 186, 0.65);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
}

.nav-child:hover,
.nav-child.active {
  color: #F6D58A;
  background: rgba(255, 255, 255, 0.06);
}

.sidebar-footer {
  height: 150px;
  position: relative;
  z-index: 1;
}

.palace-svg {
  width: 100%;
  height: 100%;
  opacity: 0.9;
}
</style>
