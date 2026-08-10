<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth'
import { useTheme } from '../theme'

const route = useRoute()
const router = useRouter()
const { isLoggedIn, user, clearSession } = useAuth()
const { theme, toggle } = useTheme()
const menuOpen = ref(false)

const links = computed(() => {
  const base = [
    { to: '/', label: '首页', icon: '🏠' },
    { to: '/workbench', label: '工作台', icon: '✍️' },
    { to: '/history', label: '历史记录', icon: '🕘' },
  ]
  if (user.value?.role === 'admin') {
    base.push({ to: '/admin', label: '管理台', icon: '⚙️' })
  }
  return base
})

const logout = () => {
  menuOpen.value = false
  clearSession()
  router.push('/login')
}

// 路由切换时收起移动端菜单
watch(() => route.path, () => {
  menuOpen.value = false
})
</script>

<template>
  <header class="navbar">
    <div class="navbar-inner">
      <RouterLink to="/" class="brand" @click="menuOpen = false">
        <span class="brand-logo">AI</span>
        <span class="brand-name">AI 文案工坊</span>
      </RouterLink>

      <button
        class="nav-toggle"
        :aria-expanded="menuOpen"
        aria-label="切换菜单"
        @click="menuOpen = !menuOpen"
      >
        <span></span><span></span><span></span>
      </button>

      <nav class="nav-links" :class="{ open: menuOpen }" @click="menuOpen = false">
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

      <div class="nav-actions">
        <button class="icon-btn theme-toggle" :title="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'" @click="toggle">
          <span v-if="theme === 'dark'">☀️</span>
          <span v-else>🌙</span>
        </button>

        <template v-if="isLoggedIn">
          <span class="user-chip">👤 {{ user?.username }}</span>
          <button class="btn btn-ghost btn-sm nav-logout" @click="logout">退出</button>
        </template>
        <RouterLink v-else to="/login" class="btn btn-primary btn-sm nav-login">登录</RouterLink>
      </div>
    </div>
  </header>
</template>
