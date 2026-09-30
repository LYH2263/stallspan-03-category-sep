// 摊主品类口径（与后端 app/services/categories.py 对齐）
// 未标品类（null/''）按手作兼容；枚举可扩。
export const CATEGORIES = ['餐饮', '手作'] as const

export const CATEGORY_COLORS: Record<string, string> = {
  餐饮: '#e27d60',
  手作: '#85dcb8',
}

// 未标品类按手作兼容着色
export function effectiveCategory(category?: string | null): string {
  return category === '餐饮' ? '餐饮' : '手作'
}

export function categoryColor(category?: string | null): string {
  return CATEGORY_COLORS[effectiveCategory(category)]
}

export function categoryLabel(category?: string | null): string {
  return category || '未标 · 按手作兼容'
}
