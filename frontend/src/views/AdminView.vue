<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '../api'
import UsageChart from '../components/UsageChart.vue'
import StatNumber from '../components/StatNumber.vue'

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
    ElMessage.error(errorMsg.value)
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
      <el-tabs v-model="tab" class="admin-tabs-ep">
        <el-tab-pane label="📊 用量概览" name="overview">
          <div class="stat-grid">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-num"><StatNumber :value="stats?.total_users ?? 0" /></div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🗒️</div>
              <div class="stat-num"><StatNumber :value="stats?.total_records ?? 0" /></div>
              <div class="stat-label">累计生成次数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">⚡</div>
              <div class="stat-num"><StatNumber :value="stats?.today_records ?? 0" /></div>
              <div class="stat-label">今日生成次数</div>
            </div>
          </div>

          <div class="card chart-card">
            <h3>📈 最近 7 天每日生成次数</h3>
            <p class="chart-sub">展示各账号每日生成文案的数量趋势</p>
            <UsageChart :daily="stats?.daily ?? []" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="👥 用户列表" name="users">
          <div class="card">
            <el-table :data="users" stripe>
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column label="账号" min-width="190">
                <template #default="{ row }">
                  <div class="user-cell">
                    <span class="user-avatar">{{ row.username.charAt(0).toUpperCase() }}</span>
                    <span>{{ row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="角色" width="120">
                <template #default="{ row }">
                  <span class="role-badge" :class="{ admin: row.role === 'admin' }">
                    {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="注册时间" min-width="170" />
              <el-table-column prop="generation_count" label="生成次数" width="110" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="📝 生成记录" name="records">
          <div class="card">
            <el-table :data="records" stripe>
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="username" label="用户" width="150" />
              <el-table-column label="图片" width="90">
                <template #default="{ row }">
                  <img v-if="row.image_path" class="thumb-sm" :src="row.image_path" alt="图片" />
                  <span v-else class="thumb-empty">🖼️</span>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
              <el-table-column label="标签" min-width="210">
                <template #default="{ row }">
                  <span v-for="tag in row.tags" :key="tag" class="tag-chip">{{ tag }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="175" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>
