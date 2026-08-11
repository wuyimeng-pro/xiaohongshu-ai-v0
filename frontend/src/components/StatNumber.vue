<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps<{ value: number }>()

const display = ref(0)
let raf = 0

const animate = () => {
  cancelAnimationFrame(raf)
  const from = display.value
  const to = props.value
  const start = performance.now()
  const duration = 750
  const tick = (now: number) => {
    const progress = Math.min(1, (now - start) / duration)
    const eased = 1 - Math.pow(1 - progress, 3)
    display.value = Math.round(from + (to - from) * eased)
    if (progress < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}

onMounted(animate)
watch(() => props.value, animate)
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <span>{{ display }}</span>
</template>
