<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  title: string
  body: string
  tags: string[]
  imageUrl?: string
  refining?: boolean
}>()

const emit = defineEmits<{ (e: 'refine', instruction: string): void }>()

const copied = ref(false)
const tuningText = ref('')

const copyResult = async () => {
  const text = `【${props.title}】\n\n${props.body}\n\n${props.tags.join(' ')}`
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
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}

const submitRefine = () => {
  const text = tuningText.value.trim()
  if (!text || props.refining) return
  emit('refine', text)
  tuningText.value = ''
}
</script>

<template>
  <div class="note-card">
    <div class="note-card-head">
      <div class="note-avatar">AI</div>
      <div>
        <div class="note-username">AI 文案助手</div>
        <div class="note-time">刚刚生成 · 小红书风格</div>
      </div>
    </div>

    <div v-if="imageUrl" class="note-card-image">
      <img :src="imageUrl" alt="上传图片" />
    </div>

    <div class="note-card-body">
      <h3 class="note-card-title">{{ title }}</h3>
      <p class="note-card-text">{{ body }}</p>

      <div class="note-tags">
        <span v-for="tag in tags" :key="tag" class="tag-chip">{{ tag }}</span>
      </div>

      <div class="note-card-actions">
        <button class="btn btn-primary btn-sm" @click="copyResult">
          {{ copied ? '✅ 已复制' : '📋 一键复制' }}
        </button>
        <div class="tuning-input">
          <input
            v-model="tuningText"
            class="input"
            placeholder="输入修改意见，如：语气再活泼一点…"
            @keyup.enter="submitRefine"
          />
          <button class="btn btn-ghost btn-sm" style="margin-top: 8px;" :disabled="!tuningText.trim() || refining" @click="submitRefine">
            {{ refining ? '调优中…' : '✨ 生成调优版本' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
