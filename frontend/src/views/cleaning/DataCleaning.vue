<template>
  <div class="page">
    <el-tabs v-model="activeTab">
      <!-- 质量概览 -->
      <el-tab-pane label="质量概览" name="overview">
        <el-row :gutter="20">
          <el-col v-for="card in summary" :key="card.title" :xs="12" :md="6">
            <div class="panel-card summary-card">
              <div class="summary-title">{{ card.title }}</div>
              <div class="summary-value" :style="{ color: card.color }">{{ card.value }}</div>
            </div>
          </el-col>
        </el-row>

        <!-- 问题清单 -->
        <div class="panel-card table-card">
          <div class="table-header">
            <h3 class="panel-title">数据质量问题清单</h3>
            <el-button type="primary" size="small" @click="refresh">
              <el-icon style="margin-right: 4px"><Refresh /></el-icon>重新检测
            </el-button>
          </div>
          <el-table :data="issues" stripe>
            <el-table-column prop="field" label="字段" width="200" />
            <el-table-column prop="issue_type" label="问题类型" width="130">
              <template #default="{ row }">
                <el-tag :type="issueType(row.issue_type)" effect="light" round>{{ row.issue_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="count" label="问题数量" width="120" />
            <el-table-column prop="detail" label="说明" />
          </el-table>
          <el-empty v-if="issues.length === 0" description="未检测到数据质量问题" />
        </div>

        <!-- 办件量异常 -->
        <div class="panel-card table-card">
          <div class="table-header">
            <h3 class="panel-title">办件量异常日期（Holt-Winters 残差 3-sigma）</h3>
          </div>
          <el-table :data="anomalies" stripe>
            <el-table-column prop="date" label="日期" width="160" />
            <el-table-column prop="count" label="当日办件量" width="140" />
            <el-table-column prop="direction" label="方向" width="120">
              <template #default="{ row }">
                <el-tag :type="row.direction === '偏高' ? 'danger' : 'warning'" effect="light" round>{{ row.direction }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="z_score" label="Z-Score" width="140" />
            <el-table-column label="说明" />
          </el-table>
          <el-empty v-if="anomalies.length === 0" description="近 60 天未检测到异常日期" />
        </div>
      </el-tab-pane>

      <!-- 质检规则 -->
      <el-tab-pane label="质检规则" name="rules">
        <div class="panel-card">
          <h3 class="panel-title">数据质量检测规则</h3>
          <el-table :data="rules" stripe>
            <el-table-column prop="name" label="规则名称" width="220" />
            <el-table-column prop="desc" label="规则说明" />
            <el-table-column prop="enabled" label="启用" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const activeTab = ref('overview')

const summary = ref([
  { title: '数据总量', value: '…', color: '#1E293B' },
  { title: '完整率', value: '…', color: '#10B981' },
  { title: '问题记录', value: '…', color: '#F59E0B' },
  { title: '异常日期', value: '…', color: '#EF4444' }
])

const issues = ref([])
const anomalies = ref([])

async function loadQuality() {
  try {
    const q = await api.quality()
    const problemCount = q.issues.reduce((s, i) => s + i.count, 0)
    summary.value = [
      { title: '数据总量', value: q.total.toLocaleString(), color: '#1E293B' },
      { title: '完整率', value: `${q.completeness}%`, color: '#10B981' },
      { title: '问题记录', value: problemCount.toLocaleString(), color: '#F59E0B' },
      { title: '异常日期', value: `${q.anomalies.length} 个`, color: '#EF4444' }
    ]
    issues.value = q.issues
    anomalies.value = q.anomalies
  } catch {
    /* 后端未启动 */
  }
}

function refresh() {
  loadQuality()
}

function issueType(t) {
  const map = { 缺失: 'warning', 重复: 'primary', 异常: 'danger', 时间逻辑: 'info' }
  return map[t] || 'info'
}

onMounted(loadQuality)

const rules = ref([
  { name: '关键字段缺失检测', desc: '检测办件编号、区域、办理人等关键字段的缺失或未规范值（如 Unspecified）', enabled: true },
  { name: '重复工单检测', desc: '按诉求内容 + 分类 + 区域 + 提交时间识别重复提交', enabled: true },
  { name: '时间逻辑校验', desc: '检查办结时间是否早于受理时间', enabled: true },
  { name: '办件量异常检测', desc: '基于 Holt-Winters 拟合残差的 3-sigma 识别异常日期', enabled: true },
  { name: '分类规范化', desc: '统一诉求分类名称（预留，可接入分类字典）', enabled: false }
])
</script>

<style scoped lang="scss">
.summary-card {
  text-align: center;
  padding: 24px 20px;
}

.summary-title {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
}

.summary-value {
  font-size: 26px;
  font-weight: 700;
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
</style>
