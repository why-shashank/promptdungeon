from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Protocol


# ---------- Events ----------
class Event:
    pass


@dataclass
class MessageEvent(Event):
    text: str
    color: str = "white"
    priority: str = "normal"


@dataclass
class SpawnItemEvent(Event):
    name: str


@dataclass
class SpawnEnemyEvent(Event):
    name: str


@dataclass
class LayoutChangedEvent(Event):
    layout: List[str]


@dataclass
class NewRoomEvent(Event):
    pass


@dataclass
class PlayerUpdatedEvent(Event):
    health: Optional[int] = None
    mana: Optional[int] = None
    experience: Optional[int] = None
    gold: Optional[int] = None
    inventory: Optional[List[str]] = None


@dataclass
class TurnAdvancedEvent(Event):
    delta: int = 1


@dataclass
class TurnDebugEvent(Event):
    payload: dict


class EventBus:
    def __init__(self) -> None:
        self._subs: List[Callable[[Event], None]] = []

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        self._subs.append(handler)

    def publish(self, event: Event) -> None:
        for h in list(self._subs):
            h(event)


class Command(Protocol):
    def execute(self, state: "GameState", bus: EventBus) -> None: ...


@dataclass
class GameState:
    # Pointers to live systems; this is a bridge in the current codebase
    dungeon: Any
    player: Any
    turn_count: int = 0

    def advance_turn(self, n: int = 1) -> None:
        self.turn_count += n
