from dataclasses import dataclass, field


@dataclass(frozen=True)
class Player:
    id: str
    hp: int
    mana: int
    mana_slots: int
    hand: list[int] = field(default_factory=list)
    deck: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class GameState:
    players: list[Player]
    active_player_index: int
