<template>
  <div class="page">
    <el-row :gutter="16" class="kpi-row">
      <el-col v-for="s in stats" :key="s.label" :xs="12" :md="6">
        <div class="panel-card kpi">
          <div class="kpi-label">{{ s.label }}</div>
          <div class="kpi-value">{{ Number(s.value || 0).toLocaleString('zh-CN') }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <div class="panel-card">
          <h3 class="panel-title">各区办件量（NYC 311）</h3>
          <el-table :data="regions" stripe max-height="420">
            <el-table-column prop="name" label="区域" />
            <el-table-column prop="value" label="办件量" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel-card">
          <h3 class="panel-title">事项类型 TOP</h3>
          <BaseChart :option="pieOption" height="380px" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BaseChart from '@/components/BaseChart.vue'
import { api } from '@/api'
import { dashboardAPI } from '@/api/dashboard'

const stats = ref([])
const regions = ref([])
const categories = ref([])

onMounted(async () => {
  try {
    const [dash, region, cats] = await Promise.all([
      dashboardAPI.getStats(),
      api.regionVolume(),
      api.caseCategories()
    ])
    stats.value = dash.stats || []
    regions.value = region
    categories.value = cats.slice(0, 8)
  } catch (e) {
    console.error(e)
  }
})

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '68%'],
    data: categories.value
  }]
}))
</script>

<style scoped>
.kpi-row { margin-bottom: 16px; }
.kpi-label { color: #909399; font-size: 13px; }
.kpi-value { font-size: 26px; font-weight: 700; margin-top: 6px; }
.panel-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.panel-title { margin: 0 0 12px; font-size: 15px; }
</style>
