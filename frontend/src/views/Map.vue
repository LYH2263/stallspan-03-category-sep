<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { categoryColor, categoryLabel } from '../categories'
const data = ref<any>(null)
const vendors = ref<any[]>([])
async function run() { data.value = await api('/allocate/run?segment_id=1', { method: 'POST' }) }
onMounted(async () => {
  vendors.value = await api('/vendors')
  await run()
})
const cells = computed(() => {
  if (!data.value) return []
  const width = data.value.segment.width_m
  const out: any[] = []
  for (const p of data.value.pillars || []) {
    out.push({ type: 'pillar', start: p.position_m - p.thickness_m/2, w: p.thickness_m, label: p.label || '挡柱' })
  }
  for (const p of (data.value.placements || [])) {
    // 颜色按品类：餐饮 / 手作；未标按手作兼容
    out.push({
      type: 'stall', start: p.start_m, w: p.width_m,
      label: `${p.vendor_name} · ${p.category}`, color: categoryColor(p.category),
    })
  }
  return out.sort((a,b) => a.start - b.start).map(c => ({ ...c, pct: Math.max((c.w / width) * 100, 2) }))
})
</script>
<template>
  <div class="ss-street-wrap">
    <h1>街段分配带</h1>
    <p class="sub">沿街一维开间 · 挡柱为竖直阻断 · 同柱间空档内餐饮与手作不得紧邻 · 底部为摊主排队</p>
    <div class="ss-legend">
      <span><i class="ss-cat-dot" :style="{ background: categoryColor('餐饮') }"></i>餐饮</span>
      <span><i class="ss-cat-dot" :style="{ background: categoryColor('手作') }"></i>手作 / 未标兼容</span>
      <span><i class="ss-cat-dot ss-cat-pillar"></i>挡柱</span>
    </div>
    <button class="btn" @click="run">重新分配</button>
    <div class="ss-band-ruler" v-if="data">
      <span>0 m</span>
      <span>{{ data.segment.name }} · {{ data.segment.width_m }} m</span>
      <span>{{ data.segment.width_m }} m</span>
    </div>
    <div class="ss-street-band" v-if="data">
      <div class="ss-street-inner">
        <div
          v-for="(c,i) in cells" :key="i"
          class="ss-band-cell"
          :class="{ 'ss-pillar': c.type === 'pillar' }"
          :style="{ width: c.pct + '%', background: c.type === 'pillar' ? undefined : c.color, flex: '0 0 ' + c.pct + '%' }"
        >{{ c.label }}</div>
      </div>
    </div>
    <div class="ss-vendor-queue">
      <div v-for="v in vendors" :key="v.id" class="ss-vendor-chip">
        <strong>
          <span class="ss-cat-dot" :style="{ background: categoryColor(v.category) }"></span>
          {{ v.name }}
        </strong>
        <span>需 {{ v.stall_width_m }} m · 优先 {{ v.priority }} · {{ categoryLabel(v.category) }}</span>
      </div>
    </div>
    <div class="card" v-if="data">
      <table>
        <thead><tr><th>摊主</th><th>品类</th><th>起点</th><th>终点</th><th>宽度</th></tr></thead>
        <tbody>
          <tr v-for="p in data.placements" :key="p.vendor_id">
            <td>{{ p.vendor_name }}</td>
            <td>
              <span class="ss-cat-dot" :style="{ background: categoryColor(p.category) }"></span>
              {{ p.category }}
            </td>
            <td>{{ p.start_m }}</td><td>{{ p.end_m }}</td><td>{{ p.width_m }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card" v-if="data && data.rejected.length">
      <strong>放不下（{{ data.rejected.length }}）</strong>
      <p class="sub" style="margin:0.3rem 0">与「放不下」页为同一口径</p>
      <table>
        <thead><tr><th>摊主</th><th>品类</th><th>需求宽度</th><th>原因</th></tr></thead>
        <tbody>
          <tr v-for="r in data.rejected" :key="r.vendor_id">
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
    </div>
  </div>
</template>
