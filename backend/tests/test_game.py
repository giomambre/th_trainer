from copy import deepcopy
import random

import pytest

from th_trainer.game import Hand, RANKS, SUITS, evaluate, describe_hand, CATEGORIES


@pytest.mark.parametrize("cards,expected", [
    ("As Ks Qs Js Ts 2d 3c", (8, 14)),
    ("As Ah Ad Ac Ks 2d 3c", (7, 14, 13)),
    ("As Ah Ad Ks Kh Kd 3c", (6, 14, 13)),
    ("As Js 9s 6s 2s Kh Kd", (5, 14, 11, 9, 6, 2)),
    ("As 2h 3d 4c 5s Kh Kd", (4, 5)),
    ("As Ah Ad Ks Qh 2d 3c", (3, 14, 13, 12)),
    ("As Ah Ks Kh Qh Qd 3c", (2, 14, 13, 12)),
    ("As Ah Ks Qh Jd 4d 3c", (1, 14, 13, 12, 11)),
    ("As Ks Qh Jd 9c 4d 3c", (0, 14, 13, 12, 11, 9)),
])
def test_best_five_of_seven(cards, expected):
    assert evaluate(cards.split()) == expected
    visible = cards.split()
    description = describe_hand(visible[:2], visible[2:])
    assert description["name"] == CATEGORIES[expected[0]]
    assert evaluate(description["cards"]) == expected


def test_hand_description_preflop_and_on_incomplete_board():
    assert describe_hand(["Ah", "As"], [])["detail"] == "Coppia di assi nelle tue carte."
    assert describe_hand(["As", "Ks"], [])["name"] == "A / K suited"
    assert describe_hand(["As", "Kh"], [])["name"] == "A / K offsuit"
    flop = describe_hand(["Qs", "Ad"], ["Qh", "2c", "5s"])
    assert flop["name"] == "One pair"
    assert flop["detail"] == "Coppia di donne."
    assert len(flop["cards"]) == 5
    turn = describe_hand(["Qs", "Ad"], ["Qh", "2c", "5s", "Ac"])
    assert turn["name"] == "Two pair"
    assert turn["detail"] == "Doppia coppia: assi e donne."


def test_description_identifies_when_the_board_plays():
    board = ["As", "Ks", "Qs", "Js", "Ts"]
    description = describe_hand(["2c", "3d"], board)
    assert description["name"] == "Straight flush"
    assert description["board_plays"]
    assert set(description["cards"]) == set(board)


def test_big_blind_option_and_postflop_order():
    hand = Hand.new()
    assert hand.state["actor"] == 0
    assert hand.legal()["call"] == 1
    assert hand.legal()["raise_min"] == 4
    before = deepcopy(hand.state)
    with pytest.raises(ValueError):
        hand.act(0, "check")
    assert hand.state == before
    with pytest.raises(ValueError):
        hand.act(1, "call")
    hand.act(0, "call")
    assert hand.state["street"] == "preflop"
    assert hand.state["actor"] == 1
    assert hand.legal()["check"]
    hand.act(1, "check")
    assert hand.state["street"] == "flop"
    assert hand.state["actor"] == 1
    assert len(hand.state["board"]) == 3
    assert hand.legal()["raise_min"] == 2
    reverse = Hand.new(dealer=1)
    reverse.act(1, "call")
    reverse.act(0, "check")
    assert reverse.state["actor"] == 0


def test_raise_minimum_and_no_mutation_on_invalid_size():
    hand = Hand.new()
    before = deepcopy(hand.state)
    for size in (3, 201, 4.5):
        with pytest.raises(ValueError):
            hand.act(0, "raise", size)
        assert hand.state == before
    hand.act(0, "raise", 6)
    assert hand.legal()["raise_min"] == 10
    hand.act(1, "raise", 10)
    assert hand.legal()["raise_min"] == 14


def test_fold_returns_uncalled_chips_and_keeps_hidden_cards():
    hand = Hand.new()
    hand.act(0, "raise", 100)
    hand.act(1, "fold")
    assert hand.state["result"]["pot"] == 4
    assert hand.state["result"]["deltas"] == [2, -2]
    assert [p["stack"] for p in hand.state["players"]] == [202, 198]
    assert hand.view()["players"][1]["cards"] == [None, None]
    assert hand.legal() == {}
    with pytest.raises(ValueError):
        hand.act(0, "check")


def test_short_all_in_and_unmatched_refund():
    hand = Hand.new(stacks=(200, 7))
    hand.act(0, "raise", 6)
    assert hand.legal()["raise_min"] == hand.legal()["raise_max"] == 7
    assert hand.legal()["short_all_in"]
    hand.act(1, "raise", 7)
    assert hand.legal()["raise_min"] is None
    hand.act(0, "call")
    assert hand.state["result"]["pot"] == 14
    assert len(hand.state["board"]) == 5
    assert sum(p["stack"] for p in hand.state["players"]) == 207
    hand = Hand.new(stacks=(200, 10))
    hand.act(0, "raise", 200)
    assert hand.legal()["call"] == 8
    hand.act(1, "call")
    assert hand.state["result"]["pot"] == 20
    assert any(e["action"] == "refund" and e["amount"] == 190 for e in hand.state["history"])
    assert sum(p["stack"] for p in hand.state["players"]) == 210


def test_big_blind_all_in_at_posting():
    hand = Hand.new(stacks=(20, 2))
    assert hand.legal()["raise_max"] is None
    hand.act(0, "call")
    assert hand.state["result"]["reason"] == "showdown"
    assert hand.state["result"]["pot"] == 4


def test_board_plays_split_pot():
    hand = Hand.new()
    hand.state["players"][0]["cards"] = ["2c", "3d"]
    hand.state["players"][1]["cards"] = ["4c", "5d"]
    hand.state["board"] = ["As", "Ks", "Qs", "Js", "Ts"]
    hand.state["street"] = "river"
    hand.act(0, "call")
    hand.act(1, "check")
    assert hand.state["result"]["winners"] == [0, 1]
    assert hand.state["result"]["deltas"] == [0, 0]


def test_chip_and_card_invariants_across_legal_hands():
    rng = random.Random(42)
    for _ in range(100):
        deck = [r + s for r in RANKS for s in SUITS]
        rng.shuffle(deck)
        initial = (rng.randint(2, 200), rng.randint(2, 200))
        hand = Hand.new(dealer=rng.randrange(2), deck=deck, stacks=initial)
        for _ in range(200):
            s = hand.state
            cards = s["deck"] + s["board"] + s["burned"] + sum((p["cards"] for p in s["players"]), [])
            assert len(cards) == len(set(cards)) == 52
            assert all(p["stack"] >= 0 for p in s["players"])
            if s["result"]:
                assert sum(p["stack"] for p in s["players"]) == sum(initial)
                assert sum(s["result"]["deltas"]) == 0
                break
            assert sum(p["stack"] + p["committed"] for p in s["players"]) == sum(initial)
            legal = hand.legal()
            choices = ["check"] if legal["check"] else ["call", "fold"]
            if legal["raise_min"] is not None:
                choices.append("raise")
            action = rng.choice(choices)
            total = rng.randint(legal["raise_min"], legal["raise_max"]) if action == "raise" else None
            hand.act(s["actor"], action, total)
        else:
            pytest.fail("Una mano non termina entro 200 azioni")
