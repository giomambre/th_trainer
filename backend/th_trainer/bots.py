"""Avversario di collaudo. Non è il modello strategico del trainer."""

from .game import Hand


def advance_test_bot(hand: Hand) -> None:
    # Only legal actions are supplied to the policy: no deck or opponent cards.
    while hand.state["actor"] == 1 and hand.state["result"] is None:
        legal = hand.legal()
        hand.act(1, "check" if legal["check"] else "call")
