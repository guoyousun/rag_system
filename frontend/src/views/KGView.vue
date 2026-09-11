<template>
  <div class="page-container kg-page">
    <el-card shadow="never" class="kg-card">
      <template #header>
        <div class="card-head">
          <span>知识图谱可视化（Neo4j 实体关系）</span>
          <div class="head-actions">
            <el-input-number v-model="limit" :min="20" :max="300" :step="20" size="small" />
            <el-button :icon="Refresh" size="small" circle @click="load" />
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart" v-loading="loading"></div>
      <div v-if="!loading && !nodes.length" class="empty-tip">
        图谱为空。请先在「文档管理」上传文档，系统会自动抽取实体与关系构建知识图谱。
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { getGraphOverview } from '../api/chat'

const chartRef = ref()
const limit = ref(80)
const loading = ref(false)
const nodes = ref([])
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
  load()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})

async function load() {
  loading.value = true
  try {
    const data = await getGraphOverview(limit.value)
    nodes.value = data.nodes || []
    render(data)
  } finally {
    loading.value = false
  }
}

function render(data) {
  const nodes = (data.nodes || []).map((n) => ({
    id: n.id,
    name: n.name,
    symbolSize: n.category === 1 ? 36 : 24,
    category: n.category,
    itemStyle: { color: n.category === 1 ? '#f59e0b' : '#2563eb' },
    label: { show: n.category === 1 || n.name.length <= 8 }
  }))
  const links = (data.links || []).map((l) => ({
    source: l.source,
    target: l.target,
    label: { show: false, formatter: l.relation, fontSize: 10 }
  }))
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: {
      data: ['实体', '文档'],
      top: 0,
      textStyle: { fontSize: 12 }
    },
    animationDuration: 800,
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 300, edgeLength: 80, gravity: 0.1 },
        categories: [
          { name: '实体', itemStyle: { color: '#2563eb' } },
          { name: '文档', itemStyle: { color: '#f59e0b' } }
        ],
        data: nodes,
        links,
        emphasis: { focus: 'adjacency', lineStyle: { width: 2 } },
        lineStyle: { color: '#94a3b8', curveness: 0.1, opacity: 0.7 }
      }
    ]
  })
}

function onResize() {
  chart?.resize()
}
</script>

<style scoped>
.kg-page {
  height: 100%;
}
.kg-card {
  height: calc(100vh - 40px);
}
.kg-card :deep(.el-card__body) {
  height: calc(100% - 55px);
  position: relative;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.head-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.chart {
  width: 100%;
  height: 100%;
}
.empty-tip {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
</style>
