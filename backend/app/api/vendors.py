from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Vendor
from app.services.first_fit_engine import CATEGORY_LABELS, normalize_category

router = APIRouter(prefix="/vendors", tags=["vendors"])

# 可扩枚举：合法品类即 CATEGORY_LABELS 的键；空串视为未标（按手作兼容）
ALLOWED_CATEGORIES = set(CATEGORY_LABELS) | {""}


class VendorPatch(BaseModel):
    category: str | None = None


def serialize(r: Vendor) -> dict:
    return {"id": r.id, "market_day_id": r.market_day_id, "name": r.name,
            "stall_width_m": r.stall_width_m, "priority": r.priority,
            "category": normalize_category(r.category)}


@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    return [serialize(r) for r in db.scalars(select(Vendor).order_by(Vendor.priority, Vendor.id)).all()]


@router.patch("/{vendor_id}")
def update_vendor(vendor_id: int, body: VendorPatch, db: Session = Depends(get_db)):
    r = db.get(Vendor, vendor_id)
    if not r:
        raise HTTPException(404, "摊主不存在")
    if body.category is not None:
        cat = body.category.strip()
        if cat not in ALLOWED_CATEGORIES:
            raise HTTPException(422, f"未知品类：{body.category}（可选：{', '.join(CATEGORY_LABELS.values())}）")
        # 空串落库为默认手作，保证重新打开仍显示新值
        r.category = normalize_category(cat)
    db.commit(); db.refresh(r)
    return serialize(r)
