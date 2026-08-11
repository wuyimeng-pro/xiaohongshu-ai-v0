<template>
  <div class="not-found">
    <div class="nf-code">404</div>
    <h1>页面走丢了</h1>
    <p>你访问的页面不存在，或者已经被移动到了别的地方。</p>
    <div class="nf-actions">
      <RouterLink to="/" class="btn btn-primary">回到首页</RouterLink>
      <RouterLink to="/workbench" class="btn btn-ghost">去工作台</RouterLink>
    </div>
  </div>
</template>
