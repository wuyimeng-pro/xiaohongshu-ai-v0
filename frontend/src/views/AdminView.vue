<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '../api'

interface AdminUser {
  id: number
  username: string
  role: string
  created_at: string | null
  generation_count: number
}

interface AdminRecord {
  id: number
  username: string
  image_name: string | null
  image_path: string | null
  title: string
  tags: string[]
  created_at: string | null
}

interface Stats {
  total_users: number
  total_records: number
  today_records: number
  daily: { date: string; count: number }[]
}

const tab = ref<'overview' | 'users' | 'records'>('overview')
const loading = ref(true)
const errorMsg = ref('')
const stats = ref<Stats | null>(null)
const users = ref<AdminUser[]>([])
const records = ref<AdminRecord[]>([])

const maxDaily = computed(() =>
  Math.max(1, ...(stats.value?.daily.map((d) => d.count) ?? [1]))
)

const barHeight = (count: number) =>
  `${Math.max(6, Math.round((count / maxDaily.value) * 100))}%`

const loadAll = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const [statsRes, usersRes, recordsRes] = await Promise.all([
      api.get('/api/admin/stats'),
      api.get('/api/admin/users'),
      api.get('/api/admin/records'),
    ])
    stats.value = statsRes.data.stats
    users.value = usersRes.data.users ?? []
    records.value = recordsRes.data.records ?? []
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || '加载管理数据失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <header class="page-head">
      <h1>⚙️ 后台管理台</h1>
      <p>管理员专用：用户管理、生成记录、每日用量统计。</p>
    </header>

    <div v-if="loading" class="card loading-box">
      <div class="spinner"></div>
      <p>正在加载管理数据…</p>
    </div>

    <div v-else-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>

    <template v-else>
      <div class="admin-tabs">
        <button class="admin-tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">📊 用量概览</button>
        <button class="admin-tab" :class="{ active: tab === 'users' }" @click="tab = 'users'">👥 用户列表</button>
        <button class="admin-tab" :class="{ active: tab === 'records' }" @click="tab = 'records'">📝 生成记录</button>
      </div>

      <div v-if="tab === 'overview'" class="card">
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-num">{{ stats?.total_users }}</div>
            <div class="stat-label">总用户数</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ stats?.total_records }}</div>
            <div class="stat-label">累计生成次数</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ stats?.today_records }}</div>
            <div class="stat-label">今日生成次数</div>
          </div>
        </div>

        <h3 style="margin: 24px 0 12px;">最近 7 天每日生成次数</h3>
        <div class="daily-bars">
          <div v-for="item in stats?.daily" :key="item.date" class="daily-bar">
            <div class="daily-count">{{ item.count }}</div>
            <div class="daily-track">
              <div class="daily-fill" :style="{ height: barHeight(item.count) }"></div>
            </div>
            <div class="daily-date">{{ item.date }}</div>
          </div>
          <div v-if="!stats?.daily.length" class="daily-empty">近 7 天暂无生成记录</div>
        </div>
      </div>

      <div v-else-if="tab === 'users'" class="card">
        <div class="admin-table-wrap">
          <table class="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>账号</th>
                <th>角色</th>
                <th>注册时间</th>
                <th>生成次数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td>{{ u.id }}</td>
                <td>{{ u.username }}</td>
                <td>
                  <span class="role-badge" :class="{ admin: u.role === 'admin' }">
                    {{ u.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>
                <td>{{ u.created_at }}</td>
                <td>{{ u.generation_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="card">
        <div class="admin-table-wrap">
          <table class="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户</th>
                <th>图片</th>
                <th>标题</th>
                <th>标签</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in records" :key="r.id">
                <td>{{ r.id }}</td>
                <td>{{ r.username }}</td>
                <td>
                  <img
                    v-if="r.image_path"
                    class="thumb-sm"
                    :src="'http://127.0.0.1:8000/' + r.image_path"
                    alt="图片"
                  />
                </td>
                <td class="record-title">{{ r.title }}</td>
                <td>
                  <span v-for="tag in r.tags" :key="tag" class="tag-chip">{{ tag }}</span>
                </td>
                <td class="record-time">{{ r.created_at }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
