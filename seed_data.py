"""
种子数据：初始化 6 个预置动作
"""

from database import SessionLocal
from models import ExerciseModel

PRESET_EXERCISES = [
    {
        "name": "平板支撑",
        "type": "timed",
        "target": 60,
        "category": "核心",
        "instructions": (
            "### 平板支撑\n\n"
            "**要点**\n"
            "- 双肘撑地，与肩同宽\n"
            "- 身体成一条直线，**肩-髋-踝**保持对齐\n"
            "- 核心收紧，避免塌腰或弓背\n"
            "- 自然呼吸，不要憋气\n\n"
            "**常见错误**\n"
            "- ❌ 塌腰：髋部下坠，腰部受力过大\n"
            "- ❌ 耸肩：肩胛骨没有收紧\n\n"
            "**拍摄角度**：侧面，手机放在侧边地板上仰拍\n"
            "**检测要点**：肩-髋-踝连线偏差 > 8° 提醒"
        ),
        "cover_image_url": "",
    },
    {
        "name": "靠墙站立",
        "type": "timed",
        "target": 120,
        "category": "体态",
        "instructions": (
            "### 靠墙站立\n\n"
            "**要点**\n"
            "- 后脑勺、肩胛骨、臀部、脚后跟四点贴墙\n"
            "- 下巴微收，目视前方\n"
            "- 自然呼吸，保持放松\n\n"
            "**常见错误**\n"
            "- ❌ 骨盆前倾：腰距墙面过远\n"
            "- ❌ 探头：下巴前伸\n\n"
            "**拍摄角度**：侧面\n"
            "**检测要点**：后脑/肩/臀/脚跟 任一点距墙 > 3cm 提醒"
        ),
        "cover_image_url": "",
    },
    {
        "name": "臀桥",
        "type": "reps",
        "target": 15,
        "category": "臀腿",
        "instructions": (
            "### 臀桥\n\n"
            "**要点**\n"
            "- 仰卧屈膝，双脚与肩同宽\n"
            "- 臀部发力抬起，至**肩-髋-膝**呈一直线\n"
            "- 顶峰收紧臀部 1-2 秒后缓慢下落\n\n"
            "**常见错误**\n"
            "- ❌ 腰代偿：下背过度发力而非臀部\n"
            "- ❌ 幅度不够：髋部没有抬到肩-膝一线\n\n"
            "**拍摄角度**：侧面\n"
            "**检测要点**：髋部上升→顶峰→下降，计 1 次"
        ),
        "cover_image_url": "",
    },
    {
        "name": "小燕飞",
        "type": "reps",
        "target": 12,
        "category": "背",
        "instructions": (
            "### 小燕飞\n\n"
            "**要点**\n"
            "- 俯卧，双臂前伸或置于身侧\n"
            "- 胸部和大腿同时离地\n"
            "- 顶峰保持 1-2 秒后缓慢下落\n\n"
            "**常见错误**\n"
            "- ❌ 幅度过大：腰过度反弓\n"
            "- ❌ 速度过快：用惯性而非肌肉控制\n\n"
            "**拍摄角度**：侧面或俯拍（手机架高）\n"
            "**检测要点**：胸部离地→顶峰→下落，计 1 次"
        ),
        "cover_image_url": "",
    },
    {
        "name": "鸟狗式",
        "type": "reps",
        "target": 10,
        "category": "核心",
        "instructions": (
            "### 鸟狗式\n\n"
            "**要点**\n"
            "- 四点支撑，手在肩下、膝在髋下\n"
            "- 对侧手和腿同时伸展（左臂+右腿 或 右臂+左腿）\n"
            "- 保持核心稳定，躯干不旋转\n"
            "- 两侧各 10 次为一组\n\n"
            "**常见错误**\n"
            "- ❌ 身体旋转：伸展时髋部翻转\n"
            "- ❌ 同侧伸展：伸出了同侧手脚\n\n"
            "**拍摄角度**：侧面\n"
            "**检测要点**：对侧手脚伸展→收回，计 1 次"
        ),
        "cover_image_url": "",
    },
    {
        "name": "侧卧抬腿",
        "type": "reps",
        "target": 15,
        "category": "臀腿",
        "instructions": (
            "### 侧卧抬腿\n\n"
            "**要点**\n"
            "- 侧卧，下方腿微屈，上方腿伸直\n"
            "- 上方腿直腿抬起，至约 45°\n"
            "- 骨盆不前倾不后倾\n"
            "- 缓慢下落，全程控制\n\n"
            "**常见错误**\n"
            "- ❌ 骨盆旋转：抬腿时骨盆向后翻转\n"
            "- ❌ 用髋屈肌代偿：上身晃动\n\n"
            "**拍摄角度**：侧面\n"
            "**检测要点**：腿上抬→下落，计 1 次"
        ),
        "cover_image_url": "",
    },
]


def seed_preset_exercises():
    """安全插入：已存在的预置动作跳过"""
    db = SessionLocal()
    try:
        existing = db.query(ExerciseModel).filter(
            ExerciseModel.is_preset == True
        ).count()
        if existing >= len(PRESET_EXERCISES):
            return  # 已种子化

        for ex in PRESET_EXERCISES:
            existing_one = db.query(ExerciseModel).filter(
                ExerciseModel.name == ex["name"],
                ExerciseModel.is_preset == True,
            ).first()
            if not existing_one:
                db.add(ExerciseModel(**ex, is_preset=True))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_preset_exercises()
    print("种子数据初始化完成！")
