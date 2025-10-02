from __future__ import annotations

import json
from typing import Any

from .visual_game_engine import CellType, Item


def _cell_char(cell: Any) -> str:
    if hasattr(cell, "value"):
        return cell.value
    s = str(cell)
    return s if s in ("█", ".", "+", ">", "<", " ") else "."


def save_game(path: str, game) -> None:
    d = game.dungeon
    p = game.player
    data = {
        "turn_count": game.turn_count,
        "player": {
            "name": p.name,
            "role": p.role,
            "x": p.x,
            "y": p.y,
            "health": p.health,
            "max_health": p.max_health,
            "mana": p.mana,
            "max_mana": p.max_mana,
            "experience": p.experience,
            "level": p.level,
            "gold": p.gold,
            "inventory": p.inventory,
        },
        "grid": [[_cell_char(c) for c in row] for row in d.grid],
        "items": [
            {"x": it.x, "y": it.y, "symbol": it.symbol, "name": it.name, "desc": it.description, "value": it.value}
            for it in d.items
        ],
        "enemies": [
            {"x": e.x, "y": e.y, "name": e.name, "health": e.health, "max_health": e.max_health}
            for e in d.entities if e is not d.player
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(path: str, game) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Restore player
    p = game.player
    pd = data["player"]
    p.name = pd["name"]
    p.role = pd["role"]
    p.x = pd["x"]
    p.y = pd["y"]
    p.health = pd["health"]
    p.max_health = pd["max_health"]
    p.mana = pd["mana"]
    p.max_mana = pd["max_mana"]
    p.experience = pd["experience"]
    p.level = pd.get("level", p.level)
    p.gold = pd["gold"]
    p.inventory = list(pd.get("inventory", []))

    # Restore grid
    g = data["grid"]
    height = min(len(g), game.dungeon.height)
    for y in range(height):
        row = g[y]
        for x in range(min(len(row), game.dungeon.width)):
            ch = row[x]
            if ch == "█":
                game.dungeon.grid[y][x] = CellType.WALL
            elif ch == ".":
                game.dungeon.grid[y][x] = CellType.FLOOR
            elif ch == "+":
                game.dungeon.grid[y][x] = CellType.DOOR
            elif ch == ">":
                game.dungeon.grid[y][x] = CellType.STAIRS_DOWN
            elif ch == "<":
                game.dungeon.grid[y][x] = CellType.STAIRS_UP
            else:
                game.dungeon.grid[y][x] = CellType.FLOOR

    # Restore items and enemies
    game.dungeon.items = [
        Item(it["x"], it["y"], it.get("symbol", "?"), it["name"], it.get("desc", ""), it.get("value", 0))
        for it in data.get("items", [])
    ]
    # Keep player entity at index 0
    game.dungeon.entities = [game.dungeon.player]
    for e in data.get("enemies", []):
        from .visual_game_engine import Entity as VEntity
        game.dungeon.entities.append(VEntity(e["x"], e["y"], "E", "red", e["name"], e["health"], e["max_health"]))

    game.turn_count = int(data.get("turn_count", game.turn_count))
    # Sync player entity pos
    game.dungeon.player.x = p.x
    game.dungeon.player.y = p.y
    game.dungeon.needs_redraw = True
