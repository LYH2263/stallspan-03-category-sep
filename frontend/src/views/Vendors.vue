<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { CATEGORY_OPTIONS, categoryOf, reasonBadge, REASON_CATEGORY } from '../categories'

const rows = ref<any[]>([])
// vendor_id -> 最近一次分配的放不下原因；不在表里即已上图
const rejectMap = ref<Record<number, string>>({})
const saving = ref<number | null>(null)

async function loadStatus() {
  const data = await api('/allocate/latest?segment_id=1')
  const m: Record<number, string> = {}
  for (const r of data.rejected || []) m[r.vendor_id] = r.reason
  rejectMap.value = m
}
async function load() {
  rows.value = await api('/vendors')
  await loadStatus()
}
onMounted(load)

async function changeCategory(r: any, cat: string) {
  saving.value = r.id
  try {
    // 写入后本地立即更新；重新打开仍由 GET /vendors 返回新值
    const updated = await api(`/vendors/${r.id}`, { method: 'PATCH', body: JSON.stringify({ category: cat }) })
    const idx = rows.value.findIndex(x => x.id === r.id)
    if (idx >= 0) rows.value[idx] = updated
    // 改品类后须重新分配才会按新品类占位；此处刷新最近一次结果的口径提示
    await loadStatus()
  } finally {
    saving.value = null
  }
}
</script>
<template>
  <h1>摊主队列</h1>
  <p class="sub">底部排队条 · 宽度、优先级与品类 · 改品类后请到「分配图」重新分配</p>
  <div class="ss-vendor-queue" style="border-top:none; background:transparent; margin:0; padding:0.5rem 0 1rem">
    <div v-for="r in rows" :key="r.id ?? JSON.stringify(r)" class="ss-vendor-chip">
      <strong>{{ r.name }}</strong>
      <span>需 {{ r.stall_width_m }} m · 优先 {{ r.priority }}</span>
      <span :class="categoryOf(r.category).badge">{{ categoryOf(r.category).label }}</span>
    </div>
  </div>
  <div class="card">
    <table>
      <thead><tr><th>摊主</th><th>宽度(m)</th><th>优先级</th><th>品类</th><th>最近分配</th></tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id ?? JSON.stringify(r)">
          <td>{{ r.name }}</td>
          <td>{{ r.stall_width_m }}</td>
          <td>{{ r.priority }}</td>
          <td>
            <select :value="r.category" :disabled="saving === r.id"
                    @change="changeCategory(r, ($event.target as HTMLSelectElement).value)">
              <option v-for="c in CATEGORY_OPTIONS" :key="c" :value="c">{{ categoryOf(c).label }}</option>
            </select>
          </td>
          <td>
            <span v-if="rejectMap[r.id]" :class="reasonBadge(rejectMap[r.id])">{{ rejectMap[r.id] }}</span>
            <span v-else class="badge badge-ok">已上图</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p class="muted" style="margin-bottom:0">
      「{{ REASON_CATEGORY }}」指同一柱间空档内与互斥品类直接相邻；跨挡柱或隔空档不算相邻。
    </p>
  </div>
</template>
