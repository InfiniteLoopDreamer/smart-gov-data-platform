<template>
  <el-container class="layout-container">
    <div v-if="mobileMenuOpen" class="sidebar-mask" @click="mobileMenuOpen = false"></div>
    <el-aside width="220px" :class="['layout-aside', { open: mobileMenuOpen }]">
      <SidebarMenu @navigate="mobileMenuOpen = false" />
    </el-aside>

    <!-- 右侧：顶栏 + 内容区 -->
    <el-container class="layout-body">
      <el-header height="72px" class="layout-header">
        <HeaderBar @toggle-menu="mobileMenuOpen = !mobileMenuOpen" />
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import SidebarMenu from './SidebarMenu.vue'
import HeaderBar from './HeaderBar.vue'

const mobileMenuOpen = ref(false)
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout-aside {
  background: #0f172a;
  overflow: hidden;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.layout-header {
  overflow: visible;
  background: linear-gradient(100deg, #0f172a 0%, #172554 58%, #1e3a5f 100%);
  border-bottom: none;
  padding: 0;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10;
}

.sidebar-mask {
  display: none;
}

@media (max-width: 900px) {
  .layout-aside {
    position: fixed;
    inset: 0 auto 0 0;
    width: 260px !important;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.22s ease;
  }

  .layout-aside.open {
    transform: translateX(0);
  }

  .sidebar-mask {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 90;
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(2px);
  }

  .layout-header {
    height: 64px !important;
  }

  .layout-main {
    padding: 12px;
  }
}

.layout-body {
  min-width: 0;
  overflow: hidden;
}

.layout-main {
  background: #F3F4F6;
  padding: 16px 18px;
  overflow-y: auto;
  overflow-x: hidden;
}

.layout-main::-webkit-scrollbar {
  width: 8px;
}

.layout-main::-webkit-scrollbar-track {
  background: #F4F4F6;
}

.layout-main::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 4px;
}

.layout-main::-webkit-scrollbar-thumb:hover {
  background: #94A3B8;
}
</style>
