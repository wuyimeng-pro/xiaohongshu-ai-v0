<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth'

const route = useRoute()
const router = useRouter()
const { isLoggedIn, user, clearSession } = useAuth()

const links = computed(() => {
  const base = [
    { to: '/', label: '工作台', icon: '✍️' },
    { to: '/history', label: '历史记录', icon: '🕘' },
  ]
  if (user.value?.role === 'admin') {
    base.push({ to: '/admin', label: '管理台', icon: '⚙️' })
  }
  return base
})

const logout = () => {
  clearSession()
  router.push('/login')
}
</script>

<template>
  <header class="navbar">
    <div class="navbar-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-logo">AI</span>
        <span class="brand-name">AI 文案工坊</span>
      </RouterLink>

      <nav class="nav-links">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: route.path === link.to }"
        >
          <span>{{ link.icon }}</span>{{ link.label }}
        </RouterLink>
      </nav>

      <template v-if="isLoggedIn">
        <span class="user-chip">👤 {{ user?.username }}</span>
        <button class="btn btn-ghost btn-sm" @click="logout">退出</button>
      </template>
      <RouterLink v-else to="/login" class="btn btn-primary btn-sm">登录</RouterLink>
    </div>
  </header>
</template>
