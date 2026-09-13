<template>
  <div class="supervision">
    <!-- 概览卡片 -->
    <el-row :gutter="20" class="summary-row">
      <el-col :xs="12" :md="6">
        <div class="panel-card summary-card"><div class="s-label">在办工单</div><div class="s-value" style="color:#F59E0B">{{ summary.open }}</div></div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="panel-card summary-card"><div class="s-label">超时工单</div><div class="s-value" style="color:#EF4444">{{ summary.overdue }}</div></div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="panel-card summary-card"><div class="s-label">已办结</div><div class="s-value" style="color:#10B981">{{ summary.finished }}</div></div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="panel-card summary-card"><div class="s-label">参评部门</div><div class="s-value">{{ ranking.length }}</div></div>
      </el-col>
    </el-row>

    <!-- 部门效能排名 -->
    <div class="panel-card">
      <h3 class="panel-title">部门效能排名（按综合得分）</h3>
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <BaseChart :option="rankOption" height="340px" />
        </el-col>
        <el-col :xs="24" :md="12">
          <el-table :data="ranking" stripe size="small" height="340">
            <el-table-column prop="rank" label="排名" width="60" />
            <el-table-column prop="department" label="部门" min-width="140" />
            <el-table-column prop="case_count" label="办结量" width="90" />
            <el-table-column prop="avg_duration" label="平均时长(h)" width="110" />
            <el-table-column prop="avg_satisfaction" label="满意度" width="90" />
            <el-table-column prop="score" label="得分" width="80">
              <template #default="{ row }">
                <b>{{ Math.round(row.score) }}</b>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </div>

    <!-- 超时工单 -->
    <div class="panel-card table-card">
      <div class="table-header">
        <h3 class="panel-title">超时工单（在办且超过 {{ days }} 天未办结）</h3>
        <div>
          <el-input-number v-model="days" :min="1" :max="30" size="small" style="margin-right: 8px" />
          <el-button size="small" @click="loadOverdue">刷新</el-button>
        </div>
      </div>
      <el-table :data="overdue" stripe :row-class-name="() => 'overdue-row'">
        <el-table-column prop="appeal_id" label="工单编号" width="140" />
        <el-table-column prop="content" label="诉求内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="department" label="办理部门" width="160">
          <template #default="{ row }">{{ row.department || '未分派' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag type="danger" effect="dark" round>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="受理时间" width="170" />
      </el-table>
      <el-empty v-if="overdue.length === 0" description="暂无超时工单" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'

const days = ref(3)
const overdue = ref([])
const ranking = ref([])
const summary = ref({ open: 0, overdue: 0, finished: 0 })

async function loadOverdue() {
  try {
    overdue.value = await api.workOrderOverdue({ days: days.value, limit: 100 })
  } catch {
    overdue.value = []
  }
}

async function loadRanking() {
  try {
    ranking.value = await api.departmentRanking()
  } catch {
    ranking.value = []
  }
}

async function loadSummary() {
  try {
    summary.value = await api.workOrderSummary({ days: days.value })
  } catch {
    summary.value = { open: 0, overdue: 0, finished: 0 }
  }
}

const rankOption = computed(() => ({
  color: ['#2B5FD7'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 100, right: 40, top: 20, bottom: 30 },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F5F9' } } },
  yAxis: {
    type: 'category',
    data: ranking.value.map((i) => i.department).reverse(),
    axisLabel: { color: '#64748B', fontSize: 11 }
  },
  series: [
    {
      name: '效能得分',
      type: 'bar',
      barWidth: 14,
      data: ranking.value.map((i) => Math.round(i.score)).reverse(),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#5581E0' },
            { offset: 1, color: '#2B5FD7' }
          ]
        }
      },
      label: { show: true, position: 'right', color: '#64748B', fontSize: 11 }
    }
  ]
}))

onMounted(() => {
  loadOverdue()
  loadRanking()
  loadSummary()
})
</script>

<style scoped lang="scss">
.summary-row {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
  padding: 18px 20px;
}

.s-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.s-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.table-card {
  margin-top: 20px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-header .panel-title {
  margin: 0;
}

:deep(.overdue-row) {
  --el-table-tr-bg-color: #fef2f2;
}
</style>
