#!/usr/bin/env python3
"""下注逻辑模拟测试脚本"""

FIXED_PATTERN_TRIGGER_WINDOW = 5
FIXED_PATTERNS = {
    "010101": {"follow": "reverse", "label": "交替循环反转"},
    "101010": {"follow": "reverse", "label": "交替循环反转"},
    "111111": {"follow": "1", "label": "大龙延续"},
    "000000": {"follow": "0", "label": "小龙延续"},
    "00101": {"follow": "reverse", "label": "00101反向下注"},
    "11010": {"follow": "reverse", "label": "11010反向下注"},
}

ALTERNATION_BREAK_TRIGGER_WINDOW = 6
ALTERNATION_BREAK_PATTERNS = {"010101", "101010"}


def _get_history_tail_streak(history):
    """返回历史尾部连庄信息：(连庄长度, 连庄方向0/1)。"""
    if not isinstance(history, list) or not history:
        return 0, -1
    try:
        tail_value = int(history[-1])
    except Exception:
        return 0, -1
    streak = 1
    for idx in range(len(history) - 2, -1, -1):
        try:
            current = int(history[idx])
        except Exception:
            break
        if current != tail_value:
            break
        streak += 1
    return streak, tail_value


def _get_dragon_extra_bet_amount(rt, history=None):
    """6连以上长龙期间，每次下注额外加250000，直到不中后停止。"""
    if rt.get("lose_count", 0) > 0:
        rt["dragon_extra_active"] = False
        rt["dragon_tail_streak"] = 0
        return 0

    if history is None:
        history = rt.get("_history_cache", [])
    else:
        rt["_history_cache"] = history

    if not isinstance(history, list) or len(history) < 6:
        rt["dragon_extra_active"] = False
        return 0

    streak, _ = _get_history_tail_streak(history)

    if streak >= 6:
        rt["dragon_extra_active"] = True
        rt["dragon_tail_streak"] = streak
        return 250000

    if rt.get("dragon_extra_active", False):
        return 250000

    return 0


def simulate_dragon_extra(history_sequence, description=""):
    """模拟长龙额外加注逻辑"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"{'='*60}")
    print(f"历史序列: {' '.join(str(x) for x in history_sequence)}")
    
    rt = {"lose_count": 0, "dragon_extra_active": False}
    
    for i in range(len(history_sequence)):
        current_history = history_sequence[:i]
        next_actual = history_sequence[i]
        
        extra = _get_dragon_extra_bet_amount(rt, current_history)
        streak, side = _get_history_tail_streak(current_history)
        
        if extra > 0:
            print(f"  第{i+1}手: 尾连{streak} -> 额外加注+250000 [龙尾方向{'大' if side==1 else '小'}]")
        else:
            print(f"  第{i+1}手: 尾连{streak} -> 无额外加注")
        
        # 模拟结果：如果预测错误，设置 lose_count > 0
        # 这里假设我们预测与龙尾同向
        if streak >= 6:
            prediction = side
            if prediction != next_actual:
                rt["lose_count"] = 1
                print(f"         -> 预测错误，停止额外加注")


# 测试用例
print("长龙额外加注逻辑模拟测试")
print("="*60)

# 测试 1: 6连大后额外加注
simulate_dragon_extra([0, 1, 0, 1, 1, 1, 1, 1, 1, 1], "6连大后额外加注")

# 测试 2: 7连小后额外加注
simulate_dragon_extra([1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], "7连小后额外加注")

# 测试 3: 长龙中断后停止加注
print(f"\n{'='*60}")
print("测试: 长龙中断后停止加注")
print(f"{'='*60}")
history = [1, 1, 1, 1, 1, 1, 1, 0, 1, 1]  # 7连大后断掉
rt = {"lose_count": 0, "dragon_extra_active": False}
for i in range(len(history)):
    current_history = history[:i]
    next_actual = history[i]
    
    extra = _get_dragon_extra_bet_amount(rt, current_history)
    streak, side = _get_history_tail_streak(current_history)
    
    if extra > 0:
        print(f"  第{i+1}手: [{ ''.join(str(x) for x in current_history[-8:]) }] 尾连{streak} -> 额外加注+250000")
    else:
        reason = "龙尾不足6连" if streak < 6 else "已中断"
        print(f"  第{i+1}手: [{ ''.join(str(x) for x in current_history[-8:]) }] 尾连{streak} -> 无额外加注 ({reason})")
    
    if streak >= 6:
        prediction = side
        if prediction != next_actual:
            rt["lose_count"] = 1
            print(f"         -> 预测错误，后续停止加注")
