from app.services.categories import REASON_CATEGORY, REASON_SPAN, normalize_category
from app.services.first_fit_engine import allocate_first_fit, free_spans_from_pillars

def test_free_spans_with_pillars():
    spans = free_spans_from_pillars(30.0, [{"position_m": 10.0, "thickness_m": 0.5}, {"position_m": 20.0, "thickness_m": 0.5}])
    assert len(spans) == 3
    assert spans[0][0] == 0.0

def test_first_fit_no_cross_pillar():
    vendors = [
        {"id": 1, "name": "A", "stall_width_m": 4.0, "priority": 1, "category": "餐饮"},
        {"id": 2, "name": "B", "stall_width_m": 12.0, "priority": 1, "category": "餐饮"},
    ]
    pillars = [{"position_m": 10.0, "thickness_m": 0.5}]
    r = allocate_first_fit(30.0, vendors, pillars)
    assert any(p.vendor_name == "A" for p in r.placements)
    # 12m may fit in a free span after first placement depending on remainders
    assert len(r.placements) + len(r.rejected) == 2

def test_reject_oversized():
    vendors = [{"id": 1, "name": "Huge", "stall_width_m": 25.0, "priority": 1, "category": "餐饮"}]
    pillars = [{"position_m": 10.0, "thickness_m": 0.5}, {"position_m": 20.0, "thickness_m": 0.5}]
    r = allocate_first_fit(30.0, vendors, pillars)
    assert len(r.rejected) == 1
    assert r.rejected[0].vendor_name == "Huge"
    assert r.rejected[0].reason == REASON_SPAN

def test_unmarked_category_defaults_to_craft():
    assert normalize_category(None) == "手作"
    assert normalize_category("") == "手作"
    vendors = [
        {"id": 1, "name": "手作摊", "stall_width_m": 2.0, "priority": 1, "category": "手作"},
        {"id": 2, "name": "未标摊", "stall_width_m": 2.0, "priority": 1, "category": None},
    ]
    r = allocate_first_fit(10.0, vendors, [])
    assert len(r.placements) == 2  # 未标按手作，与手作紧邻不冲突

def test_incompatible_categories_adjacent_in_same_span_rejected():
    # 同一柱间空档内，手作先落、餐饮后到且只能紧挨 → 品类相邻冲突
    vendors = [
        {"id": 1, "name": "手作皮具", "stall_width_m": 3.0, "priority": 1, "category": "手作"},
        {"id": 2, "name": "阿强烧烤", "stall_width_m": 3.0, "priority": 2, "category": "餐饮"},
    ]
    r = allocate_first_fit(10.0, vendors, [])
    assert len(r.placements) == 1
    assert r.placements[0].vendor_name == "手作皮具"
    assert len(r.rejected) == 1
    assert r.rejected[0].vendor_name == "阿强烧烤"
    assert r.rejected[0].reason == REASON_CATEGORY

def test_categories_on_opposite_sides_of_pillar_both_place():
    # 分属挡柱两侧空档：互斥品类不相邻，二者都可落且一左一右
    vendors = [
        {"id": 1, "name": "手作皮具", "stall_width_m": 3.0, "priority": 1, "category": "手作"},
        {"id": 2, "name": "阿强烧烤", "stall_width_m": 4.0, "priority": 2, "category": "餐饮"},
    ]
    pillars = [{"position_m": 5.0, "thickness_m": 0.4}]
    r = allocate_first_fit(10.0, vendors, pillars)
    assert len(r.rejected) == 0
    assert [p.vendor_name for p in r.placements] == ["手作皮具", "阿强烧烤"]
    assert r.placements[0].end_m <= 4.8
    assert r.placements[1].start_m >= 5.2
    assert {p.category for p in r.placements} == {"手作", "餐饮"}

