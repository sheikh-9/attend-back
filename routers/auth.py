from fastapi import APIRouter, HTTPException, Response, Depends, Cookie
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import uuid
from datetime import datetime, timedelta
from database import SessionLocal
from pydantic import BaseModel

router = APIRouter()
SESSION_DURATION = timedelta(minutes=15)

# Dependency لقاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# نموذج استقبال بيانات تسجيل الدخول من JSON
class LoginRequest(BaseModel):
    national_id: str
    password: str

@router.post("/login")
def login(
    req: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    # تحقق من المستخدم
    row = db.execute(
        "SELECT id, password_hash, role FROM users WHERE national_id = :nid",
        {"nid": req.national_id}
    ).fetchone()
    if not row or not bcrypt.verify(req.password, row.password_hash):
        raise HTTPException(401, "بيانات الدخول غير صحيحة")

    # إنشاء session وتخزينه مع صلاحية 15 دقيقة
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + SESSION_DURATION
    db.execute(
        "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (:sid, :uid, :exp)",
        {"sid": session_id, "uid": row.id, "exp": expires_at}
    )
    db.commit()

    # إرسال الكوكي للمتصفح
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="strict",
        secure=False,            # أثناء التطوير، في الإنتاج اجعلها True
        expires=int(expires_at.timestamp())
    )

    return {"message": "تم تسجيل الدخول بنجاح", "role": row.role}

# Dependency لاستخراج user_id من الكوكي والتحقق من الصلاحية
def get_current_user(
    session_id: str = Cookie(None),
    db: Session = Depends(get_db)
) -> int:
    if not session_id:
        raise HTTPException(401, "لم يتم تسجيل الدخول")
    row = db.execute(
        "SELECT user_id, expires_at FROM sessions WHERE session_id = :sid",
        {"sid": session_id}
    ).fetchone()
    if not row or row.expires_at < datetime.utcnow():
        raise HTTPException(401, "الجلسة منتهية أو غير صالحة")
    return row.user_id

# Dependency للتحقق من صلاحية الأدمن
def get_current_admin(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    role_row = db.execute(
        "SELECT role FROM users WHERE id = :uid",
        {"uid": user_id}
    ).fetchone()
    if not role_row or role_row.role != "admin":
        raise HTTPException(403, "ليس لديك صلاحيات المدير")
    return user_id

# مسار اختياري لاختبار الجلسة
@router.get("/me")
def me(user_id: int = Depends(get_current_user)):
    return {"user_id": user_id}