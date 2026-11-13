"""
三模型同盘面对比测试：glm-5.3 vs deepseek-v4-pro vs kimi-k3.1-pro
- 所有模型使用同一份固定开奖序列（60局，混合长龙/交替/乱盘）
- 每局只考"方向判断"（SKIP 记 0 分不计胜负），不含倍投
- 评分：命中率、SKIP 率、平均置信度
"""
import asyncio
import json
import random
import sys

import zq_multiuser as zq
from user_manager import UserState

MODELS = ["glm-5.3", "deepseek-v4-pro", "kimi-k3.1-pro"]
ROUNDS = 60

# 固定考题：随机种子固定生成，混合形态（长龙段/交替段/随机段）
rng = random.Random(20260813)
RESULTS = []
# 前20局：随机盘
RESULTS += [rng.randint(0, 1) for _ in range(20)]
# 中间20局：长龙偏多（70%大）
RESULTS += [1 if rng.random() < 0.7 else 0 for _ in range(20)]
# 后20局：交替偏多
for i in range(20):
    if i == 0:
        RESULTS.append(rng.randint(0, 1))
    else:
        RESULTS.append(1 - RESULTS[-1] if rng.random() < 0.75 else rng.randint(0, 1))


class BenchUserContext:
    def __init__(self, model_id: str):
        import threading
        from user_manager import UserConfig
        self.user_dir = "users/_template"
        self.global_config = {}
        self.user_id = 9999
        self.account_slug = "bench"
        self._model_manager = None
        self._model_manager_ai_sig = ""
        self._lock = threading.Lock()
        self.config = UserConfig(
            user_id=9999,
            name="评测账号",
            ai={
                "enabled": True,
                "api_keys": ["83d77f78f8cc6bcc15cd2cc158b94d161f51"],
                "base_url": "http://106.53.71.101:8788/v1",
                "timeout": 90,
                "max_retries": 2,
                "models": {"1": {"model_id": model_id, "enabled": True}},
                "fallback_chain": ["1"],
            },
        )
        self.state = UserState()
        rt = self.state.runtime
        rt.update({
            "initial_amount": 500,
            "bet_amount": 500,
            "lose_stop": 13,
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


async def run_model(model_id: str, results: list):
    ctx = BenchUserContext(model_id)
    history = ctx.state.history
    hits = misses = skips = errors = 0
    conf_sum = 0
    conf_n = 0
    detail = []
    for rnd in range(1, len(results) + 1):
        try:
            pred = await zq.predict_next_bet_core(ctx, {}, current_round=rnd)
        except Exception:
            errors += 1
            pred = 0
        src = str(ctx.state.runtime.get("last_predict_source", ""))
        conf = int(ctx.state.runtime.get("last_predict_confidence", 0) or 0)
        reason = str(ctx.state.runtime.get("last_predict_reason", ""))[:20]
        if pred == -1 or src in zq.MODEL_WAIT_SOURCES or src in {"hard_fallback", "fallback", "fallback_skip"}:
            skips += 1
            detail.append((rnd, "SKIP", "-", "-", reason))
        else:
            actual = results[rnd - 1]
            if pred == actual:
                hits += 1
                detail.append((rnd, "中", pred, actual, reason))
            else:
                misses += 1
                detail.append((rnd, "错", pred, actual, reason))
            conf_sum += conf
            conf_n += 1
        history.append(results[rnd - 1])
    hit_rate = hits / max(1, hits + misses)
    return {
        "model": model_id,
        "hits": hits,
        "misses": misses,
        "skips": skips,
        "errors": errors,
        "hit_rate": hit_rate,
        "avg_conf": conf_sum / max(1, conf_n),
        "detail": detail,
    }


async def main():
    print(f"固定考题 {ROUNDS} 局 | 前段随机/中段偏大长龙/后段偏交替")
    print("开奖序列:", "".join(str(x) for x in RESULTS))
    print("=" * 90)

    tasks = {m: asyncio.create_task(run_model(m, RESULTS)) for m in MODELS}
    results = {}
    for m, t in tasks.items():
        results[m] = await t

    print(f"\n{'模型':<22} {'命中':<6} {'失误':<6} {'SKIP':<6} {'异常':<6} {'命中率':<9} {'平均置信度'}")
    print("-" * 90)
    for m in MODELS:
        r = results[m]
        print(f"{r['model']:<22} {r['hits']:<6} {r['misses']:<6} {r['skips']:<6} {r['errors']:<6} "
              f"{r['hit_rate']*100:<8.1f}% {r['avg_conf']:.0f}")

    print("\n--- 每局明细（前20局）---")
    for m in MODELS:
        r = results[m]
        print(f"\n[{r['model']}]")
        for rnd, mark, pred, actual, reason in r["detail"][:20]:
            print(f"  局{rnd:<3} {mark:<4} 预测={pred} 实际={actual}  {reason}")

    best = max(MODELS, key=lambda m: results[m]["hit_rate"])
    print(f"\n>>> 命中率最高: {best} ({results[best]['hit_rate']*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
