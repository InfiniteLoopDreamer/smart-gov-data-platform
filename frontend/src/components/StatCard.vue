<template>
  <div class="stat-card">
    <div class="stat-left">
      <div class="stat-title">{{ title }}</div>
      <div class="stat-value">
        {{ value }}<span v-if="unit" class="stat-unit">{{ unit }}</span>
      </div>
      <div v-if="trend" class="stat-trend" :class="trendClass">
        {{ trend }}
      </div>
    </div>
    <div class="stat-icon" :style="{ background: iconBg, color }">
      <el-icon :size="24"><component :is="icon" /></el-icon>
    </div>
  </div>
</template>

<script setup>
// 统计卡片：标题 + 数值 + 趋势 + 彩色图标
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#2B5FD7' },
  trend: { type: String, default: '' },
  trendType: { type: String, default: 'up' } // up | down | flat
})

const iconBg = computed(() => `${props.color}1A`) // 主色 10% 透明度背景
const trendClass = computed(() => ({
  'is-up': props.trendType === 'up',
  'is-down': props.trendType === 'down'
}))
</script>

<style scoped lang="scss">
.stat-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.stat-title {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-unit {
  font-size: 14px;
  font-weight: 400;
  color: #64748b;
  margin-left: 4px;
}

.stat-trend {
  font-size: 13px;
  margin-top: 8px;
  color: #64748b;
}

.stat-trend.is-up {
  color: #10b981;
}

.stat-trend.is-down {
  color: #ef4444;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
