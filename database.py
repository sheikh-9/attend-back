# database.py

import os
from sqlalchemy import (
    create_engine, Column, BigInteger, Text,
    DateTime, Float, String, ForeignKey, Index, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# رابط قاعدة البيانات (مثبّت في متغير بيئة DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")

# إعداد المحرك وجلسة العمل
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# تعريف Base للجداول
Base = declarative_base()

def init_db():
    """
    ينشئ جميع الجداول المعرفة على Base في قاعدة البيانات
    """
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = "users"
    id             = Column(BigInteger, primary_key=True, index=True)
    national_id    = Column(Text, unique=True, nullable=False, index=True)
    password_hash  = Column(Text, nullable=False)
    role           = Column(String(10), nullable=False, default="user", index=True)  # 'admin' أو 'user'
    attendances    = relationship("Attendance", back_populates="user")
    sessions       = relationship("UserSession", back_populates="user")


class Attendance(Base):
    __tablename__ = "attendance"
    id           = Column(BigInteger, primary_key=True, index=True)
    user_id      = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    timestamp    = Column(
        DateTime(timezone=False),
        server_default=text("now()"),
        nullable=False
    )
    device_info  = Column(Text, nullable=False)
    type         = Column(String(10), nullable=False)  # 'in' أو 'out'
    latitude     = Column(Float, nullable=False)
    longitude    = Column(Float, nullable=False)

    user         = relationship("User", back_populates="attendances")
    __table_args__ = (
        Index("idx_attendance_date_only", text("date(timestamp)")),  # فهرس على التاريخ فقط
    )


class UserSession(Base):
    __tablename__ = "sessions"
    id           = Column(BigInteger, primary_key=True, index=True)
    user_id      = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    session_id   = Column(Text, unique=True, nullable=False, index=True)
    expires_at   = Column(DateTime(timezone=False), nullable=False)

    user         = relationship("User", back_populates="sessions")