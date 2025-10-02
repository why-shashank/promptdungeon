from __future__ import annotations

from typing import Any

from .core import (
    EventBus,
    GameState,
    LayoutChangedEvent,
    MessageEvent,
    NewRoomEvent,
    PlayerUpdatedEvent,
    SpawnEnemyEvent,
    SpawnItemEvent,
    TurnAdvancedEvent,
    TurnDebugEvent,
)
from .engine import GameConfig, GameEngine


class StorySystem:
    def __init__(self, provider, player_name: str, role: str, log_ai: bool = False) -> None:
        self.engine = GameEngine(provider, GameConfig(player_name=player_name, role=role))
        import os
        self.log_ai = log_ai or (os.getenv("PD_LOG_AI") == "1")
    def start(self, state: GameState, bus: EventBus) -> None:
        turn = self.engine.start_new_story()
        self._turn_to_events(turn, state, bus)

    def step(self, action: str, state: GameState, bus: EventBus) -> None:
        turn = self.engine.step(action)
        self._turn_to_events(turn, state, bus)

    def _turn_to_events(self, turn: Any, state: GameState, bus: EventBus) -> None:
        # Debug snapshot for overlay
        dbg = {
            "narration": getattr(turn, "narration", None),
            "actions": getattr(turn, "actions", None),
            "player_updates": getattr(turn, "player_updates", None),
            "room_updates": getattr(turn, "room_updates", None),
            "done": getattr(turn, "done", False),
        }
        bus.publish(TurnDebugEvent(dbg))

        # Optional logging of raw AI turn
        if self.log_ai:
            try:
                import json
                import os
                os.makedirs("logs", exist_ok=True)
                with open("logs/ai_turns.log", "a", encoding="utf-8") as f:
                    json.dump(getattr(turn, "debug_raw", {}), f, ensure_ascii=False)
                    f.write("\n")
            except Exception:
                pass

        # Narration and suggested actions
        if getattr(turn, "narration", None):
            bus.publish(MessageEvent(turn.narration, "white"))
        if getattr(turn, "actions", None):
            bus.publish(
                MessageEvent(
                    "Actions: " + ", ".join(list(turn.actions)[:5]), "cyan"
                )
            )

        # Player updates
        pu = getattr(turn, "player_updates", None)
        if isinstance(pu, dict):
            bus.publish(
                PlayerUpdatedEvent(
                    health=pu.get("health"),
                    mana=pu.get("mana"),
                    experience=pu.get("experience"),
                    gold=pu.get("gold"),
                    inventory=pu.get("inventory"),
                )
            )

        # Room updates
        ru = getattr(turn, "room_updates", None)
        if isinstance(ru, dict):
            items = ru.get("items") or []
            for it in items[:10]:
                if isinstance(it, str):
                    bus.publish(SpawnItemEvent(it))
            enemies = ru.get("enemies") or []
            for en in enemies[:8]:
                if isinstance(en, str):
                    bus.publish(SpawnEnemyEvent(en))
            layout = ru.get("layout")
            if isinstance(layout, list) and all(isinstance(r, str) for r in layout):
                bus.publish(LayoutChangedEvent(layout))
            if bool(ru.get("new_room", False)):
                bus.publish(NewRoomEvent())

        if getattr(turn, "done", False):
            bus.publish(MessageEvent("The story concludes.", "yellow"))

        # Advance time
        bus.publish(TurnAdvancedEvent(1))
