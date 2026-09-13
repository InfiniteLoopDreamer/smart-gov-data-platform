<template>
  <div class="citizen-home">
    <!-- 欢迎横幅 -->
    <div class="welcome panel-card">
      <div class="welcome-title">您好，{{ auth.name }}</div>
      <div class="welcome-sub">欢迎使用政务服务 · 您的诉求我们用心办</div>
    </div>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-row">
      <el-col :xs="24" :sm="8">
        <div class="quick-card" @click="router.push('/appeal?tab=submit')">
          <el-icon :size="28" color="#2B5FD7"><EditPen /></el-icon>
          <div>
            <div class="q-title">我要反映</div>
            <div class="q-sub">提交您的诉求与建议</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="quick-card" @click="router.push('/appeal?tab=list')">
          <el-icon :size="28" color="#10B981"><List /></el-icon>
          <div>
            <div class="q-title">我的诉求</div>
            <div class="q-sub">查询办理进度</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="quick-card" @click="router.push('/guide')">
          <el-icon :size="28" color="#F59E0B"><Service /></el-icon>
          <div>
            <div class="q-title">办事指南</div>
            <div class="q-sub">常见事项办理指引</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 我的诉求概览 -->
    <div class="panel-card">
      <div class="table-header">
        <h3 class="panel-title">我的诉求</h3>
        <el-button type="primary" size="small" @click="router.push('/appeal?tab=list')">查看全部</el-button>
      </div>
      <el-table :data="appeals" stripe>
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="content" label="诉求内容" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag type="primary" effect="light" round>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="提交时间" width="170" />
      </el-table>
      <el-empty v-if="appeals.length === 0" description="暂无诉求，点击「我要反映」提交第一条" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { auth } from '@/auth'

const router = useRouter()
const appeals = ref([])

onMounted(async () => {
  try {
    appeals.value = await api.myAppeals()
  } catch {
    appeals.value = []
  }
})
</script>

<style scoped lang="scss">
.welcome {
  background: linear-gradient(120deg, #2b5fd7 0%, #1a2b4c 100%);
  border: none;
  color: #fff;
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
}

.welcome-sub {
  font-size: 14px;
  color: #c7d2fe;
  margin-top: 6px;
}

.quick-row {
  margin: 20px 0;
}

.quick-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.quick-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.q-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.q-sub {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-header .panel-title {
  margin: 0;
}
</style>
