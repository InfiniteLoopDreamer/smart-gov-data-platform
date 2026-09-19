<template>
  <div v-loading="loading" class="home-page">
    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      show-icon
      :closable="false"
    />
    <div class="hero-banner">
      <img class="banner-photo" src="/images/hero-city.jpg" alt="" />
      <div class="banner-overlay"></div>
      <div class="banner-content">
        <h1 class="banner-title">智慧政务 · 数据驱动 · 服务民生</h1>
        <p class="banner-subtitle">让政务更高效 · 让数据更有价值 · 让群众更满意</p>
        <div class="banner-meta">
          <span>演示数据：NYC 311 公开工单</span>
          <span>统计截止：{{ dataAsOf || '-' }}</span>
        </div>
      </div>
    </div>

    <div class="stats-grid">
      <div v-for="(stat, index) in statsData" :key="index" class="stat-card">
        <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }">
          <component :is="stat.icon" :size="26" />
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ formatNumber(stat.value) }}<small>{{ stat.unit || '' }}</small></div>
          <div class="stat-trend" :class="stat.trend == null ? 'neutral' : (stat.trend >= 0 ? 'up' : 'down')">
            <span v-if="stat.trend != null">{{ stat.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}{{ stat.trendUnit || '' }}</span>
            <span v-else>●</span>
            <span class="trend-text">{{ stat.trendLabel || '环比' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="mid-grid">
      <div class="panel">
        <div class="panel-header">
          <h3 class="panel-title">每日办件量趋势</h3>
          <div class="time-tabs">
            <button
              v-for="period in timePeriods"
              :key="period.value"
              :class="['tab-btn', { active: selectedPeriod === period.value }]"
              @click="selectedPeriod = period.value"
            >
              {{ period.label }}
            </button>
          </div>
        </div>
        <BaseChart :option="trendChartOption" height="280px" />
      </div>

      <div class="panel map-panel">
        <div class="panel-header">
          <h3 class="panel-title">政务数据分布地图</h3>
        </div>
        <div class="map-body">
          <div class="map-chart">
            <BaseChart v-if="mapReady" :option="mapChartOption" height="280px" />
          </div>
          <div class="region-list">
            <div v-for="(region, index) in regionData" :key="region.name" class="region-item">
              <span class="dot" :style="{ background: regionColors[index] }"></span>
              <span class="region-name">{{ region.name }}</span>
              <span class="region-value">{{ formatWan(region.value) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h3 class="panel-title">热门服务事项</h3>
          <span class="more-link" @click="go('/case')">更多 &gt;</span>
        </div>
        <div class="service-list">
          <div v-for="(service, index) in hotServices" :key="service.name" class="service-item">
            <span class="rank" :class="'r' + (index + 1)">{{ index + 1 }}</span>
            <span class="service-name">{{ service.name }}</span>
            <span class="service-count">{{ formatNumber(service.count) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-grid">
      <div class="panel pie-panel">
        <div class="panel-header">
          <h3 class="panel-title">事项类型分布</h3>
        </div>
        <div class="pie-wrap">
          <BaseChart :option="pieChartOption" height="260px" />
          <div class="pie-center">
            <div class="pie-label">总计</div>
            <div class="pie-value">{{ formatNumber(totalCount) }}</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h3 class="panel-title">{{ barChartTitle }}</h3>
          <span class="unit-label">单位：件</span>
        </div>
        <BaseChart :option="barChartOption" height="260px" />
      </div>

      <div class="right-stack">
        <div class="panel status-panel">
          <div class="panel-header">
            <h3 class="panel-title">数据运行概况</h3>
          </div>
          <div class="status-list">
            <div v-for="item in systemStatus" :key="item.name" class="status-item">
              <span class="status-name">{{ item.name }}</span>
              <span class="status-ok">● {{ item.status || '正常' }}</span>
            </div>
          </div>
        </div>
        <div class="panel notice-panel">
          <div class="panel-header">
            <h3 class="panel-title">最新通知</h3>
            <span class="more-link" @click="go('/logs')">更多 &gt;</span>
          </div>
          <div class="notice-list">
            <div v-for="notice in notices" :key="notice.title" class="notice-item">
              <span class="notice-title">{{ notice.title }}</span>
              <span class="notice-time">{{ notice.time }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import echarts from '@/charts/echarts'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'
import { Database, CircleCheckBig, Clock3, TriangleAlert } from 'lucide-vue-next'

const router = useRouter()
const loading = ref(true)
const loadError = ref('')
const dataAsOf = ref('')
const selectedPeriod = ref('30')
const mapReady = ref(false)
const totalCount = ref(0)
const trendSeries = ref({
  '7': { x: [], y: [] },
  '30': { x: [], y: [] },
  '365': { x: [], y: [] }
})

const timePeriods = [
  { label: '近7天', value: '7' },
  { label: '近30天', value: '30' },
  { label: '全部周期', value: '365' }
]

const regionColors = ['#E65100', '#F57C00', '#FB8C00', '#FFA726', '#FFB74D', '#FFCC80']

const statsData = ref([
  { label: '累计办件量', value: 0, trend: 0, icon: Database, color: '#E57373', bg: 'rgba(229,115,115,0.16)' },
  { label: '整体办结率', value: 0, unit: '%', trend: 0, icon: CircleCheckBig, color: '#10B981', bg: 'rgba(16,185,129,0.14)' },
  { label: '近7日平均办理时长', value: 0, unit: '小时', trend: 0, icon: Clock3, color: '#F59E0B', bg: 'rgba(245,158,11,0.15)' },
  { label: '当前未办结工单', value: 0, trend: 0, icon: TriangleAlert, color: '#EF4444', bg: 'rgba(239,68,68,0.13)' }
])

const allRegions = ref([])
const regionData = computed(() => allRegions.value.slice(0, 5))
const hotServices = ref([])
const systemStatus = ref([])
const notices = ref([])
const typeDistribution = ref([])
const deptUsage = ref([])
const meaningfulDepartments = computed(() => {
  const total = totalCount.value || 1
  return deptUsage.value.filter((item) => Number(item.value || 0) / total >= 0.01)
})
const barChartTitle = computed(() => meaningfulDepartments.value.length > 1 ? '各部门承办量' : '各行政区办件量')
const barChartData = computed(() => meaningfulDepartments.value.length > 1 ? meaningfulDepartments.value : regionData.value)

function formatNumber(n) {
  return Number(n || 0).toLocaleString('zh-CN')
}

function formatWan(n) {
  if (n >= 10000) return (n / 10000).toFixed(n >= 100000 ? 0 : 1) + '万'
  return formatNumber(n)
}

function go(path) {
  router.push(path)
}

function applyRemote(data) {
  if (!data) return
  totalCount.value = data.total || data.stats?.[0]?.value || 0
  if (data.stats?.length) {
    const icons = [Database, CircleCheckBig, Clock3, TriangleAlert]
    statsData.value = data.stats.map((s, i) => ({
      ...statsData.value[i],
      label: s.label,
      value: s.value,
      trend: Object.prototype.hasOwnProperty.call(s, 'trend') ? s.trend : 0,
      unit: s.unit || '',
      trendLabel: s.trendLabel || '环比',
      trendUnit: s.trendUnit ?? '%',
      icon: icons[i] || Database,
      color: s.color || statsData.value[i]?.color
    }))
  }
  if (data.regionData?.length) allRegions.value = data.regionData
  if (data.hotServices?.length) hotServices.value = data.hotServices.slice(0, 5)
  if (data.typeDistribution?.length) typeDistribution.value = data.typeDistribution
  if (data.deptUsage?.length) deptUsage.value = data.deptUsage
  if (data.notices?.length) notices.value = data.notices
  if (data.systemStatus?.length) systemStatus.value = data.systemStatus
  if (data.trendSeries) trendSeries.value = data.trendSeries
  dataAsOf.value = data.dataAsOf || ''
}

onMounted(async () => {
  try {
    const geo = await fetch('/geo/nyc.json').then((r) => r.json())
    echarts.registerMap('nyc', geo)
    mapReady.value = true
  } catch (e) {
    console.error('纽约地图加载失败', e)
  }
  try {
    applyRemote(await api.dashboardStats())
  } catch (e) {
    loadError.value = '首页数据加载失败，请确认后端服务已启动并使用管理员账号登录。'
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
})

const trendChartOption = computed(() => {
  const pack = trendSeries.value[selectedPeriod.value] || { x: [], y: [] }
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#FF6B00',
      formatter: '{b}<br/>办件量: {c}'
    },
    grid: { left: 16, right: 16, bottom: 8, top: 24, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: pack.x,
      axisLine: { lineStyle: { color: '#E8E8E8' } },
      axisTick: { show: false },
      axisLabel: { color: '#888', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#888', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } }
    },
    series: [{
      data: pack.y,
      type: 'line',
      smooth: 0.45,
      symbol: 'circle',
      symbolSize: 7,
      lineStyle: { color: '#FF6B00', width: 3 },
      itemStyle: { color: '#FF6B00', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255,107,0,0.38)' },
            { offset: 1, color: 'rgba(255,107,0,0.02)' }
          ]
        }
      }
    }]
  }
})

const mapChartOption = computed(() => {
  const maxVal = Math.max(...allRegions.value.map((r) => r.value || 0), 1)
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${p.name}<br/>${formatNumber(p.value || 0)}`
    },
    visualMap: {
      show: false,
      min: 0,
      max: maxVal,
      inRange: { color: ['#FFF3E0', '#FFCC80', '#FF9800', '#E65100'] }
    },
    series: [{
      type: 'map',
      map: 'nyc',
      roam: false,
      zoom: 1.1,
      selectedMode: false,
      data: allRegions.value,
      itemStyle: { borderColor: '#fff', borderWidth: 1, areaColor: '#FFE0B2' },
      emphasis: { itemStyle: { areaColor: '#FF6B00' }, label: { show: true } },
      label: { show: false }
    }]
  }
})

const pieChartOption = computed(() => {
  const colors = ['#FF6B00', '#2B5FD7', '#10B981', '#F59E0B', '#8B5CF6', '#94A3B8']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'middle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      textStyle: { fontSize: 12, color: '#666' },
      formatter: (name) => {
        const item = typeDistribution.value.find((d) => d.name === name)
        return `${name}  ${item ? item.percent : 0}%`
      }
    },
    series: [{
      type: 'pie',
      radius: ['52%', '74%'],
      center: ['34%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      labelLine: { show: false },
      data: typeDistribution.value.map((t, i) => ({
        value: t.value,
        name: t.name,
        itemStyle: { color: colors[i] }
      }))
    }]
  }
})

const barChartOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: '{b}<br/>办件量: {c}' },
  grid: { left: 12, right: 12, bottom: 8, top: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: barChartData.value.map((d) => d.name),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#E8E8E8' } },
    axisLabel: { color: '#666', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#888', fontSize: 11 },
    splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } }
  },
  series: [{
    type: 'bar',
    barWidth: '42%',
    data: barChartData.value.map((d) => d.value),
    itemStyle: {
      borderRadius: [5, 5, 0, 0],
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#FF6B00' },
          { offset: 1, color: '#FFC078' }
        ]
      }
    }
  }]
}))
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-banner {
  position: relative;
  height: clamp(220px, 14vw, 280px);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(80, 40, 10, 0.18);
}

.banner-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 52%;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(40, 22, 8, 0.55) 0%, rgba(90, 45, 12, 0.28) 55%, rgba(20, 12, 6, 0.45) 100%);
}

.banner-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.banner-title {
  margin: 0 0 10px;
  font-size: 34px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 6px;
  text-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
}

.banner-subtitle {
  margin: 0;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: 3px;
}

.banner-meta {
  display: flex;
  gap: 18px;
  margin-top: 14px;
  padding: 5px 12px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(30, 18, 8, 0.25);
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-value small {
  margin-left: 4px;
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.stat-trend {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 600;
}

.stat-trend.up { color: #67C23A; }
.stat-trend.down { color: #F56C6C; }
.stat-trend.neutral { color: #F59E0B; }
.trend-text { color: #909399; font-weight: 400; margin-left: 6px; }

.mid-grid {
  display: grid;
  grid-template-columns: 1.15fr 1.05fr 0.78fr;
  gap: 16px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1.1fr 0.85fr;
  gap: 16px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  min-width: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 650;
  color: #303133;
  padding-left: 10px;
  border-left: 3px solid #FF6B00;
}

.time-tabs { display: flex; gap: 8px; }

.tab-btn {
  padding: 4px 12px;
  border: 1px solid #E6E6E6;
  border-radius: 4px;
  background: #fff;
  color: #606266;
  font-size: 12px;
  cursor: pointer;
}

.tab-btn.active {
  background: linear-gradient(135deg, #FF6B00, #FF9F43);
  border-color: #FF6B00;
  color: #fff;
}

.map-body {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 8px;
  align-items: stretch;
}

.region-list {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 8px 0;
}

.region-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.region-name { flex: 1; color: #606266; }
.region-value { font-weight: 600; color: #303133; font-variant-numeric: tabular-nums; }

.more-link { font-size: 12px; color: #409EFF; cursor: pointer; }
.unit-label { font-size: 12px; color: #909399; }

.service-list, .status-list, .notice-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.service-item, .status-item, .notice-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rank {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  background: #E8E8E8;
  color: #909399;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank.r1 { background: #F56C6C; color: #fff; }
.rank.r2 { background: #E6A23C; color: #fff; }
.rank.r3 { background: #F7BA2A; color: #fff; }

.service-name, .status-name, .notice-title {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-count { font-size: 13px; font-weight: 600; color: #303133; }

.status-ok { color: #67C23A; font-size: 12px; font-weight: 600; white-space: nowrap; }

.right-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.status-panel { flex: 0 0 auto; }
.notice-panel { flex: 1; }

.notice-time { font-size: 12px; color: #C0C4CC; flex-shrink: 0; }

.pie-wrap { position: relative; }
.pie-center {
  position: absolute;
  top: 50%;
  left: 34%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
.pie-label { font-size: 12px; color: #909399; }
.pie-value { font-size: 16px; font-weight: 700; color: #303133; }

@media (max-width: 1400px) {
  .mid-grid, .bottom-grid { grid-template-columns: 1fr 1fr; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 900px) {
  .mid-grid, .bottom-grid, .stats-grid, .map-body { grid-template-columns: 1fr; }
  .banner-title { font-size: 22px; letter-spacing: 2px; }
  .banner-meta { flex-direction: column; gap: 2px; border-radius: 8px; }
  .hero-banner { height: 220px; }
  .stat-card { padding: 16px; }
  .panel { padding: 14px; }
}

@media (max-width: 520px) {
  .home-page { gap: 12px; }
  .banner-title { font-size: 20px; line-height: 1.35; }
  .hero-banner { height: 210px; }
  .banner-subtitle { font-size: 12px; letter-spacing: 1px; }
  .banner-meta { margin-top: 10px; font-size: 11px; }
  .stat-icon { width: 48px; height: 48px; }
  .stat-value { font-size: 24px; }
  .panel-header { align-items: flex-start; gap: 10px; }
  .time-tabs { gap: 4px; }
  .tab-btn { padding: 4px 8px; }
}
</style>
