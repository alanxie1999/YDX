#!/usr/bin/env python3
"""模拟 st <预设> 连续下注 N 手（默认连续输 10 手），验证倍投金额链路是否正确。

复用真实链路：
- calculate_bet_amount()           计算本手下注金额
- _append_bet_sequence_entry()     写入真实下注日志
- _apply_inferred_settle_from_history() 按"输"结算并更新下一手基准

用法：
    python3 模拟st预设连输10手.py [预设名] [手数]
示例：
    python3 模拟st预设连输10手.py 5k 10
    python3 模拟st预设连输10手.py fix1000_0 10
"""

import argparse
import json
import tempfile
from pathlib import Path

import constants
import zq_multiuser as zm
from user_manager import UserContext


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_context(tmp_dir: Path) -> UserContext:
    user_dir = tmp_dir / "users" / "9001"
    _write_json(
        user_dir / "9001_config.json",
        {
            "account": {"name": "模拟用户"},
            "telegram": {"user_id": 9001},
            "groups": {"admin_chat": 9001},
            "notification": {"iyuu": {"enable": False}, "tg_bot": {"enable": False}},
            "admin_console": {
                "mode": "telegram_id",
                "telegram_id": {"chat_id": 9001},
                "telegram_bot": {"bot_token": "", "chat_id": "", "allowed_sender_ids": []},
            },
        },
    )
    return UserContext(str(user_dir))


def _apply_preset(rt: dict, preset: list) -> None:
    rt["continuous"] = int(preset[0])
    rt["lose_stop"] = int(preset[1])
    rt["lose_once"] = float(preset[2])
    rt["lose_twice"] = float(preset[3])
    rt["lose_three"] = float(preset[4])
    rt["lose_four"] = float(preset[5])
    rt["initial_amount"] = int(preset[6])
    rt["bet_direction"] = str(preset[7]) if len(preset) > 7 else "auto"
    rt["bet_amount"] = int(preset[6])
    rt["lose_count"] = 0
    rt["bet_sequence_count"] = 0
    rt["win_count"] = 0
    rt["current_bet_seq"] = 1
    rt["current_round"] = 1
    rt["mode_stop"] = True
    rt["bet_on"] = True
    rt["switch"] = True
    rt["bet"] = False


def simulate(preset_name: str, rounds: int, direction: int = 1) -> None:
    presets = dict(constants.PRESETS)
    if preset_name not in presets:
        print(f"预设 {preset_name} 不存在，可用：{', '.join(presets)}")
        return

    preset = presets[preset_name]
    lose_stop = int(preset[1])
    dir_label = "大" if direction == 1 else "小"
    print("=" * 78)
    print(f"预设: {preset_name}   参数: {' '.join(preset)}")
    print(f"连续输 {rounds} 手模拟（固定预测「{dir_label}」，开奖均相反）")
    print("=" * 78)

    tmp_dir = Path(tempfile.mkdtemp(prefix="st_sim_"))
    ctx = _build_context(tmp_dir)
    rt = ctx.state.runtime
    _apply_preset(rt, preset)

    print(f"{'手次':>3} {'本手下注':>12} {'下一手基准':>12} {'连输':>4} {'连投':>4} {'备注':<34}")
    print("-" * 78)
    for i in range(1, rounds + 1):
        amount = zm.calculate_bet_amount(rt)
        if amount <= 0:
            print(
                f"{i:>3} {'—':>12} {'—':>12} "
                f"{rt.get('lose_count', 0):>4} {rt.get('bet_sequence_count', 0):>4} "
                f"⛔ 已达连投上限(lose_stop={lose_stop})，停止下注"
            )
            break

        rt["bet_amount"] = amount
        rt["bet_sequence_count"] = int(rt.get("bet_sequence_count", 0)) + 1
        rt["bet_type"] = direction
        rt["current_bet_seq"] = int(rt.get("current_bet_seq", 1)) + 1
        bet_id = zm.generate_bet_id(ctx)
        entry = {
            "bet_id": bet_id,
            "sequence": rt.get("bet_sequence_count", 0),
            "direction": "big" if direction == 1 else "small",
            "amount": rt["bet_amount"],
            "result": None,
            "profit": 0,
            "lose_stop": rt.get("lose_stop", 13),
            "profit_target": rt.get("profit", 1000000),
        }
        zm._append_bet_sequence_entry(ctx.state, entry)

        inferred_result = 1 - direction
        outcome = zm._apply_inferred_settle_from_history(ctx.state, rt, entry, inferred_result)

        next_amount = int(outcome.get("next_bet_amount", 0) or 0)
        if next_amount <= 0:
            note = f"下一手停止（连投将达上限 {lose_stop}）"
        else:
            note = f"下一手将下注 {next_amount:,}"
        print(
            f"{i:>3} {amount:>12,} {rt['bet_amount']:>12,} "
            f"{outcome['lose_count_after']:>4} {outcome['sequence_after']:>4} {note}"
        )

    total_loss = sum(
        abs(int(e.get("profit", 0)))
        for e in ctx.state.bet_sequence_log
        if int(e.get("profit", 0) or 0) < 0
    )
    print("-" * 78)
    print(
        f"结算完成：已下注 {len(ctx.state.bet_sequence_log)} 手，累计亏损 {total_loss:,}，"
        f"当前连输 {rt.get('lose_count', 0)}，连投 {rt.get('bet_sequence_count', 0)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="模拟 st 预设连续输下注，验证倍投链路")
    parser.add_argument("preset", nargs="?", default="5k", help="内置预设名（默认 5k）")
    parser.add_argument("rounds", nargs="?", type=int, default=10, help="下注手数（默认 10）")
    parser.add_argument("--direction", type=int, default=1, choices=[0, 1], help="预测方向 1=大 0=小")
    args = parser.parse_args()
    simulate(args.preset, args.rounds, args.direction)


if __name__ == "__main__":
    main()