def test_category_conflict_uses_its_own_reason_not_merged():
    # 两个空档都够宽，但各自紧邻位都是互斥品类 → 品类原因，且不得与跨柱/空档不足并句
    vendors = [
        {"id": 1, "name": "手1", "stall_width_m": 3.0, "priority": 1, "category": "手作"},
        {"id": 2, "name": "手2", "stall_width_m": 3.0, "priority": 1, "category": "手作"},
        {"id": 3, "name": "餐", "stall_width_m": 1.0, "priority": 2, "category": "餐饮"},
    ]
    pillars = [{"position_m": 5.0, "thickness_m": 0.4}]
    r = allocate_first_fit(12.0, vendors, pillars)
    assert len(r.rejected) == 1
    reason = r.rejected[0].reason
    assert reason == REASON_CATEGORY
    # 不与跨柱、空档不足并句：不得出现「跨越挡柱」「放不下」等空档原因措辞
    assert "跨越" not in reason and "放不下" not in reason
    assert reason != REASON_SPAN

def test_insufficient_space_reason_not_category():
    # 宽度真的不够（非品类原因）→ 空档原因，不写品类冲突
    vendors = [
        {"id": 1, "name": "手作", "stall_width_m": 4.5, "priority": 1, "category": "手作"},
        {"id": 2, "name": "餐饮", "stall_width_m": 4.5, "priority": 2, "category": "餐饮"},
    ]
    pillars = [{"position_m": 5.5, "thickness_m": 0.4}]  # 右空档仅 4.3m
    r = allocate_first_fit(10.0, vendors, pillars)
    assert len(r.rejected) == 1
    assert r.rejected[0].reason == REASON_SPAN

def test_later_same_category_still_places_between():
    # 中间隔着另一摊：餐饮-餐饮 可连续；后到手作紧挨餐饮被拒，原因单列
    vendors = [
        {"id": 1, "name": "餐1", "stall_width_m": 2.0, "priority": 1, "category": "餐饮"},
        {"id": 2, "name": "手", "stall_width_m": 2.0, "priority": 2, "category": "手作"},
        {"id": 3, "name": "餐2", "stall_width_m": 2.0, "priority": 3, "category": "餐饮"},
    ]
    r = allocate_first_fit(20.0, vendors, [])
    assert [p.vendor_name for p in r.placements] == ["餐1", "餐2"]
    assert r.rejected[0].vendor_name == "手"
    assert r.rejected[0].reason == REASON_CATEGORY

def test_seed_named_vendors_split_by_pillar():
    # 种子口径：阿强烧烤(餐饮) 与 手作皮具(手作) 不能在同一柱间空档紧挨；
    # 灯柱A 切开后二者分属两侧空档，都能落、图上两侧都可见。
    vendors = [
        {"id": 1, "name": "阿强烧烤", "stall_width_m": 4.0, "priority": 1, "category": "餐饮"},
        {"id": 2, "name": "林记糖水", "stall_width_m": 3.0, "priority": 1, "category": "餐饮"},
        {"id": 3, "name": "老周水果", "stall_width_m": 5.0, "priority": 2, "category": None},
        {"id": 4, "name": "小美饰品", "stall_width_m": 2.5, "priority": 2, "category": None},
        {"id": 5, "name": "大碗面", "stall_width_m": 6.0, "priority": 1, "category": "餐饮"},
        {"id": 6, "name": "手作皮具", "stall_width_m": 3.5, "priority": 3, "category": "手作"},
        {"id": 7, "name": "巨型舞台车", "stall_width_m": 12.0, "priority": 9, "category": None},
    ]
    pillars = [{"position_m": 14.0, "thickness_m": 0.5}, {"position_m": 20.0, "thickness_m": 0.5}]
    r = allocate_first_fit(30.0, vendors, pillars)
    by_name = {p.vendor_name: p for p in r.placements}
    assert "阿强烧烤" in by_name and "手作皮具" in by_name
    assert by_name["阿强烧烤"].end_m <= 13.75
    assert by_name["手作皮具"].start_m >= 14.25
    # 没有任何摊因品类冲突被拒
    assert all(x.reason != REASON_CATEGORY for x in r.rejected)
