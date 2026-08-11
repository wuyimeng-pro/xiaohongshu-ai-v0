<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const visible = ref(false)

const onScroll = () => {
  visible.value = window.scrollY > 420
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <Transition name="backtop-fade">
    <button v-if="visible" class="back-to-top" title="回到顶部" @click="scrollToTop">↑</button>
  </Transition>
</template>
