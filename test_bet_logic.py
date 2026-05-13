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


def detect_fixed_pattern(history, window=FIXED_PATTERN_TRIGGER_WINDOW):
    """检测固定数据序列信号"""
    if not isinstance(history, list) or len(history) < window:
        return {"active": False}

    near_to_far = [int(x) for x in history[-window:]]
    seq = "".join(str(x) for x in near_to_far)

    if seq not in FIXED_PATTERNS:
        return {"active": False}

    pattern_info = FIXED_PATTERNS[seq]
    follow_pattern = pattern_info["follow"]
    label = pattern_info["label"]
    latest_value = int(near_to_far[-1])

    if follow_pattern == "reverse":
        prediction = 1 - latest_value
    elif len(follow_pattern) == 1:
        prediction = int(follow_pattern)
    else:
        prediction = latest_value

    return {
        "active": True,
        "detected_seq": seq,
        "window": window,
        "follow_pattern": follow_pattern,
        "label": label,
        "prediction": prediction,
    }


def detect_alternation_break(history, window=ALTERNATION_BREAK_TRIGGER_WINDOW):
    """检测纯交替信号"""
    if not isinstance(history, list) or len(history) < window:
        return {"active": False}

    near_to_far = [int(x) for x in history[-window:]]
    seq = "".join(str(x) for x in near_to_far)

    if seq not in ALTERNATION_BREAK_PATTERNS:
        return {"active": False}

    latest_value = int(near_to_far[-1])
    prediction = latest_value  # 同向

    return {
        "active": True,
        "detected_seq": seq,
        "label": "纯交替同向",
        "prediction": prediction,
    }


def simulate_bet(history_sequence, description=""):
    """模拟下注过程"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"{'='*60}")
    print(f"历史序列: {' '.join(str(x) for x in history_sequence)}")

    for i in range(len(history_sequence)):
        current_history = history_sequence[:i]
        next_actual = history_sequence[i]

        fixed_signal = detect_fixed_pattern(current_history)
        alt_signal = detect_alternation_break(current_history)

        prediction = None
        trigger_type = None

        if fixed_signal.get("active"):
            prediction = fixed_signal["prediction"]
            trigger_type = f"固定规律({fixed_signal['label']})"
        elif alt_signal.get("active"):
            prediction = alt_signal["prediction"]
            trigger_type = f"交替增强({alt_signal['label']})"

        if prediction is not None:
            match = "✓" if prediction == next_actual else "✗"
            pred_text = "大(1)" if prediction == 1 else "小(0)"
            actual_text = "大(1)" if next_actual == 1 else "小(0)"
            print(f"  第{i+1}手: 检测最近{len(current_history[-5:])}位 -> 预测{pred_text}, 实际{actual_text} {match} [{trigger_type}]")
        else:
            print(f"  第{i+1}手: 无触发, 实际开出{'大(1)' if next_actual == 1 else '小(0)'}")


# 测试用例
print("下注逻辑模拟测试")
print("="*60)

# 测试 1: 00101 反向下注
simulate_bet([0, 0, 1, 0, 1, 0], "00101 触发反向下注（应预测 0）")

# 测试 2: 11010 反向下注
simulate_bet([1, 1, 0, 1, 0, 1], "11010 触发反向下注（应预测 1）")

# 测试 3: 010101 交替同向
simulate_bet([0, 1, 0, 1, 0, 1, 1], "010101 交替同向（应预测 1）")

# 测试 4: 101010 交替同向
simulate_bet([1, 0, 1, 0, 1, 0, 0], "101010 交替同向（应预测 0）")

# 测试 5: 混合场景
print(f"\n{'='*60}")
print("测试: 混合场景 - 00101 反向 + 后续演变")
print(f"{'='*60}")
history = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
for i in range(len(history)):
    current_history = history[:i]
    next_actual = history[i]

    fixed_signal = detect_fixed_pattern(current_history)
    alt_signal = detect_alternation_break(current_history)

    prediction = None
    trigger_type = None

    if fixed_signal.get("active"):
        prediction = fixed_signal["prediction"]
        trigger_type = f"固定规律({fixed_signal['label']})"
    elif alt_signal.get("active"):
        prediction = alt_signal["prediction"]
        trigger_type = f"交替增强({alt_signal['label']})"

    if prediction is not None:
        match = "✓" if prediction == next_actual else "✗"
        pred_text = "大(1)" if prediction == 1 else "小(0)"
        actual_text = "大(1)" if next_actual == 1 else "小(0)"
        seq_str = ''.join(str(x) for x in current_history[-6:])
        print(f"  第{i+1}手: [{seq_str}] -> 预测{pred_text}, 实际{actual_text} {match} [{trigger_type}]")
    else:
        seq_str = ''.join(str(x) for x in current_history[-6:]) if len(current_history) >= 6 else ''.join(str(x) for x in current_history)
        print(f"  第{i+1}手: [{seq_str}] -> 无触发, 实际{'大(1)' if next_actual == 1 else '小(0)'}")
