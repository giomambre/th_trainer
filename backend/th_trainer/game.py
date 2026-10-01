"""Regole heads-up NLHE. Nessuna strategia o valutazione GTO in questo modulo.

Importi interi in fiches (1 BB = 2 fiches); raise_to indica il totale sulla
street, non l'incremento. Lo stato privato è serializzabile solo sul server.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import combinations
import secrets
from uuid import uuid4


RANKS = "23456789TJQKA"
SUITS = "cdhs"
STREETS = ["preflop", "flop", "turn", "river"]
CATEGORIES = ["High card", "One pair", "Two pair", "Three of a kind", "Straight",
              "Flush", "Full house", "Four of a kind", "Straight flush"]
RANK_NAMES = {2: "due", 3: "tre", 4: "quattro", 5: "cinque", 6: "sei",
              7: "sette", 8: "otto", 9: "nove", 10: "dieci", 11: "jack",
              12: "donne", 13: "re", 14: "assi"}


def describe_hand(hole_cards: list[str], board: list[str]) -> dict:
    """Descrive soltanto la combinazione già presente nelle carte visibili."""
    if not board:
        values = sorted((RANKS.index(card[0]) + 2 for card in hole_cards), reverse=True)
        if values[0] == values[1]:
            return {"name": "Pocket pair", "detail": f"Coppia di {RANK_NAMES[values[0]]} nelle tue carte.",
                    "cards": hole_cards, "board_plays": False}
        suited = hole_cards[0][1] == hole_cards[1][1]
        ranks = " / ".join("10" if RANKS[v - 2] == "T" else RANKS[v - 2] for v in values)
        return {"name": f"{ranks} {'suited' if suited else 'offsuit'}",
                "detail": "Carte dello stesso seme." if suited else "Carte di semi diversi.",
                "cards": hole_cards, "board_plays": False}
    best = max(combinations(hole_cards + board, 5), key=rank_five)
    rank = rank_five(best)
    symbol = lambda value: "10" if RANKS[value - 2] == "T" else RANKS[value - 2]
    category, high = rank[:2]
    descriptions = {
        0: lambda: f"Carta alta {symbol(high)}.",
        1: lambda: f"Coppia di {RANK_NAMES[high]}.",
        2: lambda: f"Doppia coppia: {RANK_NAMES[high]} e {RANK_NAMES[rank[2]]}.",
        3: lambda: f"Tris di {RANK_NAMES[high]}.",
        4: lambda: f"Scala fino a {symbol(high)}.",
        5: lambda: f"Colore con carta alta {symbol(high)}.",
        6: lambda: f"Tris di {RANK_NAMES[high]} e coppia di {RANK_NAMES[rank[2]]}.",
        7: lambda: f"Poker di {RANK_NAMES[high]}.",
        8: lambda: f"Scala colore fino a {symbol(high)}.",
    }
    board_plays = len(board) == 5 and evaluate(board) == rank
    if board_plays:
        best = tuple(board)
    return {"name": CATEGORIES[category], "detail": descriptions[category](),
            "cards": sorted(best, key=lambda c: RANKS.index(c[0]), reverse=True),
            "board_plays": board_plays}


def rank_five(cards: tuple[str, ...]) -> tuple[int, ...]:
    values = sorted((RANKS.index(c[0]) + 2 for c in cards), reverse=True)
    groups = sorted(((count, value) for value, count in Counter(values).items()), reverse=True)
    unique = sorted(set(values), reverse=True)
    straight = 5 if unique == [14, 5, 4, 3, 2] else (
        unique[0] if len(unique) == 5 and unique[0] - unique[-1] == 4 else 0
    )
    flush = len({c[1] for c in cards}) == 1
    if straight and flush:
        return (8, straight)
    if groups[0][0] == 4:
        return (7, groups[0][1], groups[1][1])
    if [g[0] for g in groups] == [3, 2]:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *values)
    if straight:
        return (4, straight)
    if groups[0][0] == 3:
        return (3, groups[0][1], *sorted((v for n, v in groups if n == 1), reverse=True))
    if [g[0] for g in groups[:2]] == [2, 2]:
        return (2, *sorted((v for n, v in groups if n == 2), reverse=True), groups[-1][1])
    if groups[0][0] == 2:
        return (1, groups[0][1], *sorted((v for n, v in groups if n == 1), reverse=True))
    return (0, *values)


def evaluate(cards: list[str]) -> tuple[int, ...]:
    if not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards):
        raise ValueError("Servono da 5 a 7 carte distinte")
    return max(rank_five(combo) for combo in combinations(cards, 5))


class Hand:
    def __init__(self, state: dict):
        self.state = state
        self.playback: list[dict] = []

    def response(self) -> dict:
        return self.view() | {"playback": self.playback}

    @classmethod
    def new(cls, dealer: int = 0, *, deck: list[str] | None = None,
            stacks: tuple[int, int] = (200, 200)) -> Hand:
        if dealer not in (0, 1) or min(stacks) < 2:
            raise ValueError("Dealer o stack non valido")
        cards = [r + s for r in RANKS for s in SUITS]
        if deck is None:
            secrets.SystemRandom().shuffle(cards)
        else:
            if len(deck) != 52 or set(deck) != set(cards):
                raise ValueError("Mazzo non valido")
            cards = list(deck)
        state = {
            "id": str(uuid4()), "revision": 0, "dealer": dealer,
            "street": "preflop", "deck": cards, "board": [], "burned": [],
            "players": [{"stack": stack, "initial_stack": stack, "bet": 0,
                         "committed": 0, "cards": []} for stack in stacks],
            "actor": dealer, "pending": [0, 1], "current_bet": 2,
            "last_raise": 2, "history": [], "result": None,
        }
        hand = cls(state)
        # Heads-up: button is SB; BB receives the first card.
        for _ in range(2):
            for player in (1 - dealer, dealer):
                state["players"][player]["cards"].append(cards.pop())
        for player, amount, blind in ((dealer, 1, "SB"), (1 - dealer, 2, "BB")):
            hand._pay(player, amount)
            hand._event(player, blind, amount)
        state["pending"] = [i for i in state["pending"] if state["players"][i]["stack"] > 0]
        return hand

    def _event(self, player: int | None, action: str, amount: int = 0) -> None:
        self.state["history"].append({"sequence": len(self.state["history"]) + 1,
                                      "street": self.state["street"], "player": player,
                                      "action": action, "amount": amount})
        if action not in ("SB", "BB"):
            # Freeze the permitted view before the next action/street changes it.
            # This is presentation data, never an alternate authoritative state.
            self.playback.append({"kind": action, "hand": deepcopy(self.view())})

    def _pay(self, player: int, amount: int) -> None:
        p = self.state["players"][player]
        p["stack"] -= amount
        p["bet"] += amount
        p["committed"] += amount

    def legal(self) -> dict:
        s = self.state
        if s["result"] is not None:
            return {}
        p, other = s["players"][s["actor"]], s["players"][1 - s["actor"]]
        owed = s["current_bet"] - p["bet"]
        maximum = p["bet"] + p["stack"]
        minimum = s["current_bet"] + s["last_raise"]
        can_raise = maximum > s["current_bet"] and other["stack"] > 0
        return {"fold": owed > 0, "check": owed == 0,
                "betting_action": "raise" if s["current_bet"] else "bet",
                "call": min(owed, p["stack"]) if owed else 0,
                "raise_min": min(minimum, maximum) if can_raise else None,
                "raise_max": maximum if can_raise else None,
                "short_all_in": can_raise and maximum < minimum,
                "to_call": owed}

    def act(self, player: int, action: str, raise_to: int | None = None) -> None:
        s = self.state
        if s["result"] is not None or player != s["actor"]:
            raise ValueError("Azione fuori turno o mano conclusa")
        legal = self.legal()
        p = s["players"][player]
        if action == "fold" and legal["fold"]:
            self._event(player, action)
            self._finish([1 - player], "fold")
            return
        if action == "check" and legal["check"]:
            self._event(player, action)
        elif action == "call" and legal["call"]:
            amount = legal["call"]
            self._pay(player, amount)
            self._event(player, action, amount)
        elif action == "raise" and legal["raise_min"] is not None:
            if type(raise_to) is not int or not legal["raise_min"] <= raise_to <= legal["raise_max"]:
                raise ValueError("Importo fuori dall'intervallo consentito")
            increment = raise_to - s["current_bet"]
            previous_bet = s["current_bet"]
            self._pay(player, raise_to - p["bet"])
            if increment >= s["last_raise"]:
                s["last_raise"] = increment
            s["current_bet"] = raise_to
            s["pending"] = [1 - player]
            self._event(player, "bet" if previous_bet == 0 else "raise", raise_to)
            s["actor"] = 1 - player
            return
        else:
            raise ValueError("Azione non consentita")
        s["pending"] = [i for i in s["pending"] if i != player]
        if not s["pending"]:
            self._advance()
        else:
            s["actor"] = 1 - player

    def _deal_street(self) -> None:
        s = self.state
        s["street"] = STREETS[STREETS.index(s["street"]) + 1]
        s["burned"].append(s["deck"].pop())
        s["board"].extend(s["deck"].pop() for _ in range(3 if s["street"] == "flop" else 1))
        for p in s["players"]:
            p["bet"] = 0
        s["current_bet"], s["last_raise"] = 0, 2
        self._event(None, "deal")

    def _advance(self) -> None:
        s = self.state
        if any(p["stack"] == 0 for p in s["players"]):
            while s["street"] != "river":
                self._deal_street()
            self._showdown()
        elif s["street"] == "river":
            self._showdown()
        else:
            self._deal_street()
            s["pending"] = [0, 1]
            s["actor"] = 1 - s["dealer"]

    def _showdown(self) -> None:
        s = self.state
        ranks = [evaluate(p["cards"] + s["board"]) for p in s["players"]]
        self._finish([i for i, rank in enumerate(ranks) if rank == max(ranks)], "showdown",
                     [CATEGORIES[rank[0]] for rank in ranks])

    def _finish(self, winners: list[int], reason: str, categories: list[str] | None = None) -> None:
        s = self.state
        # A heads-up pot has no side pots: return every unmatched chip first.
        matched = min(p["committed"] for p in s["players"])
        for i, p in enumerate(s["players"]):
            refund = p["committed"] - matched
            if refund:
                p["stack"] += refund
                p["committed"] -= refund
                self._event(i, "refund", refund)
        pot = matched * 2
        for i in winners:
            s["players"][i]["stack"] += pot // len(winners)
        s["result"] = {"winners": winners, "reason": reason, "pot": pot,
                       "categories": categories,
                       "deltas": [p["stack"] - p["initial_stack"] for p in s["players"]]}
        s["actor"], s["pending"] = None, []
        self._event(None, "award", pot)

    def view(self) -> dict:
        s = self.state
        reveal = s["result"] is not None and s["result"]["reason"] == "showdown"
        return {key: s[key] for key in ("id", "revision", "dealer", "street", "board", "actor", "history", "result")} | {
            "pot": sum(p["committed"] for p in s["players"]),
            "hero_hand": describe_hand(s["players"][0]["cards"], s["board"]),
            "players": [{"name": "Tu" if i == 0 else "Bot test",
                         "stack": p["stack"], "bet": p["bet"],
                         "cards": p["cards"] if i == 0 or reveal else [None, None]}
                        for i, p in enumerate(s["players"])],
            "legal": self.legal() if s["actor"] == 0 else {},
        }
