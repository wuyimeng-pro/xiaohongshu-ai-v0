import { createApp, type Directive } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

const revealObservers = new WeakMap<HTMLElement, IntersectionObserver>()

// 滚动入场动效：元素进入视口时淡入上移
const reveal: Directive<HTMLElement> = {
  mounted(el) {
    el.classList.add('reveal')
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.classList.add('reveal-visible')
            observer.unobserve(el)
          }
        })
      },
      { threshold: 0.12 }
    )
    revealObservers.set(el, observer)
    observer.observe(el)
  },
  unmounted(el) {
    revealObservers.get(el)?.disconnect()
    revealObservers.delete(el)
  },
}

const app = createApp(App)

app.config.errorHandler = (error, _instance, info) => {
  console.error('[app error]', info, error)
  ElMessage.error('页面出了点小问题，请刷新重试')
}

app.directive('reveal', reveal).use(router).mount('#app')
