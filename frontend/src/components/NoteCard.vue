<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  title: string
  body: string
  tags: string[]
  imageUrl?: string
  refining?: boolean
  authorName?: string
  authorAvatar?: string
  noteTime?: string
  compact?: boolean
  versionLabel?: string
  selected?: boolean
}>()

const emit = defineEmits<{
  (e: 'refine', instruction: string): void
  (e: 'select'): void
}>()

const copied = ref(false)
const tuningText = ref('')
const liked = ref(false)
const collected = ref(false)
const likes = ref(128)
const collects = ref(66)
const comments = ref(23)

const authorName = computed(() => props.authorName || 'AI 文案助手')
const authorAvatar = computed(() => props.authorAvatar || 'AI')
const noteTime = computed(() => props.noteTime || '刚刚生成 · 小红书风格')

const toggleLike = () => {
  liked.value = !liked.value
  likes.value += liked.value ? 1 : -1
}

const toggleCollect = () => {
  collected.value = !collected.value
  collects.value += collected.value ? 1 : -1
}

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
  <div
    class="note-card"
    :class="{ compact, 'version-selectable': compact && versionLabel, selected }"
    @click="compact && versionLabel ? emit('select') : undefined"
  >
    <div v-if="versionLabel" class="note-version-strip" :class="{ selected }">
      <span>版本 {{ versionLabel }}</span>
      <span v-if="selected" class="note-version-check">✓ 已采用</span>
    </div>

    <div class="note-card-head">
      <div class="note-avatar">{{ authorAvatar }}</div>
      <div>
        <div class="note-username">
          {{ authorName }}
          <span class="note-badge">种草笔记</span>
        </div>
        <div class="note-time">{{ noteTime }}</div>
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

      <div class="note-card-actions" @click.stop>
        <button class="btn btn-primary btn-sm" @click="copyResult">
          {{ copied ? '✅ 已复制' : '📋 一键复制' }}
        </button>
        <div v-if="compact && versionLabel" class="compare-actions">
          <button class="btn btn-ghost btn-sm" :class="{ 'btn-choose': selected }" @click="emit('select')">
            {{ selected ? '✓ 当前版本' : '采用此版本' }}
          </button>
        </div>
        <div v-else class="tuning-input">
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

    <div v-if="!compact" class="note-card-footer">
      <button class="note-react" :class="{ active: liked }" @click="toggleLike">
        <span class="note-react-icon">{{ liked ? '💗' : '🤍' }}</span>{{ likes }}
      </button>
      <button class="note-react" :class="{ active: collected }" @click="toggleCollect">
        <span class="note-react-icon">{{ collected ? '⭐' : '☆' }}</span>{{ collects }}
      </button>
      <span class="note-react-static">
        <span class="note-react-icon">💬</span>{{ comments }}
      </span>
    </div>
  </div>
</template>
