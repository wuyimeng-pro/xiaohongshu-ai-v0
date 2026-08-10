<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api, { streamRequest } from '../api'
import UploadDropzone from '../components/UploadDropzone.vue'
import NoteCard from '../components/NoteCard.vue'

const selectedFile = ref<File | null>(null)
const inputMode = ref<'file' | 'url'>('file')
const imageUrl = ref('')
const selectedFileUrl = ref('')
const previewUrl = computed(() =>
  inputMode.value === 'url' ? imageUrl.value.trim() : selectedFileUrl.value
)
const productName = ref('')
const targetAudience = ref('')
const toneStyle = ref('')
const tonePresets = ['活泼', '专业', '温柔', '文艺', '幽默', '简约']
const loading = ref(false)
const streamingEnabled = ref(true)
const streaming = ref(false)
const streamText = ref('')
const refining = ref(false)
const aiResult = ref<{ id?: number; title: string; body: string; tags: string[]; db_saved?: boolean; db_error?: string } | null>(null)
const versions = ref<{ id: number; title: string; body: string; tags: string[] }[] | null>(null)
const currentVersion = ref(0)
const errorMsg = ref('')
const router = useRouter()

watch(selectedFile, (file) => {
  if (selectedFileUrl.value) URL.revokeObjectURL(selectedFileUrl.value)
  selectedFileUrl.value = file ? URL.createObjectURL(file) : ''
})

const generate = async () => {
  if (inputMode.value === 'file' && !selectedFile.value) return
  if (inputMode.value === 'url' && !imageUrl.value.trim()) return
  loading.value = true
  streaming.value = streamingEnabled.value
  streamText.value = ''
  aiResult.value = null
  versions.value = null
  currentVersion.value = 0
  errorMsg.value = ''

  try {
    if (streamingEnabled.value) {
      const onDelta = (text: string) => {
        streamText.value += text
      }
      let result
      if (inputMode.value === 'file') {
        const formData = new FormData()
        formData.append('file', selectedFile.value!)
        formData.append('product_name', productName.value)
        formData.append('target_audience', targetAudience.value)
        formData.append('tone_style', toneStyle.value)
        result = await streamRequest('/api/stream-upload', { formData }, onDelta)
      } else {
        result = await streamRequest(
          '/api/stream',
          {
            body: {
              url: imageUrl.value.trim(),
              product_name: productName.value,
              target_audience: targetAudience.value,
              tone_style: toneStyle.value,
            },
          },
          onDelta
        )
      }
      aiResult.value = {
        id: result.id,
        title: result.title,
        body: result.body,
        tags: result.tags ?? [],
        db_saved: result.db_saved,
      }
      versions.value = null
      currentVersion.value = 0
    } else {
      let response
      if (inputMode.value === 'file') {
        const formData = new FormData()
        formData.append('file', selectedFile.value!)
        formData.append('product_name', productName.value)
        formData.append('target_audience', targetAudience.value)
        formData.append('tone_style', toneStyle.value)
        response = await api.post('/upload', formData)
      } else {
        response = await api.post('/api/upload-by-url', {
          url: imageUrl.value.trim(),
          product_name: productName.value,
          target_audience: targetAudience.value,
          tone_style: toneStyle.value,
        })
      }
      if (response.data.status === 'success') {
        aiResult.value = response.data
      } else {
        errorMsg.value = response.data.message || '生成失败'
      }
    }
  } catch (error: any) {
    if (error?.response?.status === 401) {
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      errorMsg.value = '请求超时，请稍后重试'
    } else {
      errorMsg.value = error?.response?.data?.detail || error?.message || '连接后端失败，请确认后端已启动'
    }
  } finally {
    loading.value = false
    streaming.value = false
  }
}

