<template>
  <div class="appeal">
    <el-tabs v-model="activeTab">
      <!-- 我要反映 -->
      <el-tab-pane label="我要反映" name="submit">
        <div class="panel-card form-card">
          <h3 class="panel-title">提交诉求</h3>
          <el-form :model="form" label-width="90px">
            <el-form-item label="诉求分类">
              <el-select v-model="form.category" style="width: 100%">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-form-item label="所在区域">
              <el-select v-model="form.region" style="width: 100%">
                <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
              </el-select>
            </el-form-item>
            <el-form-item label="诉求内容">
              <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请描述您要反映的问题…" />
            </el-form-item>
            <el-form-item label="紧急程度">
              <el-radio-group v-model="form.priority">
                <el-radio value="普通">普通</el-radio>
                <el-radio value="紧急">紧急（存在即时安全风险）</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="submit">提交诉求</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 我的诉求 -->
      <el-tab-pane label="我的诉求" name="list">
        <div class="panel-card">
          <div class="table-header">
            <h3 class="panel-title">我的诉求列表</h3>
            <el-button size="small" @click="loadMy">刷新</el-button>
          </div>
          <el-table :data="myAppeals" stripe>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="content" label="诉求内容" />
            <el-table-column prop="region" label="区域" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" effect="light" round>{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="satisfaction" label="满意度" width="110">
              <template #default="{ row }">
                <span v-if="row.satisfaction != null">{{ row.satisfaction }} 分</span>
                <span v-else class="muted">未回访</span>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="提交时间" width="170" />
          </el-table>
          <el-empty v-if="myAppeals.length === 0" description="暂无诉求记录" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const route = useRoute()
const activeTab = ref(route.query.tab === 'list' ? 'list' : 'submit')
const loading = ref(false)
const myAppeals = ref([])

const categories = ref([])
const regions = ref(['布鲁克林区', '皇后区', '曼哈顿区', '布朗克斯区', '史泰登岛区'])

const form = reactive({
  category: '',
  region: '布鲁克林区',
  content: '',
  priority: '普通'
})

async function submit() {
  if (!form.content.trim()) {
    ElMessage.warning('请填写诉求内容')
    return
  }
  loading.value = true
  try {
    await api.submitAppeal({ ...form })
    ElMessage.success('诉求已提交，我们会尽快处理')
    form.content = ''
    await loadMy()
    activeTab.value = 'list'
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败，请检查后端是否启动')
  } finally {
    loading.value = false
  }
}

async function loadMy() {
  try {
    myAppeals.value = await api.myAppeals()
  } catch {
    myAppeals.value = []
  }
}

function statusType(s) {
  const map = { 已受理: 'primary', 办理中: 'warning', 已办结: 'success' }
  return map[s] || 'info'
}

onMounted(async () => {
  try {
    const cats = await api.serviceCategories()
    categories.value = cats.map((c) => c.name).filter(Boolean)
    if (categories.value.length) form.category = categories.value[0]
    const vols = await api.regionVolume()
    if (vols?.length) {
      regions.value = vols.map((r) => r.name).filter((name) => name && name !== '未指定区域')
    }
  } catch {
    categories.value = ['交通出行', '噪声扰民', '市容环境', '公共秩序', '社会救助', '动物管理']
    form.category = categories.value[0]
  }
  loadMy()
})
</script>

<style scoped lang="scss">
.form-card {
  max-width: 640px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-header .panel-title {
  margin: 0;
}

.muted {
  color: #94a3b8;
}
</style>
