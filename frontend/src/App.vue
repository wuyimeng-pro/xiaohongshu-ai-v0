<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import BackToTop from './components/BackToTop.vue'

const route = useRoute()
</script>

<template>
  <NavBar />
  <main class="page">
    <RouterView v-slot="{ Component }">
      <component :is="Component" :key="route.path" class="page-enter" />
    </RouterView>
  </main>
  <footer class="site-footer">
    <p>AI 文案工坊 · 图片小红书文案生成平台 · 上海电信智能云能力中心新人实战项目</p>
  </footer>
  <BackToTop />
</template>
