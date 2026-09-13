<template>
  <div class="page">
    <div class="panel-card">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="status" clearable placeholder="全部" style="width: 140px" @change="load">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="region" clearable placeholder="全部" style="width: 160px" @change="load">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="list" stripe>
        <el-table-column prop="case_id" label="办件编号" width="140" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="item_type" label="事项" width="140" />
        <el-table-column prop="region" label="区域" width="120" />
        <el-table-column prop="department" label="部门" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="submit_time" label="提交时间" width="170" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const status = ref('')
const region = ref('')
const list = ref([])
const regions = ref(['布鲁克林区', '皇后区', '曼哈顿区', '布朗克斯区', '史泰登岛区'])
const statuses = ['已办结', '办理中', '待审批']

async function load() {
  const params = { limit: 100 }
  if (status.value) params.status = status.value
  if (region.value) params.region = region.value
  list.value = await api.cases(params)
}

onMounted(async () => {
  try {
    const vols = await api.regionVolume()
    if (vols?.length) regions.value = vols.map((r) => r.name)
    await load()
  } catch (e) {
    console.error(e)
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
</style>
