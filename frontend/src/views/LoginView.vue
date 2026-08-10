<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuth } from '../auth'

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const adminCode = ref('')
const errorMsg = ref('')
const loading = ref(false)

const router = useRouter()
const route = useRoute()
const { setSession } = useAuth()

const submit = async () => {
  errorMsg.value = ''

  if (!username.value.trim()) {
    errorMsg.value = '请输入账号'
    return
  }
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return
  }
  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    const url = mode.value === 'login' ? '/api/login' : '/api/register'
    const response = await api.post(url, {
      username: username.value.trim(),
      password: password.value,
      admin_code: adminCode.value,
    })
    if (response.data.status === 'success') {
      setSession(response.data.token, response.data.user)
      router.push((route.query.redirect as string) || '/')
    } else {
      errorMsg.value = response.data.message || '操作失败'
    }
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || '连接后端失败，请确认后端已启动'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <div class="card">
      <h2 style="margin: 0 0 4px; text-align: center;">
        {{ mode === 'login' ? '欢迎回来 👋' : '创建你的账号 ✨' }}
      </h2>
      <p style="text-align: center; color: #6b7280; margin: 0 0 20px; font-size: 14px;">
        登录后可同步你的生成历史
      </p>

      <div class="auth-tabs">
        <button class="auth-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="auth-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div class="field">
        <label>账号</label>
        <input v-model="username" class="input" placeholder="3~20 个字符" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" class="input" type="password" :placeholder="mode === 'register' ? '至少 6 位' : '请输入密码'" />
      </div>
      <div v-if="mode === 'register'" class="field">
        <label>确认密码</label>
        <input v-model="confirmPassword" class="input" type="password" placeholder="再次输入密码" />
      </div>
      <div v-if="mode === 'register'" class="field">
        <label>管理员邀请码（选填）</label>
        <input v-model="adminCode" class="input" placeholder="留空则注册为普通用户" />
      </div>

      <button class="btn btn-primary btn-block" :disabled="loading" @click="submit">
        <span v-if="loading" class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></span>
        {{ loading ? '处理中…' : mode === 'login' ? '登 录' : '注 册' }}
      </button>

      <div v-if="errorMsg" class="alert alert-error" style="margin-top: 14px;">{{ errorMsg }}</div>
    </div>
  </div>
</template>
