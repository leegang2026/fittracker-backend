"""
锻炼相关路由：动作库 + 锻炼记录 + 统计
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import (
    ExerciseModel, ExerciseOut,
    WorkoutModel, WorkoutCreate, WorkoutOut, WorkoutStats,
)
from routers.auth import get_current_user, UserModel

router = APIRouter(prefix="/api", tags=["exercises"])


# ─── 动作库 ─────────────────────────────────────

@router.get("/exercises", response_model=list[ExerciseOut])
def list_exercises(
    is_preset: bool = True,
    db: Session = Depends(get_db),
):
    """获取动作列表（默认只返回预置动作）"""
    query = db.query(ExerciseModel)
    if is_preset is not None:
        query = query.filter(ExerciseModel.is_preset == is_preset)
    return query.all()


@router.get("/exercises/{exercise_id}", response_model=ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    ex = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="动作不存在")
    return ex


# ─── 锻炼记录 ───────────────────────────────────

@router.post("/workouts", response_model=WorkoutOut)
def create_workout(
    body: WorkoutCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录一次锻炼"""
    # 校验动作存在
    ex = db.query(ExerciseModel).filter(ExerciseModel.id == body.exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="动作不存在")

    w = WorkoutModel(
        user_id=user.id,
        exercise_id=body.exercise_id,
        duration_seconds=body.duration_seconds,
        reps=body.reps,
        score=body.score,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    # 填充 exercise_name
    out = WorkoutOut.model_validate(w)
    out.exercise_name = ex.name
    return out


@router.get("/workouts", response_model=list[WorkoutOut])
def list_workouts(
    limit: int = 20,
    exercise_id: int = None,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的锻炼记录"""
    query = db.query(WorkoutModel).filter(WorkoutModel.user_id == user.id)
    if exercise_id:
        query = query.filter(WorkoutModel.exercise_id == exercise_id)
    workouts = query.order_by(WorkoutModel.created_at.desc()).limit(limit).all()
    # 填充 exercise_name
    results = []
    for w in workouts:
        out = WorkoutOut.model_validate(w)
        ex = db.query(ExerciseModel).filter(ExerciseModel.id == w.exercise_id).first()
        out.exercise_name = ex.name if ex else ""
        results.append(out)
    return results


@router.get("/workouts/stats", response_model=WorkoutStats)
def get_stats(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的统计数据"""
    workouts = db.query(WorkoutModel).filter(
        WorkoutModel.user_id == user.id
    ).all()

    total = len(workouts)
    total_duration = sum(w.duration_seconds for w in workouts) / 60.0
    total_reps = sum(w.reps for w in workouts)
    avg_score = sum(w.score for w in workouts) / total if total > 0 else 0.0

    # 计算连续打卡天数
    streak = 0
    if workouts:
        # 收集所有有记录的日期
        record_dates = {w.created_at.date() for w in workouts}
        today = date.today()
        # 从今天往回数
        for i in range(365):
            check = today - timedelta(days=i)
            if check in record_dates:
                streak += 1
            else:
                break

    return WorkoutStats(
        total_workouts=total,
        total_duration_minutes=round(total_duration, 1),
        total_reps=total_reps,
        avg_score=round(avg_score, 1),
        current_streak=streak,
    )


@router.get("/user/streak", response_model=dict)
def get_streak(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取连续打卡天数（快捷接口）"""
    stats = get_stats(user=user, db=db)
    return {"streak": stats.current_streak, "total_workouts": stats.total_workouts}
