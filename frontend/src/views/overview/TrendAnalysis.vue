<template>
  <div class="page">
    <div class="panel-card">
      <div class="table-header">
        <h3 class="panel-title">办件趋势（真实 311 工单）</h3>
        <el-radio-group v-model="days" size="small" @change="loadTrend">
          <el-radio-button :label="7">近 7 天</el-radio-button>
          <el-radio-button :label="30">近 30 天</el-radio-button>
          <el-radio-button :label="90">近 90 天</el-radio-button>
        </el-radio-group>
      </div>
      <BaseChart :option="trendOption" height="320px" />
    </div>
    <div class="panel-card" style="margin-top: 16px">
      <h3 class="panel-title">Holt-Winters 办件量预测</h3>
      <BaseChart :option="forecastOption" height="320px" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'

const days = ref(30)
const trend = ref([])
const forecast = ref(null)

async function loadTrend() {
  trend.value = await api.trend(days.value)
}

onMounted(async () => {
  try {
    await loadTrend()
    forecast.value = await api.forecast({ days_back: 28, days_forward: 7 })
  } catch (e) {
    console.error(e)
  }
})

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 24, right: 16, bottom: 24, top: 24, containLabel: true },
  xAxis: { type: 'category', data: trend.value.map((d) => d.date) },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    smooth: true,
    data: trend.value.map((d) => d.count ?? d.value ?? d.total),
    areaStyle: { opacity: 0.2 },
    lineStyle: { color: '#FF6B00' },
    itemStyle: { color: '#FF6B00' }
  }]
}))

const forecastOption = computed(() => {
  const f = forecast.value
  if (!f) return { xAxis: { data: [] }, yAxis: {}, series: [] }
  const histX = (f.dates || []).map((d) => String(d).slice(0, 10))
  const futX = (f.future_dates || []).map((d) => String(d).slice(0, 10))
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['实际', '预测'] },
    xAxis: { type: 'category', data: [...histX, ...futX] },
    yAxis: { type: 'value' },
    series: [
      { name: '实际', type: 'line', data: [...(f.actual || []), ...Array(futX.length).fill(null)] },
      { name: '预测', type: 'line', data: [...Array(histX.length).fill(null), ...(f.predicted || [])], lineStyle: { type: 'dashed' } }
    ]
  }
})
</script>

<style scoped>
.panel-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.table-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.panel-title { margin: 0; font-size: 15px; }
</style>
