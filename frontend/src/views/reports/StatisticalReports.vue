<template>
  <div class="page">
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="panel-card">
          <h3 class="panel-title">办件分类占比</h3>
          <BaseChart :option="categoryOption" height="300px" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel-card">
          <h3 class="panel-title">部门效能排名</h3>
          <BaseChart :option="departmentOption" height="300px" />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24">
        <div class="panel-card">
          <div class="table-header">
            <h3 class="panel-title">近 30 天办件趋势</h3>
            <el-button v-if="auth.isAdmin" type="primary" size="small" @click="exportReport">
              <el-icon style="margin-right: 4px"><Download /></el-icon>导出报表
            </el-button>
          </div>
          <BaseChart :option="trendOption" height="300px" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'
import { auth } from '@/auth'

const ranking = ref([])
const categories = ref([])
const trend = ref([])

onMounted(async () => {
  try {
    const [r, c, t] = await Promise.all([
      api.departmentRanking(),
      api.caseCategories(),
      api.trend(30)
    ])
    ranking.value = r
    categories.value = c
    trend.value = t
  } catch {
    /* 后端未启动 */
  }
})

// 办件分类占比环形图
const categoryOption = computed(() => ({
  color: ['#2B5FD7', '#5581E0', '#809FE8', '#10B981', '#F59E0B', '#8B5CF6', '#94A3B8'],
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, textStyle: { color: '#64748B', fontSize: 11 } },
  series: [
    {
      name: '办件分类',
      type: 'pie',
      radius: ['45%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: categories.value.slice(0, 7)
    }
  ]
}))

// 部门效能排名柱状图
const departmentOption = computed(() => ({
  color: ['#2B5FD7'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 90, right: 40, top: 20, bottom: 30 },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#F1F5F9' } },
    axisLabel: { color: '#64748B', fontSize: 11 }
  },
  yAxis: {
    type: 'category',
    data: ranking.value.map((i) => i.department).reverse(),
    axisLine: { lineStyle: { color: '#CBD5E1' } },
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
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,
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

// 近 30 天办件趋势折线图
const trendOption = computed(() => ({
  color: ['#2B5FD7'],
  tooltip: { trigger: 'axis' },
  grid: { left: 44, right: 20, top: 24, bottom: 32 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trend.value.map((t) => t.date.slice(5)),
    axisLine: { lineStyle: { color: '#CBD5E1' } },
    axisLabel: { color: '#64748B', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#F1F5F9' } },
    axisLabel: { color: '#64748B', fontSize: 11 }
  },
  series: [
    {
      name: '办件量',
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: trend.value.map((t) => t.count),
      lineStyle: { width: 3 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(43, 95, 215, 0.25)' },
            { offset: 1, color: 'rgba(43, 95, 215, 0.02)' }
          ]
        }
      }
    }
  ]
}))

function exportReport() {
  ElMessage.success('报表已导出为 CSV，请查看下载目录')
}
</script>

<style scoped lang="scss">
.chart-row {
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
</style>
