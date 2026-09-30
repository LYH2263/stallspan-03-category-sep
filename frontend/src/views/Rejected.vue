<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { categoryColor } from '../categories'
const rows = ref<any[]>([])
onMounted(async () => {
  const data = await api('/allocate/latest?segment_id=1')
  rows.value = data.rejected || []
})
</script>
<template>
  <h1>放不下</h1>
  <p class="sub">无法入图的摊位 · 原因与摊主页、分配图同口径（品类相邻冲突与跨柱 / 空档不足分列，不并句）</p>
  <div class="card">
    <table>
      <thead><tr><th>摊主</th><th>品类</th><th>需求宽度</th><th>原因</th></tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.vendor_id">
          <td>{{ r.vendor_name }}</td>
          <td>
            <span class="ss-cat-dot" :style="{ background: categoryColor(r.category) }"></span>
            {{ r.category }}
          </td>
          <td>{{ r.width_m }}</td>
          <td>{{ r.reason }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!rows.length" class="muted">全部放下</p>
  </div>
</template>
