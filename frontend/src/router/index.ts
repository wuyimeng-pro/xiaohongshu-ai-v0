import { createRouter, createWebHistory } from 'vue-router'

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    {
      path: '/workbench',
      name: 'workbench',
      component: () => import('../views/WorkbenchView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
      meta: { requiresAuth: true },
    },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
    },
  ],
})

// 路由守卫：未登录不能进工作台/历史/管理台；非管理员不能进管理台
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const user = getStoredUser()

  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && user?.role !== 'admin') {
    return '/'
  }
  if (to.path === '/login' && token) {
    return '/workbench'
  }
  return true
})

// 路由/懒加载失败兜底：避免页面空白
const retriedNavigations = new Set<string>()
router.onError((error, to) => {
  const key = to.fullPath || to.path || 'current'
  const isChunkError = /Failed to fetch dynamically imported module|Outdated Optimize Dep/.test(String(error))

  // 开发模式下 Vite 首次编译可能 504，自动重试一次
  if (isChunkError && !retriedNavigations.has(key)) {
    retriedNavigations.add(key)
    setTimeout(() => {
      router.replace(key).catch(() => {})
    }, 600)
    return
  }

  console.error('[router error]', error)
  ElMessage.error('页面加载失败，请稍后重试或刷新页面')
})

export default router
