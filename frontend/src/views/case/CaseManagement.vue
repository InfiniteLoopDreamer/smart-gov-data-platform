<template>
  <div class="page">
    <el-alert
      :title="auth.isAdmin ? '超级管理员模式：仅紧急工单可执行跨部门改派' : `部门工作台：${auth.department}`"
      :type="auth.isAdmin ? 'warning' : 'info'"
      :closable="false"
      show-icon
      class="role-alert"
    />
    <!-- 概览卡片 -->
    <el-row :gutter="20" class="summary-row">
      <el-col :xs="12" :sm="8" :md="4">
        <div class="summary-card"><div class="s-label">工单总数</div><div class="s-value">{{ summary.total }}</div></div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="summary-card"><div class="s-label">待受理</div><div class="s-value" style="color:#64748B">{{ summaryCount('待受理') }}</div></div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="summary-card"><div class="s-label">在办</div><div class="s-value" style="color:#F59E0B">{{ summary.open }}</div></div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="summary-card"><div class="s-label">已办结</div><div class="s-value" style="color:#10B981">{{ summary.finished }}</div></div>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <div class="summary-card"><div class="s-label">超时工单</div><div class="s-value" style="color:#EF4444">{{ summary.overdue }}</div></div>
      </el-col>
    </el-row>

    <div class="panel-card">
      <!-- 筛选区 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="status" placeholder="全部" clearable style="width: 140px" @change="reload">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="keyword" placeholder="工单编号 / 诉求内容 / 区域" clearable style="width: 240px" @keyup.enter="reload">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">
            <el-icon style="margin-right: 4px"><Search /></el-icon>查询
          </el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 工单表格 -->
      <el-table :data="pagedList" stripe :row-class-name="rowClassName">
        <el-table-column prop="appeal_id" label="工单编号" width="130" />
        <el-table-column prop="content" label="诉求内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="row.priority === '紧急' ? 'danger' : 'info'" effect="light">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="区域" width="120" />
        <el-table-column prop="department" label="办理部门" width="150">
          <template #default="{ row }">{{ row.department || '未分派' }}</template>
        </el-table-column>
        <el-table-column prop="handler" label="办理人" width="100">
          <template #default="{ row }">{{ row.handler || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="light" round>{{ row.status }}</el-tag>
            <el-tag v-if="isOverdue(row)" type="danger" effect="dark" round style="margin-left:4px">超时</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="受理时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="nextAction(row)" type="success" link size="small" @click="handleAction(row)">
              {{ nextAction(row) }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ list.length }} 条</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="list.length"
          layout="sizes, prev, pager, next"
        />
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="工单详情" size="440px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工单编号">{{ current.appeal_id }}</el-descriptions-item>
          <el-descriptions-item label="诉求内容">{{ current.content }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ current.category }}</el-descriptions-item>
          <el-descriptions-item label="原始分类">{{ current.source_category || current.category }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ current.priority }}</el-descriptions-item>
          <el-descriptions-item label="区域">{{ current.region }}</el-descriptions-item>
          <el-descriptions-item label="办理部门">{{ current.department || '未分派' }}</el-descriptions-item>
          <el-descriptions-item label="办理人">{{ current.handler || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
          <el-descriptions-item label="满意度">{{ current.satisfaction ?? '未回访' }}</el-descriptions-item>
          <el-descriptions-item label="受理时间">{{ current.create_time }}</el-descriptions-item>
          <el-descriptions-item label="办结时间">{{ current.finish_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ current.source === 'citizen' ? '群众提交' : '311 热线' }}</el-descriptions-item>
          <el-descriptions-item label="分派方式">{{ current.assignment_mode }}</el-descriptions-item>
          <el-descriptions-item v-if="current.intervention_note" label="介入原因">{{ current.intervention_note }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>

    <!-- 超级管理员只在紧急情况下改派 -->
    <el-dialog v-model="assignVisible" title="紧急介入与改派" width="500px">
      <el-alert title="该操作会留下紧急介入原因，仅用于跨部门协调。" type="warning" :closable="false" style="margin-bottom:16px" />
      <el-form label-width="80px">
        <el-form-item label="改派部门">
          <el-select v-model="assignForm.department" style="width: 100%">
            <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="介入原因">
          <el-input v-model="assignForm.intervention_note" type="textarea" :rows="3" placeholder="请说明紧急风险及跨部门改派原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="danger" @click="submitAssign">确认紧急改派</el-button>
      </template>
    </el-dialog>

    <!-- 办结对话框 -->
    <el-dialog v-model="finishVisible" title="办结工单" width="460px">
      <el-form label-width="80px">
        <el-form-item label="回访满意度">
          <el-rate v-model="finishSatisfaction" :max="5" show-score />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFinish">确认办结</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { auth } from '@/auth'
import { departments } from '@/constants/catalog'

const statuses = ['待受理', '已受理', '已分派', '办理中', '已办结']

const keyword = ref('')
const status = ref('')
const list = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return list.value.slice(start, start + pageSize.value)
})
const summary = ref({ total: 0, open: 0, finished: 0, overdue: 0, status_counts: [] })
const detailVisible = ref(false)
const assignVisible = ref(false)
const finishVisible = ref(false)
const current = ref(null)
const finishSatisfaction = ref(5)

const assignForm = reactive({ department: departments[0], intervention_note: '' })

function summaryCount(s) {
  const item = summary.value.status_counts?.find((i) => i.status === s)
  return item ? item.count : 0
}

async function loadSummary() {
  try {
    summary.value = await api.workOrderSummary({ days: 3 })
  } catch {
    /* 后端未启动 */
  }
}

async function loadList() {
  try {
    const params = { limit: 500 }
    if (status.value) params.status = status.value
    if (keyword.value) params.keyword = keyword.value
    list.value = await api.workOrders(params)
    currentPage.value = 1
  } catch {
    list.value = []
  }
}

function reload() {
  loadList()
  loadSummary()
}

function reset() {
  keyword.value = ''
  status.value = ''
  reload()
}

function nextAction(row) {
  if (auth.isAdmin) {
    return row.priority === '紧急' && row.status !== '已办结' ? '紧急改派' : ''
  }
  const map = { 已分派: '办理', 办理中: '办结' }
  return map[row.status] || ''
}

function isOverdue(row) {
  if (row.status === '已办结') return false
  const t = new Date(row.create_time.replace(' ', 'T'))
  const cutoff = Date.now() - 3 * 86400 * 1000
  return t.getTime() < cutoff
}

function rowClassName({ row }) {
  return isOverdue(row) ? 'overdue-row' : ''
}

function openDetail(row) {
  current.value = row
  detailVisible.value = true
}

function handleAction(row) {
  const action = nextAction(row)
  if (action === '紧急改派') {
    current.value = row
    Object.assign(assignForm, { department: row.department || departments[0], intervention_note: '' })
    assignVisible.value = true
  } else if (action === '办结') {
    current.value = row
    finishSatisfaction.value = 5
    finishVisible.value = true
  } else {
    doAction(row, action, action === '办理' ? { handler: auth.name } : {})
  }
}

async function doAction(row, action, extra = {}) {
  try {
    await api.updateWorkOrder(row.id, { action, ...extra })
    ElMessage.success(`已${action}「${row.appeal_id}」`)
    reload()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || `${action}失败，请检查后端是否启动`)
  }
}

function submitAssign() {
  if (!assignForm.intervention_note.trim()) {
    ElMessage.warning('请填写紧急介入原因')
    return
  }
  doAction(current.value, '紧急改派', {
    department: assignForm.department,
    intervention_note: assignForm.intervention_note
  })
  assignVisible.value = false
}

function submitFinish() {
  doAction(current.value, '办结', { satisfaction: finishSatisfaction.value })
  finishVisible.value = false
}

function statusType(s) {
  const map = {
    待受理: 'info',
    已受理: 'primary',
    已分派: 'warning',
    办理中: 'primary',
    已办结: 'success'
  }
  return map[s] || 'info'
}

onMounted(() => {
  loadSummary()
  loadList()
})
</script>

<style scoped lang="scss">
.summary-row {
  margin-bottom: 20px;
}

.role-alert { margin-bottom: 16px; }

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  color: #64748b;
  font-size: 13px;
}

.summary-card {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

.filter-form {
  margin-bottom: 8px;
}

:deep(.overdue-row) {
  --el-table-tr-bg-color: #fef2f2;
}
</style>
