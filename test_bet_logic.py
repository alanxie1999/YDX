#!/usr/bin/env python3
"""下注逻辑模拟测试脚本"""

FIXED_PATTERNS = {
    "010101": {"follow": "reverse", "label": "交替循环反转"},
    "101010": {"follow": "reverse", "label": "交替循环反转"},
    "111111": {"follow": "1", "label": "大龙延续"},
    "000000": {"follow": "0", "label": "小龙延续"},
    "00101": {"follow": "reverse", "label": "00101反向下注"},
    "11010": {"follow": "reverse", "label": "11010反向下注"},
    "001010": {"follow": "same", "label": "001010同向下注"},
    "110101": {"follow": "same", "label": "110101同向下注"},
}


def _detect_fixed_pattern_signal(history):
    """识别固定数据序列信号，并给出相应的下注方向。支持不同长度的模式。"""
    if not isinstance(history, list) or len(history) < 5:
        return {"active": False}

    history_str = "".join(str(x) for x in history)

    for pattern, config in FIXED_PATTERNS.items():
        pattern_len = len(pattern)
        if len(history) < pattern_len:
            continue

        recent_seq = history_str[-pattern_len:]
        if recent_seq == pattern:
            follow_pattern = config["follow"]
            label = config["label"]
            latest_value = int(history[-1])

            if follow_pattern == "reverse":
                prediction = 1 - latest_value
            elif follow_pattern == "same":
                prediction = latest_value
            elif len(follow_pattern) == 1:
                prediction = int(follow_pattern)
            else:
                prediction = latest_value

            return {
                "active": True,
                "detected_seq": recent_seq,
                "window": pattern_len,
                "follow_pattern": follow_pattern,
                "label": label,
                "prediction": prediction,
            }

    return {"active": False}


def simulate_pattern(history_sequence, description=""):
    """模拟下注过程"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"{'='*60}")
    print(f"历史序列: {' '.join(str(x) for x in history_sequence)}")

    for i in range(len(history_sequence)):
        current_history = history_sequence[:i]
        next_actual = history_sequence[i]

        signal = _detect_fixed_pattern_signal(current_history)

        if signal.get("active"):
            prediction = signal["prediction"]
            match = "✓" if prediction == next_actual else "✗"
            pred_text = "大(1)" if prediction == 1 else "小(0)"
            actual_text = "大(1)" if next_actual == 1 else "小(0)"
            seq_str = ''.join(str(x) for x in current_history[-signal['window']:])
            follow_text = "反向" if signal['follow_pattern'] == 'reverse' else ("同向" if signal['follow_pattern'] == 'same' else "固定")
            print(f"  第{i+1}手: [{seq_str}] -> 预测{pred_text}({follow_text}), 实际{actual_text} {match} [{signal['label']}]")
        else:
            seq_str = ''.join(str(x) for x in current_history[-7:]) if len(current_history) >= 7 else ''.join(str(x) for x in current_history)
            print(f"  第{i+1}手: [{seq_str}] -> 无触发, 实际{'大(1)' if next_actual == 1 else '小(0)'}")


# 测试用例
print("固定规律下注逻辑模拟测试")
print("="*60)

# 测试 1: 001010 同向下注
simulate_pattern([0, 0, 1, 0, 1, 0, 0], "001010 触发同向下注（应预测 0）")

# 测试 2: 110101 同向下注
simulate_pattern([1, 1, 0, 1, 0, 1, 1], "110101 触发同向下注（应预测 1）")

# 测试 3: 00101 反向下注
simulate_pattern([0, 0, 1, 0, 1, 0], "00101 触发反向下注（应预测 0）")

# 测试 4: 11010 反向下注
simulate_pattern([1, 1, 0, 1, 0, 1], "11010 触发反向下注（应预测 1）")
