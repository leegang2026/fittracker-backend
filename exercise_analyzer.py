"""
FitTracker — 姿态检测与分析服务
核心逻辑：基于 MediaPipe Pose 关键点进行动作分析
"""

import math
from typing import Optional

# ─── 关键点索引（MediaPipe Pose 33个关键点）───
# 常用关键点
NOSE = 0
LEFT_EYE_INNER = 1
LEFT_EYE = 2
LEFT_EYE_OUTER = 3
RIGHT_EYE_INNER = 4
RIGHT_EYE = 5
RIGHT_EYE_OUTER = 6
LEFT_EAR = 7
RIGHT_EAR = 8
MOUTH_LEFT = 9
MOUTH_RIGHT = 10
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_PINKY = 17
RIGHT_PINKY = 18
LEFT_INDEX = 19
RIGHT_INDEX = 20
LEFT_THUMB = 21
RIGHT_THUMB = 22
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32


class Landmark:
    """单个关键点"""
    def __init__(self, x: float, y: float, z: float, visibility: float = 1.0):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


def angle_between(a: Landmark, b: Landmark, c: Landmark) -> float:
    """计算三点夹角（度），以 b 为顶点"""
    ab = math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
    bc = math.sqrt((c.x - b.x)**2 + (c.y - b.y)**2)
    dot = (a.x - b.x) * (c.x - b.x) + (a.y - b.y) * (c.y - b.y)
    if ab * bc == 0:
        return 0
    cos_angle = dot / (ab * bc)
    cos_angle = max(-1, min(1, cos_angle))
    return math.degrees(math.acos(cos_angle))


def vertical_angle(a: Landmark, b: Landmark) -> float:
    """计算线段 a-b 与垂直方向的夹角（度）"""
    dx = a.x - b.x
    dy = a.y - b.y
    if abs(dy) < 0.001:
        return 90
    return abs(math.degrees(math.atan(dx / dy)))


def horizontal_distance(a: Landmark, b: Landmark) -> float:
    """计算两个关键点的水平距离"""
    return abs(a.x - b.x)


class ExerciseState:
    """动作状态机"""
    IDLE = "idle"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    def __init__(self):
        self.state = self.IDLE
        self.rep_count = 0
        self.has_been_ready = False

    def reset(self):
        self.state = self.IDLE
        self.rep_count = 0
        self.has_been_ready = False


def analyze_plank(landmarks: dict) -> dict:
    """分析平板支撑姿态
    
    检测要点：肩-髋-踝 连线垂直偏差 < 8°
    """
    result = {"score": 100, "deviation": None, "is_correct": True}
    
    required = [LEFT_SHOULDER, LEFT_HIP, LEFT_ANKLE,
                RIGHT_SHOULDER, RIGHT_HIP, RIGHT_ANKLE]
    if not all(i in landmarks for i in required):
        return result
    
    ls = landmarks[LEFT_SHOULDER]
    lh = landmarks[LEFT_HIP]
    la = landmarks[LEFT_ANKLE]
    
    # 肩-髋-踝 角度（理想为 180° 直线）
    angle = angle_between(ls, lh, la)
    deviation = abs(180 - angle)
    
    if deviation > 8:
        result["deviation"] = f"身体弯曲 {deviation:.0f}°，请保持直线"
        result["is_correct"] = False
        result["score"] = max(0, 100 - deviation * 3)
    
    return result


def analyze_wall_stand(landmarks: dict) -> dict:
    """分析靠墙站立姿态
    
    检测要点：后脑/肩/臀/脚跟 近似直线
    """
    result = {"score": 100, "deviation": None, "is_correct": True}
    
    required = [LEFT_SHOULDER, LEFT_HIP, LEFT_ANKLE,
                RIGHT_SHOULDER, RIGHT_HIP, RIGHT_ANKLE]
    if not all(i in landmarks for i in required):
        return result
    
    # 使用右肩-右髋-右踝 垂直偏差
    rs = landmarks[RIGHT_SHOULDER]
    rh = landmarks[RIGHT_HIP]
    ra = landmarks[RIGHT_ANKLE]
    
    angle = angle_between(rs, rh, ra)
    deviation = abs(180 - angle)
    
    if deviation > 5:
        result["deviation"] = f"身体倾斜 {deviation:.0f}°，请调整"
        result["is_correct"] = False
        result["score"] = max(0, 100 - deviation * 4)
    
    return result


