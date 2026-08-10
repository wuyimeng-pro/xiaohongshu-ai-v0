import { ref } from 'vue'

export type Theme = 'light' | 'dark'

function getInitialTheme(): Theme {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const theme = ref<Theme>(getInitialTheme())

function applyTheme(next: Theme) {
  const root = document.documentElement
  root.dataset.theme = next
  root.style.colorScheme = next
  localStorage.setItem('theme', next)
}

// 模块加载时立即应用，避免页面闪烁
applyTheme(theme.value)

export function useTheme() {
  const toggle = () => {
    const next: Theme = theme.value === 'dark' ? 'light' : 'dark'
    theme.value = next
    applyTheme(next)
  }
  const setTheme = (next: Theme) => {
    theme.value = next
    applyTheme(next)
  }
  return { theme, toggle, setTheme }
}
