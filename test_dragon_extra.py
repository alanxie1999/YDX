#!/usr/bin/env python3
import zq_multiuser as zm


def _dragon_extra_rt(**overrides):
    rt = {
        "edb": True,
        "win_count": 0,
        "lose_count": 0,
        "initial_amount": 5000,
        "bet_amount": 5000,
        "lose_stop": 13,
        "lose_once": 3.0,
        "lose_twice": 2.5,
        "lose_three": 2.2,
        "lose_four": 2.1,
        "dragon_extra_active": False,
    }
    rt.update(overrides)
    return rt


def test_same_direction():
    history = [0, 1, 1, 1, 1, 1, 1]
    signal = zm._detect_dragon_extra_signal(history)
    assert signal["active"] is True
    assert signal["kind"] == "same"
    assert signal["direction"] == 1
    rt = _dragon_extra_rt()
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert rt["dragon_extra_active"] is True
    assert zm._apply_dragon_extra_direction(rt, history, 0) == 1
    assert zm.calculate_bet_amount(rt, history) == 1_005_000
    print("ok same")


def test_alternation():
    history = [1, 0, 1, 0, 1, 0]
    signal = zm._detect_dragon_extra_signal(history)
    assert signal["active"] is True
    assert signal["kind"] == "alt"
    assert signal["direction"] == 1
    rt = _dragon_extra_rt()
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert zm._apply_dragon_extra_direction(rt, history, 0) == 1
    print("ok alt")


def test_keep_after_win():
    history = [1, 1, 1, 1, 1, 1]
    rt = _dragon_extra_rt()
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    history = history + [1]
    rt["win_count"] = 1
    rt["lose_count"] = 0
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert rt["dragon_extra_active"] is True
    assert zm.calculate_bet_amount(rt, history) == 1_005_000
    print("ok win continue")


def test_stop_after_miss():
    history = [1, 1, 1, 1, 1, 1]
    rt = _dragon_extra_rt()
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    zm._clear_dragon_extra_runtime(rt)
    broken = history + [0]
    assert zm._get_dragon_extra_bet_amount(rt) == 0
    assert zm._get_dragon_extra_bet_amount(rt, broken) == 0
    assert rt["dragon_extra_active"] is False
    assert zm.calculate_bet_amount(rt, broken) == 5_000
    print("ok miss stop")


def test_after_six_losses():
    history = [0, 1, 1, 1, 1, 1, 1]
    rt = _dragon_extra_rt(lose_count=6, bet_amount=225_000)
    extra = zm._get_dragon_extra_bet_amount(rt, history)
    assert extra == 1_000_000
    assert rt["dragon_extra_active"] is True
    total = zm.calculate_bet_amount(rt, history)
    assert total > 1_000_000
    assert zm._apply_dragon_extra_direction(rt, history, 0) == 1
    print("ok after 6 losses")


def test_mt_mode_same_dragon_bets_same_direction():
    history = [0, 1, 1, 1, 1, 1, 1]
    rt = _dragon_extra_rt(bet_direction="reverse")
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert rt["dragon_extra_active"] is True
    assert zm._apply_dragon_extra_direction(rt, history, 0) == 1
    print("ok mt same dragon")


def test_mt_mode_ignores_alternation_dragon():
    history = [1, 0, 1, 0, 1, 0]
    rt = _dragon_extra_rt(bet_direction="reverse")
    assert zm._get_dragon_extra_bet_amount(rt, history) == 0
    assert rt["dragon_extra_active"] is False
    assert zm._apply_dragon_extra_direction(rt, history, 1) == 1
    print("ok mt ignores alt")


def test_st_mode_alt_dragon_bets_alternation():
    history = [1, 0, 1, 0, 1, 0]
    rt = _dragon_extra_rt(bet_direction="same")
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert rt["dragon_extra_active"] is True
    assert zm._apply_dragon_extra_direction(rt, history, 0) == 1
    print("ok st alt dragon")


def test_st_mode_ignores_same_dragon():
    history = [0, 1, 1, 1, 1, 1, 1]
    rt = _dragon_extra_rt(bet_direction="same")
    assert zm._get_dragon_extra_bet_amount(rt, history) == 0
    assert rt["dragon_extra_active"] is False
    print("ok st ignores same")


def test_fixed_direction_keeps_preset_side():
    history = [0, 0, 0, 0, 0, 0]
    rt = _dragon_extra_rt(bet_direction="1")
    assert zm._get_dragon_extra_bet_amount(rt, history) == 1_000_000
    assert rt["dragon_extra_active"] is True
    assert zm._apply_dragon_extra_direction(rt, history, 1) == 1
    print("ok fixed direction")


if __name__ == "__main__":
    test_same_direction()
    test_alternation()
    test_keep_after_win()
    test_stop_after_miss()
    test_after_six_losses()
    test_mt_mode_same_dragon_bets_same_direction()
    test_mt_mode_ignores_alternation_dragon()
    test_st_mode_alt_dragon_bets_alternation()
    test_st_mode_ignores_same_dragon()
    test_fixed_direction_keeps_preset_side()
    print("all passed")
