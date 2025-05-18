# routers/attendance.py

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic import BaseModel, confloat
from datetime import datetime
from routers.auth import get_current_user

router = APIRouter()

# نموذج لبيانات الموقع
class Location(BaseModel):
    latitude:  confloat(ge=-90,  le=90)
    longitude: confloat(ge=-180, le=180)

# Dependency لإنشاء جلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# تسجيل حضور (in)
# ----------------------------------------
@router.post("/check-in")
def check_in(
    loc: Location = Body(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    # منع التكرار في نفس اليوم
    exists = db.execute(
        """
        SELECT 1 FROM attendance
        WHERE user_id=:uid AND timestamp::date=:d AND type='in'
        """,
        {"uid": user_id, "d": today}
    ).fetchone()
    if exists:
        raise HTTPException(status_code=400, detail="تم تسجيل الحضور اليوم مسبقاً")

    db.execute(
        """
        INSERT INTO attendance
          (user_id, device_info, type, latitude, longitude)
        VALUES
          (:uid, 'web', 'in', :lat, :lng)
        """,
        {"uid": user_id, "lat": loc.latitude, "lng": loc.longitude}
    )
    db.commit()
    return {"message": "تم تسجيل الحضور", "location": loc.dict()}

# ----------------------------------------
# تسجيل انصراف (out)
# ----------------------------------------
@router.post("/check-out")
def check_out(
    loc: Location = Body(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    # تأكد من وجود in
    has_in = db.execute(
        """
        SELECT 1 FROM attendance
        WHERE user_id=:uid AND timestamp::date=:d AND type='in'
        """,
        {"uid": user_id, "d": today}
    ).fetchone()
    if not has_in:
        raise HTTPException(status_code=400, detail="لم تسجل حضور اليوم")

    # تأكد من عدم وجود out مسبق
    has_out = db.execute(
        """
        SELECT 1 FROM attendance
        WHERE user_id=:uid AND timestamp::date=:d AND type='out'
        """,
        {"uid": user_id, "d": today}
    ).fetchone()
    if has_out:
        raise HTTPException(status_code=400, detail="تم تسجيل الانصراف اليوم مسبقاً")

    db.execute(
        """
        INSERT INTO attendance
          (user_id, device_info, type, latitude, longitude)
        VALUES
          (:uid, 'web', 'out', :lat, :lng)
        """,
        {"uid": user_id, "lat": loc.latitude, "lng": loc.longitude}
    )
    db.commit()
    return {"message": "تم تسجيل الانصراف", "location": loc.dict()}