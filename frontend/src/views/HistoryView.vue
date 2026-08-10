<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

interface HistoryRecord {
  id: number
  image_name: string | null
  image_path: string | null
  product_name: string | null
  target_audience: string | null
  tone_style: string | null
  instruction: string | null
  title: string
  body: string
  tags: string[]
  created_at: string | null
}

const loading = ref(true)
const errorMsg = ref('')
const records = ref<HistoryRecord[]>([])
const router = useRouter()

const loadRecords = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const response = await api.get('/api/records')
    records.value = response.data.records ?? []
  } catch (error: any) {
    if (error?.response?.status === 401) {
      router.push({ path: '/login', query: { redirect: '/history' } })
      return
    }
    errorMsg.value = '加载历史记录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(loadRecords)
</script>

<template>
  <div>
    <header class="page-head">
      <h1>🕘 历史记录</h1>
      <p>这里展示你的所有生成记录：图片、输入参数、生成文案与时间。</p>
    </header>

    <div v-if="loading" class="card loading-box">
      <div class="spinner"></div>
      <p>正在加载历史记录…</p>
    </div>

    <div v-else-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>

    <div v-else-if="records.length === 0" class="card empty-state">
      <div class="empty-icon">🗂️</div>
      <h3>还没有生成记录</h3>
      <p>去工作台生成第一篇文案吧，每次生成都会自动保存到你的账号下。</p>
      <RouterLink to="/workbench" class="btn btn-primary">去生成第一篇</RouterLink>
    </div>

    <div v-else class="history-list">
      <article v-for="record in records" :key="record.id" class="history-card">
        <div class="history-thumb">
          <img v-if="record.image_path" :src="record.image_path" alt="上传图片" />
          <div v-else class="history-thumb-empty">🖼️</div>
        </div>
        <div class="history-info">
          <h3>{{ record.title }}</h3>
          <div v-if="record.product_name || record.target_audience || record.tone_style || record.instruction" class="history-meta">
            <span v-if="record.product_name">产品：{{ record.product_name }}</span>
            <span v-if="record.target_audience">人群：{{ record.target_audience }}</span>
            <span v-if="record.tone_style">风格：{{ record.tone_style }}</span>
            <span v-if="record.instruction">调优：{{ record.instruction }}</span>
          </div>
          <p class="history-body">{{ record.body }}</p>
          <div class="history-foot">
            <span v-for="tag in record.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            <span class="history-time">🕘 {{ record.created_at }}</span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
