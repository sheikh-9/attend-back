# routers/export_excel.py

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import SessionLocal
import io, pandas as pd

router = APIRouter()

# Dependency لإنشاء جلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/excel")
def export_excel(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date:   str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute("""
        SELECT u.national_id, a.timestamp, a.type
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.timestamp::date BETWEEN :s AND :e
        ORDER BY a.timestamp
    """, {"s": start_date, "e": end_date}).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="لا توجد بيانات في هذه الفترة")

    df = pd.DataFrame(rows, columns=["رقم الهوية", "الوقت", "نوع"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    buf.seek(0)

    filename = f"attendance_{start_date}_to_{end_date}.xlsx"
    return StreamingResponse(
        buf,
        media_type=(
            "application/"
            "vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )