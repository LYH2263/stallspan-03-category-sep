"""1D First-Fit stall placement along a street segment; stalls cannot cross pillars.

同一挡柱切开的空档内，按落位顺序不得出现互斥品类（餐饮 / 手作）直接相邻；
中间隔着另一摊，或空档被挡柱切开，均不算相邻。后到的互斥品类若所有空档
都无法落位，进放不下，原因单独记为品类相邻冲突。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.categories import REASON_CATEGORY, REASON_SPAN, categories_conflict, normalize_category

@dataclass
class Placement:
    vendor_id: int
    vendor_name: str
    start_m: float
    end_m: float
    width_m: float
    category: str = ""

@dataclass
class Rejected:
    vendor_id: int
    vendor_name: str
    width_m: float
    reason: str
    category: str = ""

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
    """vendors sorted by priority ascending then id; each needs stall_width_m contiguous in one free span (no pillar cross).

    first-fit 沿每个空档的落位顺序从左到右紧贴摆放。在某个空档内，只有
    当前最右一摊与新摊直接相邻；品类互斥时该空档不可用，继续尝试后续空档
    （被挡柱切开的另一侧空档不算相邻）。所有空档都放不下时记放不下，
    空档尺寸不足与品类相邻冲突使用各自独立的原因，不并句。
    """
    spans = free_spans_from_pillars(width_m, pillars)
    # mutable remaining capacity per span
    remain = [[a, b] for a, b in spans]
    # 每个空档已落位的最右一摊品类（新摊只与它直接相邻）
    last_category: list[str | None] = [None] * len(remain)
    ordered = sorted(vendors, key=lambda v: (v.get("priority", 1), v["id"]))
    placements: list[Placement] = []
    rejected: list[Rejected] = []
    for v in ordered:
        need = float(v["stall_width_m"])
        category = normalize_category(v.get("category"))
        placed = False
        saw_space = False  # 是否存在尺寸足够但因品类互斥不能落的空档
        for i, span in enumerate(remain):
            avail = span[1] - span[0]
            if avail + 1e-9 < need:
                continue
            neighbor = last_category[i]
            if neighbor is not None and categories_conflict(neighbor, category):
                # 该空档宽度够，但放进去会与紧邻摊位品类冲突
                saw_space = True
                continue
            start = span[0]
            end = start + need
            placements.append(Placement(v["id"], v["name"], round(start, 3), round(end, 3), need, category))
            span[0] = end
            last_category[i] = category
            placed = True
            break
        if not placed:
            reason = REASON_CATEGORY if saw_space else REASON_SPAN
            rejected.append(Rejected(v["id"], v["name"], need, reason, category))
    free = [(round(a, 3), round(b, 3)) for a, b in remain if b - a > 1e-6]
    return AllocResult(placements, rejected, free)

def result_to_dict(r: AllocResult) -> dict:
    return {
        "placements": [asdict(p) for p in r.placements],
        "rejected": [asdict(x) for x in r.rejected],
        "free_spans": [{"start_m": a, "end_m": b} for a, b in r.free_spans],
    }
