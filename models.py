"""
FitTracker 数据模型
SQLAlchemy ORM + Pydantic 验证
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from database import Base

# ─── ORM 模型 ─────────────────────────────────────────────


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workouts = relationship("WorkoutModel", back_populates="user")


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)         # "timed" / "reps"
    target = Column(Integer, nullable=False)           # 目标秒数 或 目标次数
    category = Column(String(50), nullable=False)      # 核心 / 臀腿 / 背
    instructions = Column(Text, default="")             # 图文教程（Markdown）
    cover_image_url = Column(String(500), default="")
    is_preset = Column(Boolean, default=True)           # 预置动作 / 自定义
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkoutModel(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    duration_seconds = Column(Integer, default=0)
    reps = Column(Integer, default=0)
    score = Column(Float, default=0.0)                   # 0-100 综合评分
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="workouts")


# ─── Pydantic Schema ──────────────────────────────────────

from pydantic import BaseModel, Field


# -- Auth --
class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


# -- Exercise --
class ExerciseOut(BaseModel):
    id: int
    name: str
    type: str
    target: int
    category: str
    instructions: str
    cover_image_url: str
    is_preset: bool

    class Config:
        from_attributes = True


# -- Workout --
class WorkoutCreate(BaseModel):
    exercise_id: int
    duration_seconds: int = 0
    reps: int = 0
    score: float = 0.0


class WorkoutOut(BaseModel):
    id: int
    user_id: int
    exercise_id: int
    exercise_name: str = ""  # 通过 JOIN 查询填充
    duration_seconds: int
    reps: int
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutStats(BaseModel):
    """统计聚合"""
    total_workouts: int
    total_duration_minutes: float
    total_reps: int
    avg_score: float
    current_streak: int       # 连续打卡天数
