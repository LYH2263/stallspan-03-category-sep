<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { CATEGORIES, categoryColor, categoryLabel, effectiveCategory } from '../categories'

const rows = ref<any[]>([])
const alloc = ref<any>(null)
const savingId = ref<number | null>(null)

async function refresh() {
  const data = await api('/allocate/latest?segment_id=1')
  alloc.value = data
}

onMounted(async () => {
  rows.value = await api('/vendors')
  await refresh()
})

const placedMap = computed(
  () => new Map<number, any>((alloc.value?.placements || []).map((p: any) => [p.vendor_id, p] as [number, any])),
)
const rejectedMap = computed(
  () => new Map<number, any>((alloc.value?.rejected || []).map((r: any) => [r.vendor_id, r] as [number, any])),
)

async function changeCategory(r: any, value: string) {
  savingId.value = r.id
  try {
    const cat = value === '' ? null : value
    const updated = await api(`/vendors/${r.id}`, {
      method: 'PUT',
      body: JSON.stringify({ category: cat }),
    })
    // 写入后本地立即换新值；重新打开本页也由 GET 返回新值
    r.category = updated.category
    // 旧分配结果已随写入作废，按新品类重算，三处口径一致
    await refresh()
  } finally {
    savingId.value = null
  }
}
</script>
<template>
  <h1>摊主队列</h1>
  <p class="sub">底部排队条 · 宽度与优先级 · 品类（未标按手作兼容）</p>
  <div class="ss-vendor-queue" style="border-top:none; background:transparent; margin:0; padding:0.5rem 0 1rem">
    <div v-for="r in rows" :key="r.id ?? JSON.stringify(r)" class="ss-vendor-chip">
      <strong>
        <span class="ss-cat-dot" :style="{ background: categoryColor(r.category) }"></span>
        {{ r.name }}
      </strong>
      <span>需 {{ r.stall_width_m }} m · 优先 {{ r.priority }} · {{ categoryLabel(r.category) }}</span>
    </div>
  </div>
  <div class="card">
    <table>
      <thead>
        <tr><th>摊主</th><th>宽度(m)</th><th>优先级</th><th>品类</th><th>最新分配（与分配图 / 放不下同口径）</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.id ?? JSON.stringify(r)">
          <td>{{ r.name }}</td>
          <td>{{ r.stall_width_m }}</td>
          <td>{{ r.priority }}</td>
          <td>
            <select
              :value="r.category ?? ''"
              :disabled="savingId === r.id"
              @change="changeCategory(r, ($event.target as HTMLSelectElement).value)"
            >
              <option value="">未标（按手作）</option>
              <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
            </select>
          </td>
          <td>
            <span v-if="placedMap.get(r.id)" class="badge badge-ok">
              已入图 {{ placedMap.get(r.id).start_m }}–{{ placedMap.get(r.id).end_m }} m
              <span :style="{ color: categoryColor(effectiveCategory(placedMap.get(r.id).category)) }">
                · {{ placedMap.get(r.id).category }}
              </span>
            </span>
            <span v-else-if="rejectedMap.get(r.id)" class="badge badge-bad">
              放不下：{{ rejectedMap.get(r.id).reason }}
            </span>
            <span v-else class="muted">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
