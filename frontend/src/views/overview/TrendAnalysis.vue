<template>
  <div v-loading="loading" class="page">
    <div class="panel-card">
      <div class="table-header">
        <h3 class="panel-title">办件趋势（真实 311 工单）</h3>
        <el-radio-group v-model="days" size="small" @change="loadTrend">
          <el-radio-button :value="7">近 7 天</el-radio-button>
          <el-radio-button :value="30">近 30 天</el-radio-button>
          <el-radio-button :value="90">近 90 天</el-radio-button>
        </el-radio-group>
      </div>
      <BaseChart :option="trendOption" height="320px" />
    </div>
    <div class="panel-card" style="margin-top: 16px">
      <div class="forecast-heading">
        <div>
          <h3 class="panel-title">Holt-Winters 办件量预测</h3>
          <p class="metric-note">
            {{ forecast?.validation?.method || '时间留出集评估' }} · 数据截止 {{ forecast?.data_as_of || '-' }}
          </p>
          <p v-if="forecast?.baseline" class="baseline-note">
            对比 {{ forecast.baseline.method }}（WAPE {{ metric(forecast.baseline.wape, '%') }}）
            <span :class="{ positive: forecast.baseline.improvement_pct > 0 }">
              · 模型{{ forecast.baseline.improvement_pct > 0 ? '提升' : '下降' }}
              {{ metric(Math.abs(forecast.baseline.improvement_pct), '%') }}
            </span>
          </p>
        </div>
        <div class="metric-strip">
          <div><span>MAPE</span><strong>{{ metric(forecast?.mape, '%') }}</strong></div>
          <div><span>WAPE</span><strong>{{ metric(forecast?.wape, '%') }}</strong></div>
          <div><span>MAE</span><strong>{{ metric(forecast?.mae) }}</strong></div>
          <div><span>RMSE</span><strong>{{ metric(forecast?.rmse) }}</strong></div>
          <div><span>较基线</span><strong>{{ signedMetric(forecast?.baseline?.improvement_pct) }}</strong></div>
        </div>
      </div>
      <BaseChart :option="forecastOption" height="320px" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'

const days = ref(30)
const trend = ref([])
const forecast = ref(null)
const loading = ref(false)

function metric(value, suffix = '') {
  return value == null ? '-' : `${Number(value).toFixed(2)}${suffix}`
}

function signedMetric(value) {
  if (value == null) return '-'
  return `${value >= 0 ? '+' : ''}${Number(value).toFixed(2)}%`
}

async function loadTrend() {
  trend.value = await api.trend(days.value)
}

onMounted(async () => {
  loading.value = true
  try {
    await loadTrend()
    forecast.value = await api.forecast({ days_back: 28, days_forward: 7 })
  } catch (e) {
    ElMessage.error('趋势与预测数据加载失败')
  } finally {
    loading.value = false
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
    legend: { data: ['实际', '预测', '参考下界', '参考上界'] },
    xAxis: { type: 'category', data: [...histX, ...futX] },
    yAxis: { type: 'value' },
    series: [
      { name: '实际', type: 'line', data: [...(f.actual || []), ...Array(futX.length).fill(null)] },
      {
        name: '预测',
        type: 'line',
        data: [...Array(Math.max(0, histX.length - 1)).fill(null), f.actual?.at(-1) ?? null, ...(f.predicted || [])],
        lineStyle: { type: 'dashed', width: 2, color: '#2563EB' },
        itemStyle: { color: '#2563EB' }
      },
      {
        name: '参考下界',
        type: 'line',
        symbol: 'none',
        data: [...Array(histX.length).fill(null), ...(f.interval_lower || [])],
        lineStyle: { type: 'dotted', color: '#93C5FD', width: 1 }
      },
      {
        name: '参考上界',
        type: 'line',
        symbol: 'none',
        data: [...Array(histX.length).fill(null), ...(f.interval_upper || [])],
        lineStyle: { type: 'dotted', color: '#93C5FD', width: 1 }
      }
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
.forecast-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.metric-note { margin: 6px 0 0; color: #909399; font-size: 12px; }
.baseline-note { margin: 4px 0 0; color: #64748B; font-size: 12px; }
.baseline-note .positive { color: #16A34A; font-weight: 600; }
.metric-strip { display: flex; gap: 10px; flex-wrap: wrap; }
.metric-strip > div { min-width: 78px; padding: 8px 10px; border-radius: 8px; background: #F5F7FA; }
.metric-strip span { display: block; color: #909399; font-size: 11px; }
.metric-strip strong { color: #303133; font-size: 15px; }
@media (max-width: 900px) { .forecast-heading { flex-direction: column; } }
</style>
