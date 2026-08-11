<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuth } from '../auth'

const mode = ref<'login' | 'register'>('login')
const formRef = ref()
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  adminCode: '',
})
const errorMsg = ref('')
const loading = ref(false)

const router = useRouter()
const route = useRoute()
const { setSession } = useAuth()

const validateConfirm = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (mode.value === 'register' && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度 3~20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [{ validator: validateConfirm, trigger: 'blur' }],
}

const submit = async () => {
  errorMsg.value = ''
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const url = mode.value === 'login' ? '/api/login' : '/api/register'
    const response = await api.post(url, {
      username: form.username.trim(),
      password: form.password,
      admin_code: form.adminCode,
    })
    if (response.data.status === 'success') {
      setSession(response.data.token, response.data.user)
      router.push((route.query.redirect as string) || '/workbench')
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
      <p style="text-align: center; color: var(--text-sub); margin: 0 0 20px; font-size: 14px;">
        登录后可同步你的生成历史
      </p>

      <div class="auth-tabs">
        <el-radio-group v-model="mode" class="auth-radio">
          <el-radio-button label="login">登录</el-radio-button>
          <el-radio-button label="register">注册</el-radio-button>
        </el-radio-group>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="3~20 个字符" clearable>
            <template #prefix><span class="input-emoji">👤</span></template>
          </el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="mode === 'register' ? '至少 6 位' : '请输入密码'"
          >
            <template #prefix><span class="input-emoji">🔒</span></template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="mode === 'register'" label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="再次输入密码"
          >
            <template #prefix><span class="input-emoji">🔒</span></template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="mode === 'register'" label="管理员邀请码（选填）">
          <el-input v-model="form.adminCode" placeholder="留空则注册为普通用户" clearable>
            <template #prefix><span class="input-emoji">🔑</span></template>
          </el-input>
        </el-form-item>

        <el-button class="auth-submit" type="primary" :loading="loading" @click="submit">
          {{ mode === 'login' ? '登 录' : '注 册' }}
        </el-button>
      </el-form>

      <el-alert v-if="errorMsg" :title="errorMsg" type="error" :closable="false" show-icon class="auth-error" />
    </div>
  </div>
</template>
