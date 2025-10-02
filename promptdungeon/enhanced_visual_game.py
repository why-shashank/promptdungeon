import random
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

# Fallback non-blocking keyboard handling (Unix)
try:
    import select  # type: ignore
    import termios  # type: ignore
    import tty  # type: ignore

    _UNIX_INPUT_AVAILABLE = True
except Exception:
    _UNIX_INPUT_AVAILABLE = False

# Import our beautiful UI components
from .ui_engine import BeautifulRenderer
from .commands import AIActionCommand, InspectCommand, MoveCommand, WaitCommand
from .content import ContentRegistry

# New core systems
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
)
from .story import StorySystem
from .game_engine import CellType, Direction, Entity, Item, VisualDungeon

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


@dataclass
class EnhancedPlayer:
    """Enhanced player with more stats and abilities"""

    name: str
    role: str
    x: int = 10
    y: int = 10
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    experience: int = 0
    level: int = 1
    gold: int = 50
    inventory: List[str] = None

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = ["Health Potion", "Rusty Sword"]

    @property
    def symbol(self) -> str:
        return "@"

    @property
    def color(self) -> str:
        return "bright_yellow"

    def gain_experience(self, amount: int):
        """Gain experience and level up if needed"""
        self.experience += amount
        exp_needed = self.level * 100
        if self.experience >= exp_needed:
            self.level += 1
            self.max_health += 20
            self.max_mana += 10
            self.health = min(self.health + 50, self.max_health)  # Heal on level up
            return True
        return False

    def take_damage(self, amount: int) -> bool:
        """Take damage and return True if still alive"""
        self.health = max(0, self.health - amount)
        return self.health > 0

    def heal(self, amount: int):
        """Heal the player"""
        self.health = min(self.max_health, self.health + amount)

    def use_mana(self, amount: int) -> bool:
        """Use mana and return True if successful"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False

    def restore_mana(self, amount: int):
        """Restore mana"""
        self.mana = min(self.max_mana, self.mana + amount)


class EnhancedVisualGame:
    def __init__(
        self, width: int = 60, height: int = 20, llm_provider=None, config=None
    ):
        self.dungeon = VisualDungeon(width, height)
        self.renderer = BeautifulRenderer(110, 35)  # Larger terminal for beautiful UI
        self.player = None
        self.running = True
        self.game_messages = []
        self.turn_count = 0
        self.last_action_time = 0
        self.llm_provider = llm_provider
        self.config = config
        self.story_system: Optional[StorySystem] = None
        self.debug_info: Optional[dict] = None

        # Core bus/state
        self.bus = EventBus()
        self.content = ContentRegistry()
        try:
            self.content.load_from_files()
        except Exception:
            pass
        self.state: Optional[GameState] = None

        # Raw input state (fallback mode)
        self._raw_mode_enabled = False
        self._stdin_fd = None
        self._orig_termios = None
        self._last_key = None
        self._last_key_ts = 0.0

        # Game state
        self.inventory_open = False
        self.help_open = False
        self.animation_speed = 0.1

        # Combat state
        self.in_combat = False
        self.combat_target = None

    def initialize_game(self, player_name: str = "Hero", player_class: str = "Warrior", seed: Optional[int] = None):
        """Initialize the enhanced game"""
        # Seed randomness if provided
        if seed is not None:
            try:
                import random
                random.seed(seed)
                self.add_message(f"Seed set to {seed}", "gray")
            except Exception:
                pass
        # Generate dungeon
        self.dungeon.generate_dungeon()

        # Initialize game state and event subscriptions
        self.state = GameState(self.dungeon, None, 0)  # type: ignore
        self.bus.subscribe(self._on_event)

        # Create enhanced player
        self.player = EnhancedPlayer(
            name=player_name,
            role=player_class,
            x=10,
            y=5,
            health=self.content.class_health(player_class),
            max_health=self.content.class_health(player_class),
            mana=self.content.class_mana(player_class),
            max_mana=self.content.class_mana(player_class),
        )

        # Add player to entities
        player_entity = Entity(
            self.player.x,
            self.player.y,
            "@",
            "bright_yellow",
            f"{player_name} the {player_class}",
            self.player.health,
            self.player.max_health,
        )
        self.dungeon.entities = [player_entity] + self.dungeon.entities
        self.dungeon.player = player_entity
        self.state.player = self.player  # type: ignore

        # Welcome message
        self.add_message(
            f"Welcome, {player_name} the {player_class}!", "bright_green", "important"
        )
        self.add_message("Use WASD to move, I to inspect, Tab for inventory", "cyan")

        # Initialize LLM story system if available
        if self.llm_provider is not None:
            try:
                self.story_system = StorySystem(self.llm_provider, player_name, player_class)
                self.story_system.start(self.state, self.bus)
            except Exception as e:
                self.add_message(f"AI init failed: {e}", "yellow")
                self.story_system = None

        # Create enhanced player
        self.player = EnhancedPlayer(
            name=player_name,
            role=player_class,
            x=10,
            y=5,
            health=self._get_class_health(player_class),
            max_health=self._get_class_health(player_class),
            mana=self._get_class_mana(player_class),
            max_mana=self._get_class_mana(player_class),
        )

        # Add player to entities
        player_entity = Entity(
            self.player.x,
            self.player.y,
            "@",
            "bright_yellow",
            f"{player_name} the {player_class}",
            self.player.health,
            self.player.max_health,
        )
        self.dungeon.entities = [player_entity] + self.dungeon.entities
        self.dungeon.player = player_entity

        # Welcome message
        self.add_message(
            f"Welcome, {player_name} the {player_class}!", "bright_green", "important"
        )
        self.add_message("Use WASD to move, I to inspect, Tab for inventory", "cyan")

        # Set up controls
        self._setup_controls()

    def _get_class_health(self, class_name: str) -> int:
        """Get starting health based on class"""
        health_map = {
            "Warrior": 120,
            "Cleric": 100,
            "Ranger": 90,
            "Mage": 70,
            "Rogue": 80,
        }
        return health_map.get(class_name, 100)

    def _get_class_mana(self, class_name: str) -> int:
        """Get starting mana based on class"""
        mana_map = {"Mage": 80, "Cleric": 60, "Ranger": 40, "Warrior": 30, "Rogue": 35}
        return mana_map.get(class_name, 50)

    def _setup_controls(self):
        """Set up enhanced keyboard controls"""
        if KEYBOARD_AVAILABLE:
            try:
                # Movement
                keyboard.on_press_key("w", lambda _: self._handle_input("w"))
                keyboard.on_press_key("a", lambda _: self._handle_input("a"))
                keyboard.on_press_key("s", lambda _: self._handle_input("s"))
                keyboard.on_press_key("d", lambda _: self._handle_input("d"))

                # Actions
                keyboard.on_press_key("i", lambda _: self._handle_input("i"))
                keyboard.on_press_key("space", lambda _: self._handle_input("space"))
                keyboard.on_press_key("tab", lambda _: self._handle_input("tab"))
                keyboard.on_press_key("h", lambda _: self._handle_input("h"))
                keyboard.on_press_key("q", lambda _: self._handle_input("q"))
                keyboard.on_press_key(
                    "e", lambda _: self._handle_input("e")
                )  # Use item
                keyboard.on_press_key("r", lambda _: self._handle_input("r"))  # Rest
                keyboard.on_press_key("enter", lambda _: self._handle_input("enter"))
                keyboard.on_press_key("/", lambda _: self._handle_input("/"))
                keyboard.on_press_key(":", lambda _: self._handle_input(":"))

                # Arrow keys
                keyboard.on_press_key("up", lambda _: self._handle_input("w"))
                keyboard.on_press_key("down", lambda _: self._handle_input("s"))
                keyboard.on_press_key("left", lambda _: self._handle_input("a"))
                keyboard.on_press_key("right", lambda _: self._handle_input("d"))

            except Exception as e:
                self.add_message(f"Keyboard setup warning: {e}", "yellow")

        elif PYNPUT_AVAILABLE:

            def on_press(key):
                try:
                    if hasattr(key, "char") and key.char:
                        self._handle_input(key.char.lower())
                except AttributeError:
                    if key == pynput_keyboard.Key.up:
                        self._handle_input("w")
                    elif key == pynput_keyboard.Key.down:
                        self._handle_input("s")
                    elif key == pynput_keyboard.Key.left:
                        self._handle_input("a")
                    elif key == pynput_keyboard.Key.right:
                        self._handle_input("d")
                    elif key == pynput_keyboard.Key.space:
                        self._handle_input("space")
                    elif key == pynput_keyboard.Key.tab:
                        self._handle_input("tab")
                    elif key == pynput_keyboard.Key.enter:
                        self._handle_input("enter")

            self.key_listener = pynput_keyboard.Listener(on_press=on_press)
            self.key_listener.start()

    def _handle_input(self, key: str):
        """Enhanced input handling with more actions"""
        if not self.player or not self.running:
            return

        # Deduplicate rapid duplicate events (e.g., both keyboard lib and stdin fallback)
        now = time.time()
        key_l = key.lower()
        if self._last_key == key_l and (now - self._last_key_ts) < 0.05:
            return
        self._last_key, self._last_key_ts = key_l, now

        current_time = time.time()

        # Handle movement
        if key in ["w", "s", "a", "d"]:
            self._handle_movement(key)

        # Handle actions
        elif key == "i":
            if self.state:
                InspectCommand().execute(self.state, self.bus)
        elif key == "space":
            if self.state:
                WaitCommand().execute(self.state, self.bus)
        elif key == "tab":
            self._toggle_inventory()
        elif key == "h":
            self._toggle_help()
        elif key == "e":
            self._handle_use_item()
        elif key == "r":
            self._handle_rest()
        elif key == "q":
            self._handle_quit()
        elif key in ("enter", ":", "/"):
            self._open_prompt()
        elif key == "k":
            self._save_game()
        elif key == "l":
            self._load_game()

    def _handle_movement(self, key: str):
        """Handle player movement with enhanced feedback"""
        direction_map = {
            "w": Direction.UP,
            "s": Direction.DOWN,
            "a": Direction.LEFT,
            "d": Direction.RIGHT,
        }

        direction = direction_map[key]
        if not self.state:
            return
        # Execute as command
        MoveCommand(direction).execute(self.state, self.bus)

        # Update local refs from dungeon after movement
        self.player.x = self.dungeon.player.x
        self.player.y = self.dungeon.player.y

        # Enemy updates and regen are still handled here for now
        self._check_movement_events()
        self._update_enemies()
        if self.turn_count % 3 == 0:
            self.player.restore_mana(1)

    def _handle_inspect(self):
        """Inspect surroundings"""
        self.add_message("You carefully examine your surroundings...", "cyan")

        # Look for nearby items and enemies
        nearby_items = []
        nearby_enemies = []

        for item in self.dungeon.items:
            if abs(item.x - self.player.x) <= 2 and abs(item.y - self.player.y) <= 2:
                nearby_items.append(item)

        for entity in self.dungeon.entities:
            if (
                entity != self.dungeon.player
                and abs(entity.x - self.player.x) <= 3
                and abs(entity.y - self.player.y) <= 3
            ):
                nearby_enemies.append(entity)

        if nearby_items:
            item_names = [item.name for item in nearby_items[:3]]
            self.add_message(f"You see: {', '.join(item_names)}", "green")

        if nearby_enemies:
            enemy_names = [entity.name for entity in nearby_enemies[:2]]
            self.add_message(
                f"Enemies nearby: {', '.join(enemy_names)}", "red", "warning"
            )

        if not nearby_items and not nearby_enemies:
            descriptions = [
                "The ancient stones whisper forgotten secrets.",
                "Dust motes dance in shafts of ethereal light.",
                "The air grows thick with magical energy.",
                "Shadows seem to move when you're not looking.",
                "You sense something watching from the darkness.",
            ]
            self.add_message(random.choice(descriptions), "cyan")

    def _handle_wait(self):
        """Wait/rest for a turn"""
        self.turn_count += 1
        self.add_message("You wait and catch your breath.", "gray")

        # Small healing and mana recovery
        self.player.heal(2)
        self.player.restore_mana(3)

        # Update enemies
        self._update_enemies()

    def _handle_rest(self):
        """Rest to recover health and mana"""
        if random.random() < 0.3:  # 30% chance of being interrupted
            self.add_message(
                "You try to rest but hear threatening sounds nearby!", "red", "warning"
            )
            return

        heal_amount = random.randint(15, 25)
        mana_amount = random.randint(10, 20)

        self.player.heal(heal_amount)
        self.player.restore_mana(mana_amount)

        self.add_message(
            f"You rest and recover {heal_amount} health and {mana_amount} mana.",
            "bright_green",
            "success",
        )
        self.turn_count += 2  # Resting takes time

        # Update enemies (they might find you!)
        self._update_enemies()

    def _handle_use_item(self):
        """Use an item from inventory"""
        if not self.player.inventory:
            self.add_message("You have no items to use!", "yellow")
            return

        # For now, use the first consumable item
        for item in self.player.inventory[:]:
            if "potion" in item.lower():
                self.player.inventory.remove(item)
                if "health" in item.lower():
                    heal_amount = random.randint(30, 50)
                    self.player.heal(heal_amount)
                    self.add_message(
                        f"You drink the {item} and recover {heal_amount} health!",
                        "bright_green",
                        "success",
                    )
                elif "mana" in item.lower():
                    mana_amount = random.randint(20, 40)
                    self.player.restore_mana(mana_amount)
                    self.add_message(
                        f"You drink the {item} and recover {mana_amount} mana!",
                        "bright_blue",
                        "success",
                    )
                return

        self.add_message("No usable items in inventory.", "gray")

    def _toggle_inventory(self):
        """Toggle inventory display"""
        self.inventory_open = not self.inventory_open
        if self.inventory_open:
            self.add_message("Inventory opened (Tab to close)", "cyan")
        else:
            self.add_message("Inventory closed", "gray")

    def _toggle_help(self):
        """Toggle help display"""
        self.help_open = not self.help_open
        if self.help_open:
            self.add_message("Help opened (H to close)", "cyan")
        else:
            self.add_message("Help closed", "gray")

    def _handle_quit(self):
        """Handle quit command"""
        self.running = False
        self.add_message("Farewell, brave adventurer!", "bright_yellow")

    def _check_movement_events(self):
        """Check for events when player moves"""
        # Check for items at current position
        for item in self.dungeon.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                self.dungeon.items.remove(item)
                self.player.inventory.append(item.name)
                self.add_message(
                    f"You picked up: {item.name}", "bright_green", "success"
                )

                # Special item effects
                if "gold" in item.name.lower():
                    gold_amount = random.randint(10, 50)
                    self.player.gold += gold_amount
                    self.add_message(f"You gained {gold_amount} gold!", "bright_yellow")

        # Check for special floor tiles
        if hasattr(self.dungeon, "grid"):
            cell = self.dungeon.grid[self.player.y][self.player.x]
            if hasattr(cell, "value"):
                cell_type = cell.value
                if cell_type == ">":
                    self.add_message(
                        "You found stairs leading deeper!", "bright_cyan", "important"
                    )
                elif cell_type == "+":
                    self.add_message("You pass through a door.", "yellow")

    def _update_enemies(self):
        """Update enemy AI with enhanced behavior"""
        for enemy in self.dungeon.entities[:]:
            if enemy == self.dungeon.player or not enemy.is_alive:
                continue

            # Calculate distance to player
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            distance = abs(dx) + abs(dy)

            # Enemy behavior based on distance
            if distance == 1:
                # Adjacent - attack!
                self._combat_encounter(enemy)
            elif distance <= 4 and random.random() < 0.4:
                # Close - move towards player
                if abs(dx) > abs(dy):
                    direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    direction = Direction.DOWN if dy > 0 else Direction.UP

                self.dungeon.move_entity(enemy, direction)
            elif random.random() < 0.2:
                # Far - random movement
                direction = random.choice(
                    [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
                )
                self.dungeon.move_entity(enemy, direction)

    def _combat_encounter(self, enemy):
        """Handle combat encounter"""
        self.add_message(f"💥 {enemy.name} attacks you!", "bright_red", "warning")

        # Simple combat calculation
        enemy_damage = random.randint(8, 20)
        player_damage = random.randint(12, 25)

        # Apply class bonuses
        if self.player.role == "Warrior":
            player_damage += 5
        elif self.player.role == "Mage" and self.player.use_mana(5):
            player_damage += 8
            self.add_message("You cast a spell!", "bright_magenta")
        elif self.player.role == "Rogue" and random.random() < 0.3:
            player_damage *= 2
            self.add_message("Critical hit!", "bright_yellow", "success")

        # Deal damage
        if not self.player.take_damage(enemy_damage):
            self.add_message("💀 You have been defeated!", "bright_red", "important")
            self.running = False
            return

        enemy.health -= player_damage
        self.add_message(
            f"You deal {player_damage} damage to {enemy.name}!", "bright_green"
        )

        if enemy.health <= 0:
            # Enemy defeated
            enemy.is_alive = False
            self.dungeon.entities.remove(enemy)

            exp_gain = random.randint(20, 40)
            gold_gain = random.randint(5, 20)

            if self.player.gain_experience(exp_gain):
                self.add_message(
                    f"⭐ Level up! You are now level {self.player.level}!",
                    "bright_yellow",
                    "important",
                )

            self.player.gold += gold_gain
            self.add_message(
                f"💀 {enemy.name} defeated! Gained {exp_gain} XP and {gold_gain} gold!",
                "bright_green",
                "success",
            )

            # Chance for item drop
            if random.random() < 0.4:
                loot_items = [
                    "Health Potion",
                    "Mana Potion",
                    "Silver Coin",
                    "Magic Scroll",
                    "Iron Dagger",
                ]
                loot = random.choice(loot_items)
                self.player.inventory.append(loot)
                self.add_message(f"You found: {loot}!", "bright_cyan", "success")
        else:
            self.add_message(
                f"{enemy.name} has {enemy.health} health remaining.", "red"
            )

    def add_message(self, text: str, color: str = "white", priority: str = "normal"):
        """Add a message to the game log"""
        self.renderer.message_log.add_message(text, color, priority)

    # ----- AI integration -----
    def _apply_initial_turn(self, turn):
        # Show narration
        # Deprecated: handled by StorySystem events
        pass
        # Spawn items/enemies if provided
        if getattr(turn, "items", None):
            self._spawn_items(turn.items)
        if getattr(turn, "enemies", None):
            self._spawn_enemies(turn.enemies)
        # Suggest actions
        if getattr(turn, "actions", None):
            self.add_message("Actions: " + ", ".join(turn.actions[:5]), "cyan")

    def _apply_turn(self, turn):
        # Update memory on our side if provided via engine
        # Deprecated: handled by StorySystem events
        pass
        if getattr(turn, "actions", None):
            self.add_message("Next: " + ", ".join(turn.actions[:5]), "cyan")

        # Handle richer updates when present (player_updates / room_updates)
        player_updates = getattr(turn, "player_updates", None)
        if isinstance(player_updates, dict):
            self._apply_player_updates(player_updates)
        room_updates = getattr(turn, "room_updates", None)
        if isinstance(room_updates, dict):
            if "items" in room_updates and isinstance(room_updates["items"], list):
                self._spawn_items(room_updates["items"])
            if "enemies" in room_updates and isinstance(room_updates["enemies"], list):
                self._spawn_enemies(room_updates["enemies"])
            # Optional: full layout replacement
            layout = room_updates.get("layout") if isinstance(room_updates, dict) else None
            if isinstance(layout, list) and all(isinstance(r, str) for r in layout):
                self._apply_layout(layout)
            # Optional: new room flag
            if room_updates.get("new_room") is True:
                self._generate_new_room()

        if getattr(turn, "done", False):
            self.add_message("The story concludes.", "yellow")
            self.running = False

    def _apply_player_updates(self, upd: dict):
        if self.player is None:
            return
        self.player.health = int(upd.get("health", self.player.health))
        self.player.mana = int(upd.get("mana", self.player.mana))
        self.player.experience = int(upd.get("experience", self.player.experience))
        self.player.gold = int(upd.get("gold", self.player.gold))
        inv = upd.get("inventory")
        if isinstance(inv, list):
            # Merge simple inventory strings
            for it in inv:
                if isinstance(it, str):
                    self.player.inventory.append(it)

    def _find_random_floor(self):
        # Find random floor tile
        coords = []
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                cell = self.dungeon.grid[y][x]
                char = cell.value if hasattr(cell, "value") else str(cell)
                if char == ".":
                    coords.append((x, y))
        if not coords:
            return 10, 5
        return random.choice(coords)

    def _debug_from_turn(self, turn) -> dict:
        info = {
            "narration": getattr(turn, "narration", None),
            "actions": getattr(turn, "actions", None),
            "player_updates": getattr(turn, "player_updates", None),
            "room_updates": getattr(turn, "room_updates", None),
            "done": getattr(turn, "done", False),
        }
        return info

    def _spawn_items(self, names: List[str]):
        for name in names[:10]:
            x, y = self._find_random_floor()
            self.dungeon.items.append(Item(x, y, "?", name, f"An item: {name}", 0))

    def _spawn_enemies(self, names: List[str]):
        for name in names[:8]:
            x, y = self._find_random_floor()
            enemy = Entity(x, y, "E", "red", name, random.randint(30, 80), 80)
            self.dungeon.entities.append(enemy)

    # ----- Event handling -----
    def _on_event(self, event):
        if isinstance(event, MessageEvent):
            self.add_message(event.text, event.color, event.priority)
        elif isinstance(event, SpawnItemEvent):
            self._spawn_items([event.name])
        elif isinstance(event, SpawnEnemyEvent):
            self._spawn_enemies([event.name])
        elif isinstance(event, LayoutChangedEvent):
            self._apply_layout(event.layout)
        elif isinstance(event, NewRoomEvent):
            self._generate_new_room()
        elif isinstance(event, PlayerUpdatedEvent):
            if event.health is not None:
                self.player.health = event.health
            if event.mana is not None:
                self.player.mana = event.mana
            if event.experience is not None:
                self.player.experience = event.experience
            if event.gold is not None:
                self.player.gold = event.gold
            if event.inventory:
                for it in event.inventory:
                    if isinstance(it, str):
                        self.player.inventory.append(it)
        elif isinstance(event, TurnAdvancedEvent):
            self.turn_count += event.delta
        elif event.__class__.__name__ == "TurnDebugEvent":
            # Avoid direct import cycle; accept any payload dict
            try:
                self.debug_info = getattr(event, "payload", None)
            except Exception:
                self.debug_info = None

    def _apply_layout(self, layout: List[str]):
        # Replace dungeon grid using ASCII rows (█ walls, . floor, + doors, > stairs down, < stairs up)
        height = min(len(layout), self.dungeon.height)
        width = min(max(len(row) for row in layout), self.dungeon.width) if layout else self.dungeon.width
        for y in range(height):
            row = layout[y]
            for x in range(min(len(row), self.dungeon.width)):
                ch = row[x]
                if ch == "█":
                    self.dungeon.grid[y][x] = CellType.WALL
                elif ch == ".":
                    self.dungeon.grid[y][x] = CellType.FLOOR
                elif ch == "+":
                    self.dungeon.grid[y][x] = CellType.DOOR
                elif ch == ">":
                    self.dungeon.grid[y][x] = CellType.STAIRS_DOWN
                elif ch == "<":
                    self.dungeon.grid[y][x] = CellType.STAIRS_UP
                else:
                    # default to floor for unknown walkables, wall for #
                    if ch in ("#",):
                        self.dungeon.grid[y][x] = CellType.WALL
                    else:
                        self.dungeon.grid[y][x] = CellType.FLOOR
        self.dungeon.needs_redraw = True

    def _generate_new_room(self):
        # Simple approach: regenerate dungeon and reposition player
        self.dungeon.generate_dungeon()
        if self.dungeon.player:
            self.dungeon.player.x, self.dungeon.player.y = 10, 5
            self.player.x, self.player.y = 10, 5
        self.dungeon.items.clear()
        # Keep some existing enemies/items? For now, clear items, keep enemies placed by generator
        self.add_message("You step into a new chamber...", "bright_cyan")
        self.dungeon.needs_redraw = True

    def _save_game(self):
        try:
            from .persistence import save_game
            save_game("save.json", self)
            self.add_message("Game saved to save.json", "bright_green")
        except Exception as e:
            self.add_message(f"Save failed: {e}", "red")

    def _load_game(self):
        try:
            from .persistence import load_game
            load_game("save.json", self)
            self.add_message("Game loaded from save.json", "bright_cyan")
        except FileNotFoundError:
            self.add_message("No save.json found", "yellow")
        except Exception as e:
            self.add_message(f"Load failed: {e}", "red")

    def _open_prompt(self):
        # Temporary prompt line for AI commands
        if self.story_system is None or not self.state:
            self.add_message("No AI provider configured. Set one in the launcher.", "yellow")
            return
        # Switch to cooked mode to read a full line
        self.renderer.show_cursor()
        self._exit_raw_mode()
        try:
            action = input("\nAI Action > ").strip()
        except EOFError:
            action = ""
        finally:
            # return to raw mode for non-blocking
            self._enter_raw_mode()
        if not action:
            return
        try:
            AIActionCommand(action, self.story_system).execute(self.state, self.bus)
        except Exception as e:
            self.add_message(f"AI error: {e}", "red")

    # ----- Fallback non-blocking input (Unix) -----
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
                if ch == "\x1b":
                    if select.select([sys.stdin], [], [], 0.001)[0]:
                        next1 = sys.stdin.read(1)
                        if next1 == "[" and select.select([sys.stdin], [], [], 0.001)[0]:
                            next2 = sys.stdin.read(1)
                            if next2 == "A":
                                return "w"
                            if next2 == "B":
                                return "s"
                            if next2 == "D":
                                return "a"
                            if next2 == "C":
                                return "d"
                if ch in ("\n", "\r"):
                    return "enter"
                return ch
        except Exception:
            return None
        return None

    def _manual_input_handler(self):
        if not _UNIX_INPUT_AVAILABLE:
            return
        if not self._raw_mode_enabled:
            self._enter_raw_mode()
        key = self._read_key_nonblocking()
        if not key:
            return
        # Reuse the enhanced input pipeline
        self._handle_input(key.lower())

    def run(self):
        """Main game loop with beautiful rendering"""
        try:
            print("🎮 Starting Enhanced LLM Dungeon Crawler...")
            print("💡 Make sure your terminal is at least 110x35 for best experience!")
            time.sleep(2)

            last_render_time = 0
            target_fps = 15  # Smooth but not too fast

            while self.running and self.player and self.player.health > 0:
                current_time = time.time()

                # Render at target FPS
                if current_time - last_render_time >= 1.0 / target_fps:
                    # Update player entity stats
                    if self.dungeon.player:
                        self.dungeon.player.health = self.player.health
                        self.dungeon.player.max_health = self.player.max_health

                    # Render the beautiful UI
                    self.renderer.render_complete_ui(
                        self.dungeon, self.player, self.turn_count, debug_info=self.debug_info
                    )

                    last_render_time = current_time

                # Poll stdin fallback every frame to support environments where
                # keyboard/pynput import but do not deliver events (e.g., macOS permissions)
                self._manual_input_handler()

                # Small sleep to prevent excessive CPU usage
                time.sleep(1 / 60)  # 60 FPS game logic

            # Game over screen
            if self.player.health <= 0:
                self.renderer.show_game_over(self.player, victory=False)
            else:
                self.renderer.show_game_over(self.player, victory=True)

            # Wait for keypress
            input()

        except KeyboardInterrupt:
            self.add_message("Game interrupted by user", "yellow")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.renderer.show_cursor()
        if hasattr(self, "key_listener"):
            self.key_listener.stop()
        self._exit_raw_mode()


# Export the enhanced game
__all__ = ["EnhancedVisualGame", "EnhancedPlayer"]
