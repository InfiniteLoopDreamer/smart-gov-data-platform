<template>
  <div class="page">
    <div class="panel-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="live-badge" :class="{ paused: !live }">
            <span class="live-dot"></span>{{ live ? '实时' : '已暂停' }}
          </span>
          <el-button size="small" @click="toggleLive">
            {{ live ? '暂停' : '恢复' }}
          </el-button>
          <el-select v-model="levelFilter" placeholder="日志级别" clearable style="width: 140px">
            <el-option v-for="l in levels" :key="l" :label="l" :value="l" />
          </el-select>
          <el-input
            v-model="keyword"
            placeholder="搜索用户 / 操作"
            clearable
            style="width: 200px; margin-left: 12px"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <el-button type="primary" plain @click="refresh">
          <el-icon style="margin-right: 4px"><Refresh /></el-icon>刷新
        </el-button>
      </div>

      <!-- 日志表格（最新在前） -->
      <el-table :data="pagedLogs" stripe height="520">
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="user" label="用户" width="120" />
        <el-table-column prop="module" label="模块" width="130" />
        <el-table-column prop="action" label="操作" width="160" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)" effect="dark" round>{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="来源 IP" />
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        class="pagination"
        background
        layout="total, prev, pager, next"
        :total="filteredLogs.length"
        :page-size="pageSize"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '@/api'

const levels = ['INFO', 'WARN', 'ERROR']

const keyword = ref('')
const levelFilter = ref('')
const live = ref(true)
let timer = null

// 日志列表（从后端拉取，定时轮询模拟实时）
const logs = ref([])

async function fetchLogs() {
  try {
    const real = await api.logs({ limit: 100 })
    logs.value = real.map((l) => ({
      id: l.log_id,
      user: l.user,
      module: l.module,
      action: l.operation,
      level: l.level,
      ip: l.ip_address,
      time: l.op_time
    }))
  } catch {
    /* 后端未启动时保持空列表 */
  }
}

function start() {
  timer = setInterval(fetchLogs, 5000)
}

function stop() {
  if (timer) clearInterval(timer)
  timer = null
}

function toggleLive() {
  live.value = !live.value
  live.value ? start() : stop()
}

onMounted(() => {
  fetchLogs()
  start()
})
onBeforeUnmount(stop)

const filteredLogs = computed(() => {
  return logs.value.filter((log) => {
    const matchKeyword =
      !keyword.value || log.user.includes(keyword.value) || log.action.includes(keyword.value)
    const matchLevel = !levelFilter.value || log.level === levelFilter.value
    return matchKeyword && matchLevel
  })
})

const currentPage = ref(1)
const pageSize = 10

const pagedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredLogs.value.slice(start, start + pageSize)
})

function levelType(level) {
  const map = { INFO: 'primary', WARN: 'warning', ERROR: 'danger' }
  return map[level] || 'info'
}

function refresh() {
  keyword.value = ''
  levelFilter.value = ''
  currentPage.value = 1
}
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #10b981;
}

.live-badge.paused {
  color: #94a3b8;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: pulse 1.6s ease-in-out infinite;
}

.live-badge.paused .live-dot {
  background: #94a3b8;
  box-shadow: none;
  animation: none;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(0.8);
  }
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
