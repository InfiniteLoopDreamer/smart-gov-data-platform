<template>
  <div ref="chartRef" :style="{ height }"></div>
</template>

<script setup>
// 通用 ECharts 封装：传入 option 与高度，自动处理初始化 / 自适应 / 销毁
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '320px' }
})

const chartRef = ref(null)
let chart = null

function init() {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    chart.setOption(props.option)
  }
}

function resize() {
  chart && chart.resize()
}

// option 变化时更新图表
watch(
  () => props.option,
  (val) => {
    chart && chart.setOption(val)
  },
  { deep: true }
)

onMounted(() => {
  init()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})
</script>
