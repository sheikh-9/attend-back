from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers.auth import router as auth_router
from routers.attendance import router as attendance_router
from routers.export_excel import router as export_router

app = FastAPI()

# تفعيل CORS للسماح بطلبات من الفرونت (ولتمرير الكوكيز)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # للإنتاج ضع هنا رابط فرونترك فقط، مثلاً ["https://hunterbukhari.github.io"]
    allow_credentials=True,     # مهم لتمرير الكوكيز
    allow_methods=["*"],
    allow_headers=["*"],
)

# إنشاء الجداول عند الإقلاع
init_db()

# تضمين الراوترات
app.include_router(auth_router,       prefix="/auth",       tags=["auth"])
app.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
app.include_router(export_router,     prefix="/export",     tags=["export"])