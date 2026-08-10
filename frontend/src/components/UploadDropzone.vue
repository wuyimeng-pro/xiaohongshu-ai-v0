<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ modelValue: File | null }>()
const emit = defineEmits<{ (e: 'update:modelValue', file: File | null): void }>()

const dragging = ref(false)
const previewUrl = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const selectedFileName = computed(() => props.modelValue?.name ?? '')

const pickFile = (files: FileList | null) => {
  const file = files?.[0]
  if (!file) return
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(file)
  emit('update:modelValue', file)
}

const onInputChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  pickFile(input.files)
  input.value = ''
}

const onDrop = (event: DragEvent) => {
  dragging.value = false
  pickFile(event.dataTransfer?.files ?? null)
}

const clearFile = () => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  emit('update:modelValue', null)
}
</script>

<template>
  <div>
    <div
      class="dropzone"
      :class="{ dragging }"
      @click="fileInput?.click()"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <template v-if="previewUrl">
        <div class="dropzone-preview">
          <img :src="previewUrl" alt="图片预览" />
        </div>
      </template>
      <template v-else>
        <div class="dropzone-icon"><span>📸</span></div>
        <p class="dropzone-title"><strong>点击选择图片</strong> 或拖拽到此处</p>
        <p class="dropzone-hint">支持 JPEG / PNG / GIF / WebP / BMP，最大 20MB</p>
      </template>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="onInputChange"
    />

    <div v-if="selectedFileName" class="file-meta">已选择：{{ selectedFileName }}</div>

    <div v-if="previewUrl" class="dropzone-actions">
      <button type="button" class="btn btn-ghost btn-sm" @click="clearFile">重新选择</button>
    </div>
  </div>
</template>