def analyze_bridge(landmarks: dict, state: ExerciseState) -> dict:
    """分析臀桥动作并计数
    
    状态机：仰卧 → 抬起（肩-髋-膝直线）→ 落下 → +1
    """
    result = {"score": 100, "deviation": None, "is_correct": True,
              "rep_count": state.rep_count, "rep_event": False}
    
    required = [LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE]
    if not all(i in landmarks for i in required):
        return result
    
    lsh = landmarks[LEFT_SHOULDER]
    lh = landmarks[LEFT_HIP]
    lk = landmarks[LEFT_KNEE]
    la = landmarks[LEFT_ANKLE]
    
    # 髋-膝-踝 角度（抬起时接近 180°）
    hip_angle = angle_between(lh, lk, la)
    # 肩-髋-膝 角度（抬起时接近 180°）
    body_angle = angle_between(lsh, lh, lk)
    
    # 判断是否抬起（髋-膝-踝 > 150° 且 肩-髋-膝 > 150°）
    is_raised = hip_angle > 150 and body_angle > 150
    # 判断是否落下（髋-膝-踝 < 120°）
    is_lowered = hip_angle < 120
    
    if state.state == ExerciseState.IDLE:
        if is_raised:
            state.state = ExerciseState.IN_PROGRESS
            state.has_been_ready = True
    elif state.state == ExerciseState.IN_PROGRESS:
        if is_lowered:
            state.rep_count += 1
            state.state = ExerciseState.IDLE
            result["rep_count"] = state.rep_count
            result["rep_event"] = True
        elif not is_raised:
            # 中间状态过渡
            pass
    
    if not is_raised and state.state == ExerciseState.IDLE:
        result["deviation"] = "请抬起臀部至肩-膝一线"
        result["is_correct"] = False
    
    return result


def analyze_superman(landmarks: dict, state: ExerciseState) -> dict:
    """分析小燕飞动作并计数
    
    状态机：俯卧 → 抬起（胸、腿离地）→ 落下 → +1
    """
    result = {"score": 100, "deviation": None, "is_correct": True,
              "rep_count": state.rep_count, "rep_event": False}
    
    required = [NOSE, LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE]
    if not all(i in landmarks for i in required):
        return result
    
    nose = landmarks[NOSE]
    ls = landmarks[LEFT_SHOULDER]
    lh = landmarks[LEFT_HIP]
    lk = landmarks[LEFT_KNEE]
    la = landmarks[LEFT_ANKLE]
    
    # 躯干角度（肩-髋-膝）
    body_angle = angle_between(ls, lh, lk)
    # 鼻-肩 垂直距离（抬头程度）
    nose_shoulder_vert = abs(nose.y - ls.y)
    
    # 判断抬起：躯干角度 > 170° 近似直线 且 鼻子上抬
    is_raised = body_angle > 160 and nose_shoulder_vert > 0.03
    # 判断落下：身体回落到平直
    is_lowered = body_angle < 145
    
    if state.state == ExerciseState.IDLE:
        if is_raised:
            state.state = ExerciseState.IN_PROGRESS
    elif state.state == ExerciseState.IN_PROGRESS:
        if is_lowered and state.has_been_ready:
            state.rep_count += 1
            state.state = ExerciseState.IDLE
            result["rep_count"] = state.rep_count
            result["rep_event"] = True
        state.has_been_ready = True
    
    if not is_raised and state.state == ExerciseState.IDLE:
        result["deviation"] = "请抬起胸部和双腿"
        result["is_correct"] = False
    
    return result