const refine = async (instruction: string) => {
  if (!aiResult.value?.id) {
    errorMsg.value = '当前结果没有记录 ID，无法调优（请重新生成一次）'
    return
  }
  refining.value = true
  errorMsg.value = ''
  try {
    const response = await api.post('/api/refine', {
      record_id: aiResult.value.id,
      instruction,
      versions: 3,
    })
    const resultVersions = response.data.versions
    if (response.data.status === 'success' && resultVersions?.length) {
      versions.value = resultVersions
      currentVersion.value = 0
      const first = resultVersions[0]
      aiResult.value = { ...aiResult.value, id: first.id, title: first.title, body: first.body, tags: first.tags }
    } else {
      errorMsg.value = response.data.message || '调优失败，请稍后重试'
    }
  } catch (error: any) {
    if (error?.response?.status === 401) {
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    errorMsg.value = error?.response?.data?.detail || '调优失败，请稍后重试'
  } finally {
    refining.value = false
  }
}

const selectVersion = (index: number) => {
  if (!versions.value) return
  currentVersion.value = index
  const v = versions.value[index]
  if (v && aiResult.value) {
    aiResult.value = { ...aiResult.value, id: v.id, title: v.title, body: v.body, tags: v.tags }
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
      <h2 class="panel-title">① 图片来源</h2>
      <div class="input-mode-tabs">
        <button class="input-mode-tab" :class="{ active: inputMode === 'file' }" @click="inputMode = 'file'">
          📁 本地上传
        </button>
        <button class="input-mode-tab" :class="{ active: inputMode === 'url' }" @click="inputMode = 'url'">
          🔗 在线图片 URL
        </button>
      </div>

      <UploadDropzone v-if="inputMode === 'file'" v-model="selectedFile" />
      <div v-else class="field">
        <input v-model="imageUrl" class="input" placeholder="粘贴图片链接，如 https://example.com/photo.jpg" />
        <p style="font-size: 12px; color: var(--text-faint); margin: 8px 0 0;">
          支持 http/https 图片链接，后端会自动下载并识别
        </p>
      </div>

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
        <div class="chip-row">
          <button
            v-for="tone in tonePresets"
            :key="tone"
            class="quick-chip"
            :class="{ active: toneStyle === tone }"
            @click="toneStyle = toneStyle === tone ? '' : tone"
          >
            {{ tone }}
          </button>
        </div>
      </div>

      <label class="toggle-row">
        <input v-model="streamingEnabled" type="checkbox" />
        <span>✨ 流式逐字输出（推荐）</span>
      </label>

      <button
        class="btn btn-primary btn-block"
        :disabled="loading || streaming || (inputMode === 'file' ? !selectedFile : !imageUrl.trim())"
        @click="generate"
      >
        <span v-if="loading" class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></span>
        {{ streaming ? 'AI 正在逐字生成…' : loading ? 'AI 正在生成…' : '🚀 生成小红书文案' }}
      </button>
    </div>

    <div class="card">
      <h2 class="panel-title">③ 生成结果</h2>

      <div v-if="streaming" class="stream-box">
        <div class="stream-head">✨ AI 正在逐字生成文案…</div>
        <p>{{ streamText }}<span class="stream-cursor"></span></p>
      </div>

      <div v-else-if="loading" class="note-skeleton" aria-label="AI 正在生成文案">
        <div class="skeleton" style="height: 260px; border-radius: 16px 16px 0 0;"></div>
        <div style="padding: 18px;">
          <div class="skeleton" style="height: 22px; width: 72%; margin-bottom: 16px;"></div>
          <div class="skeleton" style="height: 14px; margin-bottom: 10px;"></div>
          <div class="skeleton" style="height: 14px; margin-bottom: 10px;"></div>
          <div class="skeleton" style="height: 14px; width: 86%; margin-bottom: 18px;"></div>
          <div class="skeleton" style="height: 34px; width: 46%;"></div>
        </div>
      </div>

      <div v-else-if="aiResult">
        <div v-if="versions && versions.length > 1" class="version-bar">
          <button
            v-for="(v, index) in versions"
            :key="v.id"
            class="version-chip"
            :class="{ active: index === currentVersion }"
            @click="selectVersion(index)"
          >
            版本 {{ index + 1 }}
          </button>
        </div>
        <NoteCard
          :title="aiResult.title"
          :body="aiResult.body"
          :tags="aiResult.tags"
          :image-url="previewUrl"
          :refining="refining"
          @refine="refine"
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
