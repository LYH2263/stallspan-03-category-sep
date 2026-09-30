"""1D First-Fit stall placement along a street segment; stalls cannot cross pillars.

品类相邻隔离：同一挡柱切开的空档（free span）内，按落位顺序餐饮（food）
与手作（handmade）不得直接相邻。First-Fit 从每个空档左侧紧排，新摊只与
该空档已落位的最后一摊直接相邻，故只需比对空档队尾品类。跨挡柱、中间
隔着空档（柱子切开）不算相邻——它们本就落在不同 span。

品类可扩枚举：新增品类只需在 CATEGORY_LABELS 登记，并在 CONFLICT_PAIRS
里声明互斥对；未标品类（None/""）按手作兼容处理。
"""
from __future__ import annotations
from dataclasses import asdict, dataclass

# 品类枚举（可扩展）
CATEGORY_FOOD = "food"
CATEGORY_HANDMADE = "handmade"
CATEGORY_LABELS = {
    CATEGORY_FOOD: "餐饮",
    CATEGORY_HANDMADE: "手作",
}
# 互斥品类对：同一空档内直接相邻即冲突
CONFLICT_PAIRS = {
    frozenset((CATEGORY_FOOD, CATEGORY_HANDMADE)),
}
# 未标品类的摊按手作兼容
DEFAULT_CATEGORY = CATEGORY_HANDMADE

# 放不下原因——两条互斥口径，禁止并句
REASON_CATEGORY = "品类相邻冲突"
REASON_SPACE = "无连续空档可放下且不跨越挡柱"


def normalize_category(category: str | None) -> str:
    """未标品类按手作兼容；未知品类原样保留（与谁都不互斥，除非另在枚举登记）。"""
    if category is None or str(category).strip() == "":
        return DEFAULT_CATEGORY
    return str(category).strip()


def categories_conflict(a: str | None, b: str | None) -> bool:
    """餐饮与手作互斥；同品类或未标（按手作）不冲突。"""
    ca, cb = normalize_category(a), normalize_category(b)
    if ca == cb:
        return False
    return frozenset((ca, cb)) in CONFLICT_PAIRS


@dataclass
class Placement:
    vendor_id: int
    vendor_name: str
    start_m: float
    end_m: float
    width_m: float
    category: str = DEFAULT_CATEGORY

@dataclass
class Rejected:
    vendor_id: int
    vendor_name: str
    width_m: float
    reason: str
    category: str = DEFAULT_CATEGORY

@dataclass
class AllocResult:
    placements: list[Placement]
    rejected: list[Rejected]
    free_spans: list[tuple[float, float]]

def free_spans_from_pillars(width_m: float, pillars: list[dict]) -> list[tuple[float, float]]:
    """pillars: position_m, thickness_m — treated as blocked intervals."""
    blocked = []
    for p in pillars:
        half = p.get("thickness_m", 0.4) / 2.0
        lo = max(0.0, p["position_m"] - half)
        hi = min(width_m, p["position_m"] + half)
        if hi > lo:
            blocked.append((lo, hi))
    blocked.sort()
    merged = []
    for lo, hi in blocked:
        if not merged or lo > merged[-1][1]:
            merged.append([lo, hi])
        else:
            merged[-1][1] = max(merged[-1][1], hi)
    spans = []
    cursor = 0.0
    for lo, hi in merged:
        if lo > cursor:
            spans.append((cursor, lo))
        cursor = hi
    if cursor < width_m:
        spans.append((cursor, width_m))
    return [(round(a, 3), round(b, 3)) for a, b in spans if b - a > 1e-6]

def allocate_first_fit(width_m: float, vendors: list[dict], pillars: list[dict]) -> AllocResult:
    """vendors sorted by priority ascending then id; each needs stall_width_m
    contiguous in one free span (no pillar cross), and must not be directly
    adjacent to a conflicting category already placed at that span's frontier.
    """
    spans = free_spans_from_pillars(width_m, pillars)
    # mutable remaining capacity per span; tail category = 紧邻队尾已落位摊的品类
    remain = [[a, b] for a, b in spans]
    tail_category: list[str | None] = [None] * len(remain)
    ordered = sorted(vendors, key=lambda v: (v.get("priority", 1), v["id"]))
    placements: list[Placement] = []
    rejected: list[Rejected] = []
    for v in ordered:
        need = float(v["stall_width_m"])
        category = normalize_category(v.get("category"))
        placed = False
        category_blocked = False  # 存在“空档够宽但品类相邻冲突”的 span
        for i, span in enumerate(remain):
            avail = span[1] - span[0]
            if avail + 1e-9 < need:
                continue  # 空档不足（含被柱切开）
            # tail None 表示该空档还没有任何摊——前方无邻居，不构成相邻
            if tail_category[i] is not None and categories_conflict(tail_category[i], category):
                category_blocked = True  # 此空档宽度够，但与队尾直接相邻冲突
                continue
            start = span[0]
            end = start + need
            placements.append(Placement(v["id"], v["name"], round(start, 3), round(end, 3), need, category))
            span[0] = end
            tail_category[i] = category
            placed = True
            break
        if not placed:
            # 只要有任一档空档宽度够却因品类冲突未能进，就归品类口径；
            # 否则才是跨柱/空档不足口径。两句不并写。
            reason = REASON_CATEGORY if category_blocked else REASON_SPACE
            rejected.append(Rejected(v["id"], v["name"], need, reason, category))
    free = [(round(a, 3), round(b, 3)) for a, b in remain if b - a > 1e-6]
    return AllocResult(placements, rejected, free)

def result_to_dict(r: AllocResult) -> dict:
    return {
        "placements": [asdict(p) for p in r.placements],
        "rejected": [asdict(x) for x in r.rejected],
        "free_spans": [{"start_m": a, "end_m": b} for a, b in r.free_spans],
    }
