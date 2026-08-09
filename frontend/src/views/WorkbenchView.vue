<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import UploadDropzone from '../components/UploadDropzone.vue'
import NoteCard from '../components/NoteCard.vue'

const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const productName = ref('')
const targetAudience = ref('')
const toneStyle = ref('')
const loading = ref(false)
const aiResult = ref<{ title: string; body: string; tags: string[]; db_saved?: boolean; db_error?: string } | null>(null)
const errorMsg = ref('')
const router = useRouter()

watch(selectedFile, (file) => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = file ? URL.createObjectURL(file) : ''
})

const generate = async () => {
  if (!selectedFile.value) return
  loading.value = true
  aiResult.value = null
  errorMsg.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('product_name', productName.value)
  formData.append('target_audience', targetAudience.value)
  formData.append('tone_style', toneStyle.value)

  try {
    const response = await api.post('/upload', formData)
    if (response.data.status === 'success') {
      aiResult.value = response.data
    } else {
      errorMsg.value = response.data.message || '生成失败'
    }
  } catch (error: any) {
    if (error?.response?.status === 401) {
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      errorMsg.value = '请求超时，请稍后重试'
    } else {
      errorMsg.value = error?.response?.data?.detail || '连接后端失败，请确认后端已启动'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="hero">
    <h1>上传一张图片<br />生成爆款小红书文案</h1>
    <p>基于阿里云 Qwen-VL 多模态大模型，自动识别图片内容，一键生成标题、正文与话题标签。</p>
    <div class="hero-badges">
      <span>✨ 智能识图</span>
      <span>📝 种草文案</span>
      <span># 话题标签</span>
      <span>🎯 自定义风格</span>
    </div>
  </section>

  <div class="workbench-grid">
    <div class="card">
      <h2 class="panel-title">① 上传图片</h2>
      <UploadDropzone v-model="selectedFile" />

      <h2 class="panel-title">② 补充信息（选填）</h2>
      <div class="field">
        <label>产品名称</label>
        <input v-model="productName" class="input" placeholder="如：天翼云B27大楼" />
      </div>
      <div class="field">
        <label>目标人群</label>
        <input v-model="targetAudience" class="input" placeholder="如：科技从业者" />
      </div>
      <div class="field">
        <label>语气风格</label>
        <input v-model="toneStyle" class="input" placeholder="如：活泼、专业、温柔" />
      </div>

      <button class="btn btn-primary btn-block" :disabled="loading || !selectedFile" @click="generate">
        <span v-if="loading" class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></span>
        {{ loading ? 'AI 正在生成…' : '🚀 生成小红书文案' }}
      </button>
    </div>

    <div class="card">
      <h2 class="panel-title">③ 生成结果</h2>

      <div v-if="loading" class="loading-box">
        <div class="spinner"></div>
        <p>AI 正在识别图片并撰写文案，请稍候…</p>
      </div>

      <div v-else-if="aiResult">
        <NoteCard
          :title="aiResult.title"
          :body="aiResult.body"
          :tags="aiResult.tags"
          :image-url="previewUrl"
        />
        <div v-if="aiResult.db_saved === false" class="alert alert-warning" style="margin-top: 14px;">
          ⚠️ 文案已生成，但保存到数据库失败：{{ aiResult.db_error || '未知错误' }}
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">📸</div>
        <h3>等待生成</h3>
        <p>上传一张图片，点击“生成小红书文案”，结果会以小红书笔记卡片的形式展示在这里。</p>
      </div>

      <div v-if="errorMsg" class="alert alert-error" style="margin-top: 14px;">
        {{ errorMsg }}
      </div>
    </div>
  </div>
</template>
