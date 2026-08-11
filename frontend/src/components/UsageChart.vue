<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useTheme } from '../theme'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  daily: { date: string; count: number }[]
}>()

const chartEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const { theme } = useTheme()

const renderChart = () => {
  if (!chartEl.value) return
  chart ??= echarts.init(chartEl.value)

  const isDark = theme.value === 'dark'
  const axisColor = isDark ? '#7e8696' : '#9ca3af'
  const splitColor = isDark ? '#262a34' : '#ecedf1'

  chart.setOption({
    grid: { left: 44, right: 18, top: 26, bottom: 30 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1d2028' : '#ffffff',
      borderColor: isDark ? '#343947' : '#ecedf1',
      textStyle: { color: isDark ? '#eceff4' : '#1f2329' },
      axisPointer: { type: 'line', lineStyle: { color: splitColor } },
    },
    xAxis: {
      type: 'category',
      data: props.daily.map((item) => item.date),
      boundaryGap: false,
      axisLine: { lineStyle: { color: axisColor } },
      axisTick: { show: false },
      axisLabel: { color: axisColor },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: axisColor },
      splitLine: { lineStyle: { color: splitColor } },
    },
    series: [
      {
        name: '生成次数',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: props.daily.map((item) => item.count),
        lineStyle: { width: 3, color: '#ff2442' },
        itemStyle: { color: '#ff2442', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 36, 66, 0.28)' },
            { offset: 1, color: 'rgba(255, 36, 66, 0.02)' },
          ]),
        },
      },
    ],
  })
}

const handleResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(() => props.daily, renderChart, { deep: true })
watch(theme, () => {
  // 主题切换后等 DOM 样式更新再重绘
  setTimeout(renderChart, 30)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartEl" class="usage-chart"></div>
</template>
