<template>
  <el-container class="layout-container">
    <!-- 左侧深棕红色导航 -->
    <el-aside width="220px" class="layout-aside">
      <SidebarMenu />
    </el-aside>

    <!-- 右侧：顶栏 + 内容区 -->
    <el-container class="layout-body">
      <el-header height="72px" class="layout-header">
        <HeaderBar />
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import SidebarMenu from './SidebarMenu.vue'
import HeaderBar from './HeaderBar.vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout-aside {
  background: #2C1A0E;
  overflow: hidden;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.layout-header {
  overflow: visible;
  background: linear-gradient(90deg, #6B4A28 0%, #8B6238 50%, #7A5530 100%);
  border-bottom: none;
  padding: 0;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10;
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