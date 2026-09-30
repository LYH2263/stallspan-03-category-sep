from app.services.first_fit_engine import (
    REASON_CATEGORY,
    REASON_SPACE,
    allocate_first_fit,
    categories_conflict,
    free_spans_from_pillars,
    normalize_category,
)

FOOD = "food"
HAND = "handmade"
PILLARS_AB = [{"position_m": 10.0, "thickness_m": 0.5}, {"position_m": 20.0, "thickness_m": 0.5}]


def v(id, name, w, pri, category=HAND):
    return {"id": id, "name": name, "stall_width_m": w, "priority": pri, "category": category}


def by_name(r, name):
    return next((p for p in r.placements if p.vendor_name == name), None)


def rejected_by_name(r, name):
    return next((x for x in r.rejected if x.vendor_name == name), None)


def test_free_spans_with_pillars():
    spans = free_spans_from_pillars(30.0, PILLARS_AB)
    assert len(spans) == 3
    assert spans[0][0] == 0.0


def test_first_fit_no_cross_pillar():
    vendors = [
        {"id": 1, "name": "A", "stall_width_m": 4.0, "priority": 1, "category": HAND},
        {"id": 2, "name": "B", "stall_width_m": 12.0, "priority": 1, "category": HAND},
    ]
    pillars = [{"position_m": 10.0, "thickness_m": 0.5}]
    r = allocate_first_fit(30.0, vendors, pillars)
    assert any(p.vendor_name == "A" for p in r.placements)
    # 12m may fit in a free span after first placement depending on remainders
    assert len(r.placements) + len(r.rejected) == 2


def test_reject_oversized():
    vendors = [{"id": 1, "name": "Huge", "stall_width_m": 25.0, "priority": 1, "category": HAND}]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    assert len(r.rejected) == 1
    assert r.rejected[0].vendor_name == "Huge"
    assert r.rejected[0].reason == REASON_SPACE


def test_unmarked_defaults_to_handmade():
    assert normalize_category(None) == HAND
    assert normalize_category("") == HAND
    assert categories_conflict(None, FOOD) is True
    assert categories_conflict("", HAND) is False


def test_same_category_may_be_adjacent():
    # 两个手作在同一空档紧挨，全部落位
    vendors = [v(1, "H1", 4.0, 1, HAND), v(2, "H2", 4.0, 2, HAND)]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    assert len(r.placements) == 2
    assert r.placements[1].start_m == 4.0  # 紧接队尾
    assert not r.rejected


def test_conflicting_category_pushed_to_next_span_across_pillar():
    # 餐饮先占灯柱A左侧，后到手作不得在同空档紧挨 → 被推到灯柱A右侧空档，二者都落
    vendors = [v(1, "阿强烧烤", 4.0, 1, FOOD), v(2, "手作皮具", 3.5, 2, HAND)]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    a_qiang = by_name(r, "阿强烧烤")
    pi_ju = by_name(r, "手作皮具")
    assert a_qiang and pi_ju
    assert not r.rejected
    # 阿强在灯柱A左（end 不越过柱的左缘 9.75），皮具在灯柱A右（start >= 10.25）
    assert a_qiang.start_m == 0.0 and a_qiang.end_m <= 9.75
    assert pi_ju.start_m >= 10.25


def test_late_conflicting_category_rejected_with_category_reason():
    # 三个空档队尾都被餐饮占据（各自仍留有余宽），后到手作在各空档虽放得下
    # 却都会直接相邻 → 品类冲突
    vendors = [
        v(1, "F1", 7.0, 1, FOOD),  # S1 [0,7] 余 2.75
        v(2, "F2", 7.0, 2, FOOD),  # S2 [10.25,17.25] 余 2.5
        v(3, "F3", 7.0, 3, FOOD),  # S3 [20.25,27.25] 余 2.75
        v(4, "手作尾巴", 2.0, 4, HAND),
    ]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    x = rejected_by_name(r, "手作尾巴")
    assert x is not None
    assert x.reason == REASON_CATEGORY
    # 原因不得与跨柱/空档不足并句
    assert REASON_SPACE not in x.reason


def test_category_conflict_distinct_from_space_reason():
    # 三个空档队尾都是餐饮且各留 ≥3m 余宽，3m 手作放得下却处处直接相邻 → 品类冲突；
    # 同时超宽摊走空档不足口径——两条原因各自独立、不并句。
    vendors = [
        v(1, "F1", 6.5, 1, FOOD),  # S1 余 3.25
        v(2, "F2", 6.5, 2, FOOD),  # S2 余 3.0
        v(3, "F3", 6.5, 3, FOOD),  # S3 余 3.25
        v(4, "手作", 3.0, 4, HAND),
        v(5, "巨型舞台车", 12.0, 9, HAND),
    ]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    hand = rejected_by_name(r, "手作")
    huge = rejected_by_name(r, "巨型舞台车")
    assert hand and hand.reason == REASON_CATEGORY
    assert huge and huge.reason == REASON_SPACE
    assert hand.reason != huge.reason


def test_seed_scenario_layout():
    # 复刻 seed_if_empty 的摊主集合，验证题目要求的灯柱两侧可见性
    vendors = [
        v(1, "阿强烧烤", 4.0, 1, FOOD),
        v(2, "手作皮具", 3.5, 2, HAND),
        v(3, "林记糖水", 3.0, 3, FOOD),
        v(4, "大碗面", 6.0, 4, FOOD),
        v(5, "老周水果", 5.0, 5, HAND),
        v(6, "小美饰品", 2.5, 6, HAND),
        v(7, "巨型舞台车", 12.0, 9, HAND),
    ]
    r = allocate_first_fit(30.0, vendors, PILLARS_AB)
    a_qiang = by_name(r, "阿强烧烤")
    pi_ju = by_name(r, "手作皮具")
    # 分属灯柱A两侧空档，图上两侧都能看见
    assert a_qiang and pi_ju
    assert a_qiang.end_m <= 9.75 and pi_ju.start_m >= 10.25
    # 小美饰品：品类相邻冲突；舞台车：空档不足
    assert rejected_by_name(r, "小美饰品").reason == REASON_CATEGORY
    assert rejected_by_name(r, "巨型舞台车").reason == REASON_SPACE
    # 每个已落位摊都不与同空档队尾互斥（不变式自检）
    placed = sorted(r.placements, key=lambda p: p.start_m)
    for prev, cur in zip(placed, placed[1:]):
        same_span = (prev.start_m < 9.75 and cur.start_m < 9.75) or \
                    (10.25 <= prev.start_m <= 19.75 and 10.25 <= cur.start_m <= 19.75) or \
                    (prev.start_m >= 20.25 and cur.start_m >= 20.25)
        if same_span:
            assert not categories_conflict(prev.category, cur.category)
