import os
import random
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Fallback non-blocking keyboard handling (Unix)
try:
    import select  # type: ignore
    import termios  # type: ignore
    import tty  # type: ignore

    _UNIX_INPUT_AVAILABLE = True
except Exception:
    _UNIX_INPUT_AVAILABLE = False

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    from pynput import keyboard as pynput_keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class CellType(Enum):
    EMPTY = " "
    WALL = "█"
    FLOOR = "."
    DOOR = "+"
    PLAYER = "@"
    ENEMY = "E"
    ITEM = "?"
    TREASURE = "$"
    STAIRS_DOWN = ">"
    STAIRS_UP = "<"


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)


@dataclass
class Entity:
    x: int
    y: int
    symbol: str
    color: str = "white"
    name: str = ""
    health: int = 100
    max_health: int = 100
    is_alive: bool = True


@dataclass
class Item:
    x: int
    y: int
    symbol: str
    name: str
    description: str
    value: int = 0


class VisualDungeon:
    def __init__(self, width: int = 60, height: int = 20):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        self.entities: List[Entity] = []
        self.items: List[Item] = []
        self.player: Optional[Entity] = None
        self.game_running = True
        self.needs_redraw = True
        self.turn_count = 0

    def generate_dungeon(self):
        """Generate a simple dungeon layout"""
        # Fill with walls
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = CellType.WALL

        # Create rooms
        rooms = [
            (5, 3, 15, 8),  # x, y, width, height
            (25, 2, 12, 6),
            (45, 4, 10, 10),
            (8, 12, 20, 6),
            (35, 14, 18, 5),
        ]

        # Carve out rooms
        for room_x, room_y, room_w, room_h in rooms:
            for y in range(room_y, min(room_y + room_h, self.height)):
                for x in range(room_x, min(room_x + room_w, self.width)):
                    self.grid[y][x] = CellType.FLOOR

        # Create corridors between rooms
        self._create_corridor(12, 6, 25, 5)  # Connect room 1 to 2
        self._create_corridor(37, 5, 45, 8)  # Connect room 2 to 3
        self._create_corridor(15, 11, 18, 12)  # Connect room 1 to 4
        self._create_corridor(28, 12, 35, 16)  # Connect room 4 to 5

        # Add some doors
        self.grid[6][20] = CellType.DOOR
        self.grid[8][40] = CellType.DOOR

        # Place stairs
        self.grid[5][50] = CellType.STAIRS_DOWN

        # Place some items randomly in rooms
        for _ in range(8):
            room_x, room_y, room_w, room_h = random.choice(rooms)
            item_x = random.randint(room_x + 1, room_x + room_w - 2)
            item_y = random.randint(room_y + 1, room_y + room_h - 2)

            if self.grid[item_y][item_x] == CellType.FLOOR:
                items = [
                    ("Sword", "A sharp blade", 100),
                    ("Potion", "Restores health", 50),
                    ("Gold", "Shiny coins", 25),
                    ("Shield", "Protective gear", 75),
                    ("Scroll", "Ancient magic", 150),
                ]
                item_name, desc, value = random.choice(items)
                self.items.append(Item(item_x, item_y, "?", item_name, desc, value))

        # Place some enemies
        for _ in range(5):
            room_x, room_y, room_w, room_h = random.choice(rooms)
            enemy_x = random.randint(room_x + 1, room_x + room_w - 2)
            enemy_y = random.randint(room_y + 1, room_y + room_h - 2)

            if self.grid[enemy_y][enemy_x] == CellType.FLOOR:
                enemies = ["Goblin", "Orc", "Skeleton", "Rat", "Spider"]
                enemy_name = random.choice(enemies)
                enemy = Entity(
                    enemy_x,
                    enemy_y,
                    "E",
                    "red",
                    enemy_name,
                    random.randint(30, 80),
                    random.randint(30, 80),
                )
                self.entities.append(enemy)

    def _create_corridor(self, x1: int, y1: int, x2: int, y2: int):
        """Create a simple L-shaped corridor"""
        # Horizontal first
        start_x, end_x = (x1, x2) if x1 < x2 else (x2, x1)
        for x in range(start_x, end_x + 1):
            if 0 <= y1 < self.height and 0 <= x < self.width:
                self.grid[y1][x] = CellType.FLOOR

        # Then vertical
        start_y, end_y = (y1, y2) if y1 < y2 else (y2, y1)
        for y in range(start_y, end_y + 1):
            if 0 <= y < self.height and 0 <= x2 < self.width:
                self.grid[y][x2] = CellType.FLOOR

    def place_player(self, x: int = 10, y: int = 5):
        """Place the player in the dungeon"""
        if self.player:
            self.entities.remove(self.player)

        self.player = Entity(x, y, "@", "yellow", "Player", 100, 100)
        self.entities.append(self.player)
        self.needs_redraw = True

    def move_entity(self, entity: Entity, direction: Direction) -> bool:
        """Move an entity in the given direction"""
        dy, dx = direction.value
        new_x = entity.x + dx
        new_y = entity.y + dy

        # Check bounds
        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return False

        # Check for walls
        cell = self.grid[new_y][new_x]
        if cell == CellType.WALL:
            return False

        # Check for other entities (except self)
        for other in self.entities:
            if other != entity and other.x == new_x and other.y == new_y:
                if entity == self.player and other != self.player:
                    # Player attacking an enemy
                    self._combat(entity, other)
                return False

        # Move is valid
        entity.x = new_x
        entity.y = new_y
        self.needs_redraw = True

        # Check for items at new position
        if entity == self.player:
            self._check_item_pickup(new_x, new_y)

        return True

    def _combat(self, attacker: Entity, defender: Entity):
        """Simple combat system"""
        damage = random.randint(10, 25)
        defender.health -= damage

        # Add combat message (we'll implement message system later)
        if defender.health <= 0:
            defender.is_alive = False
            if defender in self.entities:
                self.entities.remove(defender)

        self.needs_redraw = True

    def _check_item_pickup(self, x: int, y: int):
        """Check if player picked up an item"""
        for item in self.items[:]:  # Copy list to avoid modification during iteration
            if item.x == x and item.y == y:
                self.items.remove(item)
                # Add to player inventory (implement later)
                self.needs_redraw = True
                break

    def update_enemies(self):
        """Simple AI for enemy movement"""
        if not self.player:
            return

        for enemy in self.entities[:]:
            if enemy == self.player or not enemy.is_alive:
                continue

            # Simple AI: move towards player sometimes
            if random.random() < 0.3:  # 30% chance to move each turn
                # Calculate direction to player
                dx = self.player.x - enemy.x
                dy = self.player.y - enemy.y

                # Choose direction (simple pathfinding)
                if abs(dx) > abs(dy):
                    direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    direction = Direction.DOWN if dy > 0 else Direction.UP

                self.move_entity(enemy, direction)


