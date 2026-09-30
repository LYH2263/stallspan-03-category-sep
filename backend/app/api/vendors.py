from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import AllocationRun, Vendor
from app.services.categories import CATEGORIES, normalize_category

router = APIRouter(prefix="/vendors", tags=["vendors"])

class CategoryIn(BaseModel):
    category: str | None = None

def _serialize(r: Vendor) -> dict:
    # 未标品类回传 None；分配时仍按手作兼容处理
    return {"id": r.id, "market_day_id": r.market_day_id, "name": r.name,
            "stall_width_m": r.stall_width_m, "priority": r.priority,
            "category": r.category}

@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    return [_serialize(r)
            for r in db.scalars(select(Vendor).order_by(Vendor.priority, Vendor.id)).all()]

@router.put("/{vendor_id}")
def update_category(vendor_id: int, body: CategoryIn, db: Session = Depends(get_db)):
    v = db.get(Vendor, vendor_id)
    if not v:
        raise HTTPException(404, "摊主不存在")
    raw = body.category
    if raw is not None and str(raw).strip():
        cat = normalize_category(raw)
        if cat not in CATEGORIES:
            raise HTTPException(422, f"品类仅支持：{'、'.join(CATEGORIES)}")
        v.category = cat
    else:
        v.category = None  # 未标品类 → 按手作兼容
    # 品类变了，旧分配结果即作废，避免分配图/放不下仍按旧品类口径展示
    db.execute(delete(AllocationRun))
    db.commit()
    db.refresh(v)
    return _serialize(v)
