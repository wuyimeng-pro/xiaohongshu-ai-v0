<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div>
    <header class="page-head">
      <h1>⚙️ 后台管理台</h1>
      <p>管理员专用：用户管理、生成记录、用量统计概览。</p>
    </header>

    <div class="card empty-state">
      <div class="empty-icon">🔒</div>
      <h3>后台管理即将上线</h3>
      <p>该页面仅管理员（role = admin）可访问，后续将接入用户管理与数据统计。</p>
      <RouterLink to="/" class="btn btn-ghost">返回工作台</RouterLink>
    </div>
  </div>
</template>
