<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const features = [
  { icon: '🖼️', title: '智能识图', desc: '基于阿里云 Qwen-VL 多模态大模型，自动识别图片内容与场景。' },
  { icon: '📝', title: '种草文案', desc: '标题、正文、话题标签一键生成，小红书爆款风格。' },
  { icon: '🎯', title: '自定义风格', desc: '填写产品名称、目标人群、语气风格，文案贴合你的需求。' },
  { icon: '📋', title: '一键复制', desc: '标题、正文、标签打包复制，直接粘贴发布。' },
  { icon: '🕘', title: '历史回溯', desc: '所有生成记录自动保存，随时回到过去的灵感。' },
  { icon: '✨', title: '多版本调优', desc: '对结果提出修改意见，一次生成多个版本对比选择。' },
]

const steps = [
  { num: '01', title: '上传图片', desc: '选择一张本地图片，支持 JPEG / PNG / GIF / WebP / BMP' },
  { num: '02', title: '补充信息', desc: '选填产品名称、目标人群和语气风格，让文案更精准' },
  { num: '03', title: '生成与发布', desc: 'AI 生成笔记卡片，一键复制到小红书即可发布' },
]

const faqs = [
  { q: '需要登录才能使用吗？', a: '首次使用需要注册并登录，登录后所有生成记录都会保存到你的账号下。' },
  { q: '支持哪些图片格式？', a: '支持 JPEG、PNG、GIF、WebP、BMP，单张图片最大 20MB。' },
  { q: '生成记录保存在哪里？', a: '所有记录（图片、输入参数、文案、时间）都保存在本地 MySQL 数据库中，安全可控。' },
  { q: '生成结果不满意怎么办？', a: '可以直接在结果卡片上输入修改意见，比如“语气更活泼一点”，每次会生成 3 个版本供你对比。' },
  { q: '文案可以一键复制到小红书吗？', a: '可以，结果卡片上的“一键复制”会把标题、正文和话题标签一起复制到剪贴板。' },
]

const openFaq = ref<number | null>(0)
</script>

<template>
  <div>
    <section class="hero home-hero">
      <h1>上传一张图片<br />生成爆款小红书文案</h1>
      <p>AI 文案工坊基于阿里云 Qwen-VL 多模态大模型，自动识别图片内容，一键生成标题、正文与话题标签，让你的种草笔记又快又专业。</p>
      <div class="home-cta">
        <RouterLink to="/workbench" class="btn btn-primary btn-lg">🚀 进入工作台</RouterLink>
        <a href="#features" class="btn btn-ghost btn-lg" style="background: rgba(255,255,255,.15); color: #fff; border-color: rgba(255,255,255,.4);">了解功能</a>
      </div>
      <div class="hero-badges" style="margin-top: 22px;">
        <span>✨ 智能识图</span>
        <span>📝 种草文案</span>
        <span># 话题标签</span>
        <span>🎯 自定义风格</span>
      </div>
    </section>

    <section id="features" class="home-section">
      <h2>产品功能</h2>
      <p class="sub">从一张图片到一篇完整的小红书文案，只需三步</p>
      <div class="features-grid">
        <div v-for="f in features" :key="f.title" class="feature-card">
          <div class="feature-icon">{{ f.icon }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <section class="home-section">
      <h2>如何使用</h2>
      <p class="sub">简单的三步，快速产出你的第一篇种草笔记</p>
      <div class="steps-grid">
        <div v-for="s in steps" :key="s.num" class="step-card">
          <div class="step-num">{{ s.num }}</div>
          <h3>{{ s.title }}</h3>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </section>

    <section class="home-section">
      <h2>常见问题</h2>
      <p class="sub">使用前你可能想知道的事</p>
      <div class="card faq-card">
        <div v-for="(item, index) in faqs" :key="item.q" class="faq-item">
          <button class="faq-question" @click="openFaq = openFaq === index ? null : index">
            {{ item.q }}
            <span>{{ openFaq === index ? '−' : '+' }}</span>
          </button>
          <div v-if="openFaq === index" class="faq-answer">{{ item.a }}</div>
        </div>
      </div>
    </section>

    <section class="cta-box">
      <h2>准备好了吗？现在就开始生成你的第一篇小红书文案</h2>
      <p>免费注册，登录后即可使用全部功能</p>
      <RouterLink to="/workbench" class="btn btn-primary btn-lg" style="background:#fff; color:var(--primary); box-shadow: none;">立即开始</RouterLink>
    </section>
  </div>
</template>
