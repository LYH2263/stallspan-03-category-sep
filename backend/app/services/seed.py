from datetime import date
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from app.models.models import MarketDay, Pillar, Segment, Vendor
from app.services.categories import CATEGORY_FOOD, CATEGORY_CRAFT

def seed_if_empty(db: Session) -> None:
    if (db.scalar(select(func.count()).select_from(MarketDay)) or 0) > 0:
        # 旧库（品类列后加）补齐种子口径：阿强烧烤=餐饮，手作皮具=手作
        _backfill_seed_categories(db)
        return
    day = MarketDay(name="周末夜市", day=date(2026, 9, 20))
    db.add(day); db.flush()
    # 灯柱A 落在 14m：左空档 13.75m 恰可容纳三个餐饮摊，
    # 手作皮具随后只能落到灯柱另一侧空档，与阿强烧烤隔柱相望、两侧都可见。
    seg = Segment(market_day_id=day.id, name="东街段", width_m=30.0)
    db.add(seg); db.flush()
    db.add(Pillar(segment_id=seg.id, position_m=14.0, thickness_m=0.5, label="灯柱A"))
    db.add(Pillar(segment_id=seg.id, position_m=20.0, thickness_m=0.5, label="灯柱B"))
    # (name, width, priority, category)；category=None 表示未标，按手作兼容
    vendors = [
        ("阿强烧烤", 4.0, 1, CATEGORY_FOOD),
        ("林记糖水", 3.0, 1, CATEGORY_FOOD),
        ("老周水果", 5.0, 2, None),
        ("小美饰品", 2.5, 2, None),
        ("大碗面", 6.0, 1, CATEGORY_FOOD),
        ("手作皮具", 3.5, 3, CATEGORY_CRAFT),
        ("巨型舞台车", 12.0, 9, None),
    ]
    for name, wdt, pri, cat in vendors:
        db.add(Vendor(market_day_id=day.id, name=name, stall_width_m=wdt, priority=pri, category=cat))
    db.commit()

def _backfill_seed_categories(db: Session) -> None:
    """让早于品类功能建库的环境也满足种子口径（仅补这两个具名摊）。"""
    if db.execute(text("SELECT 1 FROM vendors WHERE name = :n AND category IS NULL"),
                  {"n": "阿强烧烤"}).first():
        db.execute(text("UPDATE vendors SET category = :c WHERE name = :n AND category IS NULL"),
                   {"c": CATEGORY_FOOD, "n": "阿强烧烤"})
    if db.execute(text("SELECT 1 FROM vendors WHERE name = :n AND category IS NULL"),
                  {"n": "手作皮具"}).first():
        db.execute(text("UPDATE vendors SET category = :c WHERE name = :n AND category IS NULL"),
                   {"c": CATEGORY_CRAFT, "n": "手作皮具"})
    db.commit()
