<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { categoryOf, reasonBadge } from '../categories'
const rows = ref<any[]>([])
const loading = ref(true)
// 进入即按当前摊主品类重新分配，确保改品类后放不下口径与分配图一致，不沿用旧结果。
async function refresh() {
  loading.value = true
  try {
    const data = await api('/allocate/run?segment_id=1', { method: 'POST' })
    rows.value = data.rejected || []
  } finally {
    loading.value = false
  }
}
onMounted(refresh)
</script>
<template>
  <h1>放不下</h1>
  <p class="sub">无法在连续空档内安置的摊位 · 品类相邻冲突与跨柱/空档不足分列原因，不并句</p>
  <button class="btn" :disabled="loading" @click="refresh">重新分配并刷新</button>
  <div class="card" style="margin-top:0.75rem">
    <table>
      <thead><tr><th>摊主</th><th>品类</th><th>需求宽度</th><th>原因</th></tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.vendor_id">
          <td>{{ r.vendor_name }}</td>
          <td><span :class="categoryOf(r.category).badge">{{ categoryOf(r.category).label }}</span></td>
          <td>{{ r.width_m }}</td>
          <td><span :class="reasonBadge(r.reason)">{{ r.reason }}</span></td>
        </tr>
      </tbody>
    </table>
    <p v-if="!loading && !rows.length" class="muted">全部放下</p>
  </div>
</template>
