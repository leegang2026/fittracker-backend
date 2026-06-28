"""
FitTracker 后端入口
MVP Phase 1: 账户 + 动作库 + 锻炼记录
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, exercises
from seed_data import seed_preset_exercises


# ─── 启动/关闭生命周期 ────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    seed_preset_exercises()
    yield  # 关闭时无操作


# ─── 应用 ────────────────────────────────────

app = FastAPI(
    title="FitTracker",
    description="运动追踪 App 后端 (MVP)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(exercises.router)


@app.get("/")
def root():
    return {"app": "FitTracker", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
