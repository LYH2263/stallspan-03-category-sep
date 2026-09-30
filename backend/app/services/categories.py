"""摊主品类与相邻互斥规则。

品类枚举可扩展；本题至少有「餐饮」「手作」两种。
未标品类（None / 空串）的摊按手作兼容处理。
"""
from __future__ import annotations

CATEGORY_FOOD = "餐饮"
CATEGORY_CRAFT = "手作"

# 允许登记的品类（可扩枚举）
CATEGORIES = [CATEGORY_FOOD, CATEGORY_CRAFT]

# 同一柱间空档内不得直接相邻的品类对
INCOMPATIBLE_PAIRS = frozenset({
    (CATEGORY_CRAFT, CATEGORY_FOOD),
})

# 放不下原因口径（摊主页 / 分配图 / 放不下 三处共用，不得并句）
REASON_SPAN = "无连续空档可放下且不跨越挡柱"
REASON_CATEGORY = "品类相邻冲突：同一柱间空档内不得与相邻摊位品类紧邻"


def normalize_category(category: str | None) -> str:
    """未标品类按手作兼容。"""
    if category is None:
        return CATEGORY_CRAFT
    c = str(category).strip()
    return c if c else CATEGORY_CRAFT


def categories_conflict(a: str | None, b: str | None) -> bool:
    """两摊品类是否互斥（同一空档内紧邻时禁止）。"""
    ca, cb = normalize_category(a), normalize_category(b)
    if ca == cb:
        return False
    return tuple(sorted((ca, cb))) in INCOMPATIBLE_PAIRS
