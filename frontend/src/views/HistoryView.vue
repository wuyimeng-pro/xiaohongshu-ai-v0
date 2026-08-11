<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
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

const detailVisible = ref(false)
const detailRecord = ref<HistoryRecord | null>(null)

const keyword = ref('')
const dateFilter = ref<'all' | 'today' | 'week'>('all')
const dateOptions = [
  { value: 'all', label: '全部时间' },
  { value: 'today', label: '今天' },
  { value: 'week', label: '近 7 天' },
] as const

const pageSize = 6
const currentPage = ref(1)

const matchesDate = (created: string | null) => {
  if (!created || dateFilter.value === 'all') return true
  const date = new Date(created.replace(' ', 'T'))
  const now = new Date()
  if (dateFilter.value === 'today') {
    return date.toDateString() === now.toDateString()
  }
  const sixDaysAgo = new Date(now)
  sixDaysAgo.setDate(now.getDate() - 6)
  return date >= sixDaysAgo
}

const filteredRecords = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return records.value.filter((record) => {
    const haystack = [
      record.title,
      record.body,
      record.tags.join(' '),
      record.product_name,
      record.target_audience,
      record.tone_style,
      record.instruction,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return (!kw || haystack.includes(kw)) && matchesDate(record.created_at)
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredRecords.value.length / pageSize))
)

const pagedRecords = computed(() =>
  filteredRecords.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize)
)

const openDetail = (record: HistoryRecord) => {
  detailRecord.value = record
  detailVisible.value = true
}

const copyDetail = async () => {
  if (!detailRecord.value) return
  const record = detailRecord.value
  const text = `【${record.title}】\n\n${record.body}\n\n${record.tags.join(' ')}`
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    textarea.remove()
  }
  ElMessage.success('完整文案已复制')
}

watch([keyword, dateFilter], () => {
  currentPage.value = 1
})

watch(totalPages, () => {
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
})

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

    <el-empty v-else-if="records.length === 0" description="还没有生成记录">
      <p class="empty-tip">去工作台生成第一篇文案吧，每次生成都会自动保存到你的账号下。</p>
      <RouterLink to="/workbench" class="btn btn-primary">去生成第一篇</RouterLink>
    </el-empty>

    <template v-else>
      <div class="card history-toolbar">
        <div class="search-box">
          <el-input v-model="keyword" placeholder="搜索标题、正文、标签或参数…" clearable>
            <template #prefix><span class="input-emoji">🔍</span></template>
          </el-input>
        </div>
        <div class="filter-tabs">
          <el-radio-group v-model="dateFilter">
            <el-radio-button v-for="option in dateOptions" :key="option.value" :label="option.value">
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
        <span class="history-count">共 {{ filteredRecords.length }} 条</span>
      </div>

      <el-empty v-if="filteredRecords.length === 0" description="没有匹配的记录">
        <p class="empty-tip">换个关键词或时间范围试试，也可以去工作台生成新的文案。</p>
        <RouterLink to="/workbench" class="btn btn-primary">去生成新文案</RouterLink>
      </el-empty>

      <div v-else class="history-list">
        <article
          v-for="record in pagedRecords"
          :key="record.id"
          class="history-card"
          role="button"
          tabindex="0"
          @click="openDetail(record)"
          @keyup.enter="openDetail(record)"
        >
          <div class="history-thumb">
            <img v-if="record.image_path" :src="record.image_path" alt="上传图片" loading="lazy" />
            <div v-else class="history-thumb-empty">🖼️</div>
          </div>
          <div class="history-info">
            <h3 class="history-title">
              {{ record.title }}
              <span class="history-open">查看详情 →</span>
            </h3>
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

      <el-pagination
        v-if="totalPages > 1"
        class="history-pagination"
        background
        layout="prev, pager, next"
        :total="filteredRecords.length"
        :page-size="pageSize"
        v-model:current-page="currentPage"
      />
    </template>

    <el-dialog v-model="detailVisible" :title="detailRecord?.title || '记录详情'" width="min(720px, 92vw)">
      <div v-if="detailRecord" class="history-detail">
        <div class="detail-grid">
          <div class="detail-image">
            <img v-if="detailRecord.image_path" :src="detailRecord.image_path" alt="上传图片" />
            <div v-else class="detail-image-empty">🖼️</div>
          </div>
          <div class="detail-content">
            <div class="detail-params">
              <span v-if="detailRecord.product_name">产品：{{ detailRecord.product_name }}</span>
              <span v-if="detailRecord.target_audience">人群：{{ detailRecord.target_audience }}</span>
              <span v-if="detailRecord.tone_style">风格：{{ detailRecord.tone_style }}</span>
              <span v-if="detailRecord.instruction">调优：{{ detailRecord.instruction }}</span>
            </div>
            <p class="detail-body">{{ detailRecord.body }}</p>
            <div class="note-tags">
              <span v-for="tag in detailRecord.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
            <p class="detail-time">🕘 {{ detailRecord.created_at }}</p>
          </div>
        </div>
        <div class="detail-actions">
          <el-button type="primary" @click="copyDetail">📋 复制完整文案</el-button>
          <RouterLink to="/workbench" class="btn btn-ghost btn-sm">去工作台继续生成</RouterLink>
        </div>
      </div>
    </el-dialog>
  </div>
</template>