class TerminalRenderer:
    def __init__(self):
        self.colors = {
            "black": "\033[30m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "reset": "\033[0m",
            "bold": "\033[1m",
        }

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def hide_cursor(self):
        print("\033[?25l", end="")

    def show_cursor(self):
        print("\033[?25h", end="")

    def move_cursor(self, x: int, y: int):
        print(f"\033[{y + 1};{x + 1}H", end="")

    def color_text(self, text: str, color: str) -> str:
        if color in self.colors:
            return f"{self.colors[color]}{text}{self.colors['reset']}"
        return text

    def render_dungeon(self, dungeon: VisualDungeon):
        """Render the entire dungeon"""
        self.clear_screen()
        self.hide_cursor()

        # Create display grid
        display = [[" " for _ in range(dungeon.width)] for _ in range(dungeon.height)]

        # Fill with dungeon cells
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                cell = dungeon.grid[y][x]
                if cell == CellType.WALL:
                    display[y][x] = self.color_text("█", "white")
                elif cell == CellType.FLOOR:
                    display[y][x] = self.color_text(".", "gray")
                elif cell == CellType.DOOR:
                    display[y][x] = self.color_text("+", "yellow")
                elif cell == CellType.STAIRS_DOWN:
                    display[y][x] = self.color_text(">", "cyan")
                elif cell == CellType.STAIRS_UP:
                    display[y][x] = self.color_text("<", "cyan")

        # Add items
        for item in dungeon.items:
            if 0 <= item.y < dungeon.height and 0 <= item.x < dungeon.width:
                display[item.y][item.x] = self.color_text(item.symbol, "green")

        # Add entities
        for entity in dungeon.entities:
            if 0 <= entity.y < dungeon.height and 0 <= entity.x < dungeon.width:
                display[entity.y][entity.x] = self.color_text(
                    entity.symbol, entity.color
                )

        # Render to screen
        for y, row in enumerate(display):
            self.move_cursor(0, y)
            print("".join(row))

        # Add UI
        self._render_ui(dungeon)

        sys.stdout.flush()

    def _render_ui(self, dungeon: VisualDungeon):
        """Render game UI below the dungeon"""
        ui_y = dungeon.height + 1

        self.move_cursor(0, ui_y)
        print("─" * dungeon.width)

        if dungeon.player:
            player = dungeon.player
            health_bar = "█" * (player.health // 10) + "░" * (10 - player.health // 10)

            self.move_cursor(0, ui_y + 1)
            print(f"Health: {self.color_text(health_bar, 'red')} {player.health}/100")

            self.move_cursor(0, ui_y + 2)
            print(
                f"Turn: {dungeon.turn_count} | Enemies: {len([e for e in dungeon.entities if e != dungeon.player])}"
            )

        self.move_cursor(0, ui_y + 4)
        print("Controls: WASD/Arrow Keys to move, Q to quit")

        self.move_cursor(0, ui_y + 6)  # Position for any messages


class GameEngine:
    def __init__(self, width: int = 60, height: int = 20):
        self.dungeon = VisualDungeon(width, height)
        self.renderer = TerminalRenderer()
        self.running = True
        self.key_handler = None
        # Raw input state
        self._raw_mode_enabled = False
        self._stdin_fd = None
        self._orig_termios = None
        self._last_key = None
        self._last_key_ts = 0.0

    def initialize_game(self):
        """Set up the game"""
        self.dungeon.generate_dungeon()
        self.dungeon.place_player(10, 5)

        # Set up input handling
        if KEYBOARD_AVAILABLE:
            self._setup_keyboard_handler()
        elif PYNPUT_AVAILABLE:
            self._setup_pynput_handler()
        else:
            print(
                "Warning: No keyboard library available. Install 'keyboard' or 'pynput' for better controls."
            )

    def _setup_keyboard_handler(self):
        """Set up keyboard input using keyboard library"""
        try:
            keyboard.on_press_key("w", lambda _: self._handle_input("w"))
            keyboard.on_press_key("a", lambda _: self._handle_input("a"))
            keyboard.on_press_key("s", lambda _: self._handle_input("s"))
            keyboard.on_press_key("d", lambda _: self._handle_input("d"))
            keyboard.on_press_key("up", lambda _: self._handle_input("w"))
            keyboard.on_press_key("left", lambda _: self._handle_input("a"))
            keyboard.on_press_key("down", lambda _: self._handle_input("s"))
            keyboard.on_press_key("right", lambda _: self._handle_input("d"))
            keyboard.on_press_key("q", lambda _: self._handle_input("q"))
        except:
            pass

    def _setup_pynput_handler(self):
        """Set up keyboard input using pynput library"""

        def on_press(key):
            try:
                if hasattr(key, "char") and key.char:
                    self._handle_input(key.char.lower())
            except AttributeError:
                # Special keys
                if key == pynput_keyboard.Key.up:
                    self._handle_input("w")
                elif key == pynput_keyboard.Key.down:
                    self._handle_input("s")
                elif key == pynput_keyboard.Key.left:
                    self._handle_input("a")
                elif key == pynput_keyboard.Key.right:
                    self._handle_input("d")

        self.key_handler = pynput_keyboard.Listener(on_press=on_press)
        self.key_handler.start()

    def _handle_input(self, key: str):
        """Handle keyboard input"""
        if not self.dungeon.player or not self.running:
            return

        direction_map = {
            "w": Direction.UP,
            "s": Direction.DOWN,
            "a": Direction.LEFT,
            "d": Direction.RIGHT,
        }

        if key in direction_map:
            if self.dungeon.move_entity(self.dungeon.player, direction_map[key]):
                self.dungeon.turn_count += 1
                self.dungeon.update_enemies()
        elif key == "q":
            self.running = False

    def run(self):
        """Main game loop"""
        try:
            self.initialize_game()
            last_render_time = 0

            print("Starting LLM Dungeon Crawler...")
            print("Use WASD or arrow keys to move, Q to quit")
            time.sleep(2)

            while self.running and self.dungeon.player and self.dungeon.player.is_alive:
                current_time = time.time()

                # Render at ~30 FPS or when needed
                if (
                    current_time - last_render_time > 1 / 30
                    or self.dungeon.needs_redraw
                ):
                    self.renderer.render_dungeon(self.dungeon)
                    self.dungeon.needs_redraw = False
                    last_render_time = current_time

                # Always poll stdin fallback to support environments where
                # keyboard/pynput import but do not deliver events
                self._manual_input_handler()

                time.sleep(1 / 60)  # 60 FPS game loop

            # Game over
            self.renderer.move_cursor(0, self.dungeon.height + 8)
            if not self.dungeon.player.is_alive:
                print(self.renderer.color_text("GAME OVER! You died!", "red"))
            else:
                print(self.renderer.color_text("Thanks for playing!", "green"))

        finally:
            self.cleanup()

    def _enter_raw_mode(self):
        if self._raw_mode_enabled or not _UNIX_INPUT_AVAILABLE:
            return
        try:
            self._stdin_fd = sys.stdin.fileno()
            self._orig_termios = termios.tcgetattr(self._stdin_fd)
            tty.setcbreak(self._stdin_fd)
            self._raw_mode_enabled = True
        except Exception:
            self._raw_mode_enabled = False

    def _exit_raw_mode(self):
        if not self._raw_mode_enabled or self._stdin_fd is None or self._orig_termios is None:
            return
        try:
            termios.tcsetattr(self._stdin_fd, termios.TCSADRAIN, self._orig_termios)
        finally:
            self._raw_mode_enabled = False
            self._stdin_fd = None
            self._orig_termios = None

    def _read_key_nonblocking(self) -> Optional[str]:
        if not _UNIX_INPUT_AVAILABLE:
            return None
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == "\x1b":  # Potential escape sequence
                    if select.select([sys.stdin], [], [], 0.001)[0]:
                        next1 = sys.stdin.read(1)
                        if next1 == "[" and select.select([sys.stdin], [], [], 0.001)[0]:
                            next2 = sys.stdin.read(1)
                            # Arrow keys
                            if next2 == "A":
                                return "w"
                            if next2 == "B":
                                return "s"
                            if next2 == "D":
                                return "a"
                            if next2 == "C":
                                return "d"
                # Regular keys
                if ch in ("\n", "\r"):
                    return None
                return ch
        except Exception:
            return None
        return None

    def _manual_input_handler(self):
        """Fallback input handler using non-blocking stdin (Unix)."""
        if not _UNIX_INPUT_AVAILABLE:
            return
        if not self._raw_mode_enabled:
            self._enter_raw_mode()
        key = self._read_key_nonblocking()
        if not key:
            return
        direction_map = {
            "w": Direction.UP,
            "s": Direction.DOWN,
            "a": Direction.LEFT,
            "d": Direction.RIGHT,
        }
        now = time.time()
        if self._last_key == key and (now - self._last_key_ts) < 0.05:
            return
        self._last_key, self._last_key_ts = key, now

        if key in direction_map:
            if self.dungeon.move_entity(self.dungeon.player, direction_map[key]):
                self.dungeon.turn_count += 1
                self.dungeon.update_enemies()
        elif key.lower() == "q":
            self.running = False

    def cleanup(self):
        """Clean up resources"""
        self.renderer.show_cursor()
        if self.key_handler:
            self.key_handler.stop()
        self._exit_raw_mode()


if __name__ == "__main__":
    # Quick test
    game = GameEngine(60, 20)
    game.run()
