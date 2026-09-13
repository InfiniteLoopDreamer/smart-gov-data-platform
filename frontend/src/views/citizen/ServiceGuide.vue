<template>
  <div class="page">
    <div class="panel-card">
      <!-- 搜索与分类 -->
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索事项名称 / 关键词" clearable style="width: 280px">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-radio-group v-model="category" @change="onFilter">
          <el-radio-button label="全部">全部</el-radio-button>
          <el-radio-button v-for="c in categories" :key="c" :label="c">{{ c }}</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 办事指南列表 -->
      <el-empty v-if="filtered.length === 0" description="未找到相关事项" />
      <el-collapse v-else v-model="activeNames" accordion>
        <el-collapse-item v-for="g in filtered" :key="g.title" :name="g.title">
          <template #title>
            <div class="guide-title">
              <el-icon :size="18" color="#2B5FD7"><Document /></el-icon>
              <span class="g-name">{{ g.title }}</span>
              <el-tag size="small" effect="plain">{{ g.category }}</el-tag>
            </div>
          </template>

          <el-descriptions :column="2" border class="guide-desc">
            <el-descriptions-item label="办理部门">{{ g.department }}</el-descriptions-item>
            <el-descriptions-item label="承诺时限">{{ g.limit }}</el-descriptions-item>
            <el-descriptions-item label="办理条件" :span="2">{{ g.condition }}</el-descriptions-item>
          </el-descriptions>

          <div class="guide-section">
            <div class="section-title">所需材料</div>
            <ul class="guide-list">
              <li v-for="m in g.materials" :key="m">{{ m }}</li>
            </ul>
          </div>

          <div class="guide-section">
            <div class="section-title">办理流程</div>
            <el-steps :active="0" align-center>
              <el-step v-for="(p, i) in g.process" :key="p" :title="`第 ${i + 1} 步`" :description="p" />
            </el-steps>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'

const keyword = ref('')
const category = ref('全部')
const activeNames = ref('')
const guides = ref([])

const categories = computed(() => {
  const set = [...new Set(guides.value.map((g) => g.category))]
  return set.slice(0, 10)
})

const filtered = computed(() => {
  return guides.value.filter((g) => {
    const matchKeyword =
      !keyword.value ||
      g.title.includes(keyword.value) ||
      g.department.includes(keyword.value)
    const matchCategory = category.value === '全部' || g.category === category.value
    return matchKeyword && matchCategory
  })
})

function onFilter() {
  activeNames.value = ''
}

onMounted(async () => {
  try {
    guides.value = await api.serviceGuides()
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.guide-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.g-name {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.guide-desc {
  margin-bottom: 16px;
}

.guide-section {
  margin-top: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.guide-list {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.9;
}
</style>