def analyze_bird_dog(landmarks: dict, state: ExerciseState) -> dict:
    """分析鸟狗式动作并计数
    
    状态机：四点支撑 → 对侧手脚伸展 → 收回 → +1
    """
    result = {"score": 100, "deviation": None, "is_correct": True,
              "rep_count": state.rep_count, "rep_event": False}
    
    required = [LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
                LEFT_WRIST, RIGHT_WRIST, LEFT_KNEE, RIGHT_KNEE,
                LEFT_ANKLE, RIGHT_ANKLE]
    if not all(i in landmarks for i in required):
        return result
    
    lw = landmarks[LEFT_WRIST]
    rw = landmarks[RIGHT_WRIST]
    lk = landmarks[LEFT_KNEE]
    rk = landmarks[RIGHT_KNEE]
    ls = landmarks[LEFT_SHOULDER]
    rs = landmarks[RIGHT_SHOULDER]
    lh = landmarks[LEFT_HIP]
    rh = landmarks[RIGHT_HIP]
    la = landmarks[LEFT_ANKLE]
    ra = landmarks[RIGHT_ANKLE]
    
    # 左右腕距离（伸展时加大）
    wrist_dist = abs(lw.x - rw.x)
    # 肩-髋 夹角
    body_twist = abs(angle_between(ls, lh, rh) - 180)
    
    # 判断伸展：手腕间距 > 阈值 且 躯干无明显扭转
    is_extended = wrist_dist > 0.15 and body_twist < 20
    # 判断收回：手腕靠近
    is_retracted = wrist_dist < 0.08
    
    if state.state == ExerciseState.IDLE:
        if is_extended:
            state.state = ExerciseState.IN_PROGRESS
    elif state.state == ExerciseState.IN_PROGRESS:
        if is_retracted and state.has_been_ready:
            state.rep_count += 1
            state.state = ExerciseState.IDLE
            result["rep_count"] = state.rep_count
            result["rep_event"] = True
        state.has_been_ready = True
    
    if not is_extended and state.state == ExerciseState.IDLE:
        result["deviation"] = "请伸展对侧手脚"
        result["is_correct"] = False
    if body_twist > 20:
        result["deviation"] = "身体过度旋转，请保持稳定"
        result["is_correct"] = False
    
    return result


def analyze_side_leg_raise(landmarks: dict, state: ExerciseState, side="left") -> dict:
    """分析侧卧抬腿动作并计数
    
    状态机：侧卧 → 抬腿（~45°）→ 落下 → +1
    """
    result = {"score": 100, "deviation": None, "is_correct": True,
              "rep_count": state.rep_count, "rep_event": False}
    
    hip_key = LEFT_HIP if side == "left" else RIGHT_HIP
    knee_key = LEFT_KNEE if side == "left" else RIGHT_KNEE
    ankle_key = LEFT_ANKLE if side == "left" else RIGHT_ANKLE
    shoulder_key = LEFT_SHOULDER if side == "left" else RIGHT_SHOULDER
    
    required = [shoulder_key, hip_key, knee_key, ankle_key]
    if not all(i in landmarks for i in required):
        return result
    
    # 躯干直线度
    body_angle = angle_between(
        landmarks[shoulder_key],
        landmarks[hip_key],
        landmarks[knee_key]
    )
    
    # 抬腿角度（大腿与垂直方向的夹角）
    leg_angle = vertical_angle(landmarks[knee_key], landmarks[ankle_key])
    
    # 判断抬起到位（> 30° 与垂直方向夹角）
    is_raised = leg_angle > 30
    # 判断落下（< 10°）
    is_lowered = leg_angle < 10
    
    if state.state == ExerciseState.IDLE:
        if is_raised:
            state.state = ExerciseState.IN_PROGRESS
    elif state.state == ExerciseState.IN_PROGRESS:
        if is_lowered and state.has_been_ready:
            state.rep_count += 1
            state.state = ExerciseState.IDLE
            result["rep_count"] = state.rep_count
            result["rep_event"] = True
        state.has_been_ready = True
    
    # 偏差检测：躯干是否稳定
    if abs(180 - body_angle) > 15:
        result["deviation"] = "躯干不稳定，请保持侧卧不动"
        result["is_correct"] = False
    
    return result
