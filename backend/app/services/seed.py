from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.models import MarketDay, Pillar, Segment, Vendor
from app.services.first_fit_engine import CATEGORY_FOOD, CATEGORY_HANDMADE

def seed_if_empty(db: Session) -> None:
    if (db.scalar(select(func.count()).select_from(MarketDay)) or 0) > 0:
        return
    day = MarketDay(name="周末夜市", day=date(2026, 9, 20))
    db.add(day); db.flush()
    seg = Segment(market_day_id=day.id, name="东街段", width_m=30.0)
    db.add(seg); db.flush()
    # 灯柱把街段切成三个柱间空档：[0,9.75] [10.25,19.75] [20.25,30]
    db.add(Pillar(segment_id=seg.id, position_m=10.0, thickness_m=0.5, label="灯柱A"))
    db.add(Pillar(segment_id=seg.id, position_m=20.0, thickness_m=0.5, label="灯柱B"))
    # (名称, 宽度, 优先级, 品类)。优先级即落位顺序，确保下面的相邻隔离可复现：
    # 阿强烧烤(餐饮)落 [0,4] 灯柱A左侧；手作皮具紧随其后，同空档与餐饮队尾
    # 直接相邻而被推开，落到灯柱A右侧 [10.25,13.75]——分属灯柱两侧空档，都可落。
    # 小美饰品(手作)在各空档剩余宽度处都与餐饮队尾相邻 → 放不下·品类相邻冲突；
    # 巨型舞台车超宽，任何柱间空档都放不下 → 放不下·无连续空档（跨柱/空档不足口径）。
    vendors = [
        ("阿强烧烤", 4.0, 1, CATEGORY_FOOD),
        ("手作皮具", 3.5, 2, CATEGORY_HANDMADE),
        ("林记糖水", 3.0, 3, CATEGORY_FOOD),
        ("大碗面", 6.0, 4, CATEGORY_FOOD),
        ("老周水果", 5.0, 5, CATEGORY_HANDMADE),
        ("小美饰品", 2.5, 6, CATEGORY_HANDMADE),
        ("巨型舞台车", 12.0, 9, CATEGORY_HANDMADE),
    ]
    for name, wdt, pri, cat in vendors:
        db.add(Vendor(market_day_id=day.id, name=name, stall_width_m=wdt, priority=pri, category=cat))
    db.commit()
