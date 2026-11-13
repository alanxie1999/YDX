"""
模拟真实AI下注：调用 predict_next_bet_core + calculate_bet_amount 完整链路
用法：python3 模拟AI下注.py [局数] [模型ID]
- 历史数据用随机开奖模拟（也可在 SIM_RESULTS 里预设固定序列）
- 结算按 1% 抽水：赢 +amount*0.99，输 -amount
"""

import asyncio
import json
import os
import random
import sys

os.environ.setdefault("YDXBOT_VERBOSE_RUNTIME_LOGS", "")

import zq_multiuser as zq
from user_manager import UserContext, UserState

SIM_ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
MODEL_ID = sys.argv[2] if len(sys.argv) > 2 else "glm-5.3-flash"

# 预设开奖序列（None 则随机）；1=大 0=小
SIM_RESULTS = None
# SIM_RESULTS = [1,0,1,0,1,0,1,0] * 10  # 交替盘示例


class SimUserContext(UserContext):
    """绕过文件加载的轻量模拟上下文"""

    def __init__(self, model_id: str):
        self.user_dir = "users/_template"
        self.global_config = {}
        self.user_id = 9999
        self.account_slug = "sim"
        self._model_manager = None
        self._model_manager_ai_sig = ""
        self._lock = __import__("threading").Lock()

        from user_manager import UserConfig
        self.config = UserConfig(
            user_id=9999,
            name="模拟账号",
            ai={
                "enabled": True,
                "api_keys": ["83d77f78f8cc6bcc15cd2cc158b94d161f51"],
                "base_url": "http://106.53.71.101:8788/v1",
                "timeout": 60,
                "max_retries": 2,
                "models": {"1": {"model_id": model_id, "enabled": True}},
                "fallback_chain": ["1"],
            }
        )
        self.state = UserState()
        rt = self.state.runtime
        rt.update({
            "initial_amount": 500,
            "bet_amount": 500,
            "lose_stop": 13,
            "lose_once": 3.0,
            "lose_twice": 2.1,
            "lose_three": 2.1,
            "lose_four": 2.05,
            "current_model_id": model_id,
            "edb": False,
            "stat_fallback_bet_enabled": False,
        })

    def save_state(self):
        pass

    def get_model_manager(self):
        from model_manager import ModelManager
        if self._model_manager is None:
            self._model_manager = ModelManager()
        self._model_manager.apply_shared_config({"ai": dict(self.config.ai)})
        return self._model_manager


async def main():
    user_ctx = SimUserContext(MODEL_ID)
    state = user_ctx.state
    rt = state.runtime
    history = state.history
    random.seed()

    print("=" * 88)
    print(f"AI 真实链路模拟下注 | 模型: {MODEL_ID} | 局数: {SIM_ROUNDS} | 首注: 500 | 倍投: 3.0/2.1/2.1/2.05")
    print("=" * 88)
    print(f"{'局':<4} {'开奖':<5} {'预测':<6} {'来源':<14} {'置信':<5} {'下注':<9} {'盈亏':<9} {'累计':<10} 连输 说明")
    print("-" * 88)

    total = 0
    max_bet = 0
    win_n = lose_n = 0
    skipped = 0

    for rnd in range(1, SIM_ROUNDS + 1):
        prediction = await zq.predict_next_bet_core(user_ctx, {}, current_round=rnd)

        source = rt.get("last_predict_source", "")
        reason = rt.get("last_predict_reason", "")

        if prediction == -1 or rt.get("last_predict_source") in {"model_wait", "timeout_wait"}:
            skipped += 1
            print(f"{rnd:<4} {'-':<5} {'SKIP':<6} {source:<14} {'-':<5} {'0':<9} {'0':<9} {total:<10} {rt.get('lose_count',0)}  {reason[:26]}")
            result = random.randint(0, 1) if SIM_RESULTS is None else SIM_RESULTS[rnd - 1]
            history.append(result)
            continue

        bet_amount = zq.calculate_bet_amount(rt, history)
        if bet_amount <= 0:
            skipped += 1
            print(f"{rnd:<4} {'-':<5} {'STOP':<6} {source:<14} {'-':<5} {'0':<9} {'0':<9} {total:<10} {rt.get('lose_count',0)}  连输停止线触发")
            result = random.randint(0, 1) if SIM_RESULTS is None else SIM_RESULTS[rnd - 1]
            history.append(result)
            continue

        max_bet = max(max_bet, bet_amount)
        result = random.randint(0, 1) if SIM_RESULTS is None else SIM_RESULTS[rnd - 1]
        win = (result == prediction)

        if win:
            profit = int(bet_amount * 0.99)
            total += profit
            win_n += 1
            rt["win_count"] = rt.get("win_count", 0) + 1
            rt["lose_count"] = 0
            rt["bet_amount"] = int(rt.get("initial_amount", 500))
        else:
            profit = -bet_amount
            total += profit
            lose_n += 1
            rt["lose_count"] = rt.get("lose_count", 0) + 1
            rt["bet_amount"] = bet_amount

        rt["earnings"] = total
        side = lambda v: "大" if v == 1 else "小"
        mark = "赢" if win else "输"
        print(f"{rnd:<4} {side(result):<5} {side(prediction):<6} {source:<14} {rt.get('last_predict_confidence',0):<5} "
              f"{bet_amount:<9} {profit:+9d} {total:<10} {rt.get('lose_count',0)}  [{mark}] {reason[:24]}")

        state.bet_type_history.append(prediction)

    print("-" * 88)
    print(f"局数: {SIM_ROUNDS} | 赢: {win_n} | 输: {lose_n} | 跳过: {skipped} | 胜率: "
          f"{win_n / max(1, win_n + lose_n) * 100:.1f}%")
    print(f"总盈亏: {total:+d} | 最大单注: {max_bet} | 最终累计: {total:+d}")


if __name__ == "__main__":
    asyncio.run(main())
