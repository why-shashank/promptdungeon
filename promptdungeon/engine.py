from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List

from pydantic import BaseModel, Field

try:
    # pydantic v2
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore

from .json_utils import coerce_json
from .llm import LLMProvider
from .prompts import ACTION_PROCESSING_PROMPT, ROOM_GENERATION_PROMPT


@dataclass
class GameConfig:
    player_name: str
    role: str


class Turn(BaseModel):
    # Accept extra fields so providers can include richer updates we can consume later
    model_config = ConfigDict(extra="allow") if isinstance(ConfigDict, type) else {"extra": "allow"}

    narration: str
    actions: List[str] = Field(default_factory=list)
    memory: str = ""
    done: bool = False

    # Optional richer fields
    items: List[str] = Field(default_factory=list)
    enemies: List[str] = Field(default_factory=list)
    special_features: List[str] = Field(default_factory=list)


class GameEngine:
    def __init__(self, provider: LLMProvider, config: GameConfig):
        self.provider = provider
        self.config = config
        self.memory: str = ""  # compact running summary
        self.history: List[Dict[str, str]] = []  # short conversational history

    def _build_user_payload(self, action: str | None) -> str:
        payload = {
            "player": {
                "name": self.config.player_name,
                "role": self.config.role,
            },
            "memory": self.memory,
            "action": action,
        }
        return json.dumps(payload, ensure_ascii=False)

    def _call(self, action: str | None, system_prompt: str) -> Turn:
        user_payload = self._build_user_payload(action)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ]

        raw = self.provider.complete(messages=messages, json_object=True)
        data = coerce_json(raw)
        try:
            turn = Turn.model_validate(data)
        except Exception:
            # Try to map common variations
            actions = list(data.get("actions") or data.get("available_actions") or [])
            turn = Turn(
                narration=str(data.get("narration", raw)),
                actions=actions,
                memory=str(data.get("memory", self.memory)),
                done=bool(data.get("done", data.get("game_over", False))),
                items=list(data.get("items", [])),
                enemies=list(data.get("enemies", [])),
                special_features=list(data.get("special_features", [])),
            )
        # Attach raw/coerced data for debug/logging
        try:
            turn.debug_raw = data
        except Exception:
            pass
        self.memory = turn.memory
        return turn

    def start_new_story(self) -> Turn:
        return self._call(action=None, system_prompt=ROOM_GENERATION_PROMPT)

    def step(self, action: str) -> Turn:
        # Keep a tiny rolling history for subtle continuity (provider may use it internally)
        self.history.append({"role": "user", "content": action})
        if len(self.history) > 6:
            self.history = self.history[-6:]
        return self._call(action=action, system_prompt=ACTION_PROCESSING_PROMPT)
