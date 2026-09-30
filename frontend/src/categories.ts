// 品类口径：摊主页、分配图、放不下三处共用，保证标签/颜色一致。
// 键与后端 first_fit_engine.CATEGORY_LABELS 对齐，可扩枚举。
export const CATEGORY_FOOD = 'food'
export const CATEGORY_HANDMADE = 'handmade'

interface CategoryInfo { label: string; color: string; badge: string }

export const CATEGORIES: Record<string, CategoryInfo> = {
  [CATEGORY_FOOD]: { label: '餐饮', color: '#e27d60', badge: 'badge badge-warn' },
  [CATEGORY_HANDMADE]: { label: '手作', color: '#85dcb8', badge: 'badge badge-ok' },
}

// 可选项（摊主页下拉）；未标品类按手作兼容。
export const CATEGORY_OPTIONS = [CATEGORY_FOOD, CATEGORY_HANDMADE]

export function categoryOf(key?: string | null): CategoryInfo {
  return CATEGORIES[key || CATEGORY_HANDMADE] ?? CATEGORIES[CATEGORY_HANDMADE]
}

// 放不下原因口径与后端常量逐字一致，禁止并句。
export const REASON_CATEGORY = '品类相邻冲突'
export const REASON_SPACE = '无连续空档可放下且不跨越挡柱'

export function reasonBadge(reason: string): string {
  if (reason === REASON_CATEGORY) return 'badge badge-warn'
  if (reason === REASON_SPACE) return 'badge badge-bad'
  return 'badge'
}
