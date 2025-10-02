from __future__ import annotations


class ContentRegistry:
    def __init__(self) -> None:
        # Simple in-code catalog; can be overridden by JSON files in package data
        self._class_health = {
            "Warrior": 120,
            "Cleric": 100,
            "Ranger": 90,
            "Mage": 70,
            "Rogue": 80,
        }
        self._class_mana = {
            "Mage": 80,
            "Cleric": 60,
            "Ranger": 40,
            "Warrior": 30,
            "Rogue": 35,
        }

    def class_health(self, role: str) -> int:
        return self._class_health.get(role, 100)

    def class_mana(self, role: str) -> int:
        return self._class_mana.get(role, 50)

    def load_from_files(self) -> None:
        import json
        import os
        base_dir = os.path.join(os.path.dirname(__file__), "content")
        try:
            with open(os.path.join(base_dir, "classes.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                self._class_health.update(data.get("class_health", {}))
                self._class_mana.update(data.get("class_mana", {}))
        except Exception:
            pass
