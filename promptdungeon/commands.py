from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import Command, EventBus, GameState, MessageEvent, TurnAdvancedEvent
from .visual_game_engine import Direction


@dataclass
class MoveCommand(Command):
    direction: Direction

    def execute(self, state: GameState, bus: EventBus) -> None:
        player_ent = state.dungeon.player
        if state.dungeon.move_entity(player_ent, self.direction):
            state.advance_turn(1)
            bus.publish(TurnAdvancedEvent(1))
        else:
            bus.publish(MessageEvent("Your way is blocked!", "yellow"))


class InspectCommand(Command):
    def execute(self, state: GameState, bus: EventBus) -> None:
        bus.publish(MessageEvent("You carefully examine your surroundings...", "cyan"))
        state.advance_turn(1)
        bus.publish(TurnAdvancedEvent(1))


class WaitCommand(Command):
    def execute(self, state: GameState, bus: EventBus) -> None:
        bus.publish(MessageEvent("You wait and catch your breath.", "gray"))
        state.advance_turn(1)
        bus.publish(TurnAdvancedEvent(1))


@dataclass
class AIActionCommand(Command):
    action: str
    story_system: Any

    def execute(self, state: GameState, bus: EventBus) -> None:
        bus.publish(MessageEvent(f"> {self.action}", "bright_yellow"))
        self.story_system.step(self.action, state, bus)
