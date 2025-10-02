import sys
import time
from typing import Any, Dict, List, Optional


# Enhanced terminal UI with animations and effects
class TerminalEffects:
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
            "gray": "\033[90m",
            "bright_red": "\033[91m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_magenta": "\033[95m",
            "bright_cyan": "\033[96m",
            "bright_white": "\033[97m",
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "underline": "\033[4m",
            "blink": "\033[5m",
            "reverse": "\033[7m",
        }

        # Background colors
        self.bg_colors = {
            "bg_black": "\033[40m",
            "bg_red": "\033[41m",
            "bg_green": "\033[42m",
            "bg_yellow": "\033[43m",
            "bg_blue": "\033[44m",
            "bg_magenta": "\033[45m",
            "bg_cyan": "\033[46m",
            "bg_white": "\033[47m",
            "bg_gray": "\033[100m",
            "bg_bright_red": "\033[101m",
            "bg_bright_green": "\033[102m",
            "bg_bright_yellow": "\033[103m",
            "bg_bright_blue": "\033[104m",
        }

    def color(
        self,
        text: str,
        fg: str | None = None,
        bg: str | None = None,
        style: str | None = None,
    ) -> str:
        """Apply color and styling to text"""
        codes = []
        if fg and fg in self.colors:
            codes.append(self.colors[fg])
        if bg and bg in self.bg_colors:
            codes.append(self.bg_colors[bg])
        if style and style in self.colors:
            codes.append(self.colors[style])

        if codes:
            return f"{''.join(codes)}{text}{self.colors['reset']}"
        return text

    def gradient_text(self, text: str, colors: List[str]) -> str:
        """Create gradient text effect"""
        if len(colors) < 2 or len(text) == 0:
            return text

        result = ""
        color_step = len(text) / (len(colors) - 1)

        for i, char in enumerate(text):
            color_index = min(int(i / color_step), len(colors) - 1)
            result += self.color(char, colors[color_index])

        return result

    def box_chars(self, style="single"):
        """Get box drawing characters"""
        if style == "double":
            return {
                "top_left": "╔",
                "top_right": "╗",
                "bottom_left": "╚",
                "bottom_right": "╝",
                "horizontal": "═",
                "vertical": "║",
                "cross": "╬",
                "top_tee": "╦",
                "bottom_tee": "╩",
                "left_tee": "╠",
                "right_tee": "╣",
            }
        elif style == "rounded":
            return {
                "top_left": "╭",
                "top_right": "╮",
                "bottom_left": "╰",
                "bottom_right": "╯",
                "horizontal": "─",
                "vertical": "│",
                "cross": "┼",
                "top_tee": "┬",
                "bottom_tee": "┴",
                "left_tee": "├",
                "right_tee": "┤",
            }
        else:  # single
            return {
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "horizontal": "─",
                "vertical": "│",
                "cross": "┼",
                "top_tee": "┬",
                "bottom_tee": "┴",
                "left_tee": "├",
                "right_tee": "┤",
            }


class AnimatedProgressBar:
    def __init__(self, width: int = 20, style: str = "█"):
        self.width = width
        self.style = style
        self.animation_frame = 0

    def render(
        self, value: int, max_value: int, color: str = "green", show_spark: bool = True
    ) -> str:
        if max_value <= 0:
            return " " * self.width

        percentage = min(1.0, max(0.0, value / max_value))
        filled_width = int(percentage * self.width)

        # Create base bar
        filled = self.style * filled_width
        empty = "░" * (self.width - filled_width)

        # Add spark effect at the end
        if show_spark and filled_width > 0 and filled_width < self.width:
            spark_chars = ["✦", "✧", "✩", "✪"]
            spark = spark_chars[self.animation_frame % len(spark_chars)]
            if filled_width > 0:
                filled = filled[:-1] + spark if len(filled) > 1 else spark

        self.animation_frame += 1

        effects = TerminalEffects()
        return effects.color(filled, color) + effects.color(empty, "gray")


class Panel:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "",
        border_style: str = "single",
        border_color: str = "white",
        title_color: str = "bright_cyan",
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.border_style = border_style
        self.border_color = border_color
        self.title_color = title_color
        self.content_lines = []
        self.effects = TerminalEffects()

    def add_line(self, text: str, color: str = "white", align: str = "left"):
        """Add a line of content to the panel"""
        self.content_lines.append((text, color, align))

    def clear_content(self):
        """Clear panel content"""
        self.content_lines = []

    def render(self) -> List[str]:
        """Render the panel to a list of strings"""
        lines = []
        box = self.effects.box_chars(self.border_style)

        # Top border with title
        top_line = box["top_left"]
        if self.title:
            title_text = f" {self.title} "
            title_len = len(self.title) + 2
            remaining = self.width - title_len - 2
            left_border = remaining // 2
            right_border = remaining - left_border

            top_line += box["horizontal"] * left_border
            top_line += self.effects.color(title_text, self.title_color, style="bold")
            top_line += box["horizontal"] * right_border
        else:
            top_line += box["horizontal"] * (self.width - 2)
        top_line += box["top_right"]
        lines.append(self.effects.color(top_line, self.border_color))

        # Content lines
        content_height = self.height - 2
        for i in range(content_height):
            line = box["vertical"]

            if i < len(self.content_lines):
                text, color, align = self.content_lines[i]
                content_width = self.width - 2

                # Handle alignment
                if align == "center":
                    text = text.center(content_width)
                elif align == "right":
                    text = text.rjust(content_width)
                else:
                    text = text.ljust(content_width)

                # Truncate if too long
                if len(text) > content_width:
                    text = text[: content_width - 1] + "…"
                else:
                    text = text.ljust(content_width)

                line += self.effects.color(text, color)
            else:
                line += " " * (self.width - 2)

            line += self.effects.color(box["vertical"], self.border_color)
            lines.append(line)

        # Bottom border
        bottom_line = (
            box["bottom_left"]
            + box["horizontal"] * (self.width - 2)
            + box["bottom_right"]
        )
        lines.append(self.effects.color(bottom_line, self.border_color))

        return lines


class StatusDisplay:
    def __init__(self):
        self.effects = TerminalEffects()
        self.health_bar = AnimatedProgressBar(15, "█")
        self.mana_bar = AnimatedProgressBar(15, "█")
        self.exp_bar = AnimatedProgressBar(15, "▓")

    def render_status_panel(self, player, turn_count: int) -> Panel:
        """Create a beautiful status panel"""
        panel = Panel(
            0, 0, 25, 12, "⚔️ STATUS", "double", "bright_cyan", "bright_yellow"
        )

        # Player name and class
        panel.add_line(f"{player.name}", "bright_white", "center")
        panel.add_line(f"the {player.role}", "cyan", "center")
        panel.add_line("", "white")  # Empty line

        # Health
        health_bar = self.health_bar.render(
            player.health, player.max_health, "bright_red"
        )
        panel.add_line(f"❤️  {health_bar} {player.health}/{player.max_health}", "white")

        # Mana
        mana_bar = self.mana_bar.render(player.mana, player.max_mana, "bright_blue")
        panel.add_line(f"💙 {mana_bar} {player.mana}/{player.max_mana}", "white")

        # Experience
        exp_needed = player.level * 100  # Simple progression
        exp_bar = self.exp_bar.render(
            player.experience % exp_needed, exp_needed, "bright_green"
        )
        panel.add_line(f"⭐ {exp_bar} Lv.{player.level}", "white")

        panel.add_line("", "white")  # Empty line

        # Stats
        panel.add_line(f"💰 Gold: {player.gold}", "bright_yellow")
        panel.add_line(f"🎒 Items: {len(player.inventory)}", "bright_green")
        panel.add_line(f"🎯 Turn: {turn_count}", "gray")

        return panel


class MiniMap:
    def __init__(self, width: int = 20, height: int = 10):
        self.width = width
        self.height = height
        self.effects = TerminalEffects()

    def render_minimap_panel(self, dungeon, player_x: int, player_y: int) -> Panel:
        """Create a minimap panel"""
        panel = Panel(
            0,
            0,
            self.width + 2,
            self.height + 2,
            "🗺️ MAP",
            "rounded",
            "green",
            "bright_green",
        )

        # Calculate view area around player
        start_x = max(0, player_x - self.width // 2)
        start_y = max(0, player_y - self.height // 2)
        end_x = min(dungeon.width, start_x + self.width)
        end_y = min(dungeon.height, start_y + self.height)

        for y in range(start_y, end_y):
            line = ""
            for x in range(start_x, end_x):
                if x == player_x and y == player_y:
                    # Player position
                    line += self.effects.color("@", "bright_yellow", style="bold")
                elif (
                    hasattr(dungeon, "grid")
                    and y < len(dungeon.grid)
                    and x < len(dungeon.grid[y])
                ):
                    cell = dungeon.grid[y][x]
                    if hasattr(cell, "value"):
                        char = cell.value
                    else:
                        char = str(cell)

                    # Color code different cell types
                    if char == "█":  # Wall
                        line += self.effects.color("█", "white")
                    elif char == ".":  # Floor
                        line += self.effects.color("·", "gray")
                    elif char == "+":  # Door
                        line += self.effects.color("+", "yellow")
                    elif char == ">":  # Stairs
                        line += self.effects.color(">", "cyan")
                    else:
                        line += char
                else:
                    line += " "

            # Pad line to panel width
            line = line.ljust(self.width)[: self.width]
            panel.add_line(line, "white")

        return panel


class MessageLog:
    def __init__(self, max_messages: int = 10):
        self.messages = []
        self.max_messages = max_messages
        self.effects = TerminalEffects()

    def add_message(self, text: str, color: str = "white", priority: str = "normal"):
        """Add a message to the log"""
        timestamp = time.time()
        self.messages.append(
            {
                "text": text,
                "color": color,
                "priority": priority,
                "timestamp": timestamp,
                "fade": 1.0,
            }
        )

        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def update(self, dt: float):
        """Update message fade effects"""
        for msg in self.messages:
            age = time.time() - msg["timestamp"]
            if age > 5.0:  # Start fading after 5 seconds
                msg["fade"] = max(0.0, 1.0 - (age - 5.0) / 3.0)

    def render_messages_panel(self, width: int = 50, height: int = 8) -> Panel:
        """Render messages panel"""
        panel = Panel(
            0, 0, width, height, "📜 MESSAGES", "single", "yellow", "bright_yellow"
        )

        # Show recent messages
        recent_messages = self.messages[-height + 2 :]  # Account for border
        for msg in recent_messages:
            fade_intensity = msg["fade"]
            if fade_intensity > 0:
                color = msg["color"]
                if fade_intensity < 1.0:
                    color = "gray"  # Faded messages

                # Add priority indicators
                prefix = ""
                if msg["priority"] == "important":
                    prefix = "⚡ "
                elif msg["priority"] == "warning":
                    prefix = "⚠️  "
                elif msg["priority"] == "success":
                    prefix = "✨ "

                text = prefix + msg["text"]
                panel.add_line(text, color)

        return panel


class InventoryDisplay:
    def __init__(self):
        self.effects = TerminalEffects()

    def render_inventory_panel(
        self, inventory: List[str], width: int = 25, height: int = 10
    ) -> Panel:
        """Render inventory panel"""
        panel = Panel(
            0,
            0,
            width,
            height,
            "🎒 INVENTORY",
            "single",
            "bright_green",
            "bright_white",
        )

        if not inventory:
            panel.add_line("Empty", "gray", "center")
            return panel

        # Group similar items
        item_counts = {}
        for item in inventory:
            item_counts[item] = item_counts.get(item, 0) + 1

        # Display items with counts
        for item, count in list(item_counts.items())[: height - 2]:
            if count > 1:
                display_text = f"{item} x{count}"
            else:
                display_text = item

            # Color code by item type
            color = "white"
            if "potion" in item.lower():
                color = "bright_red"
            elif "sword" in item.lower() or "weapon" in item.lower():
                color = "bright_cyan"
            elif "gold" in item.lower():
                color = "bright_yellow"
            elif "scroll" in item.lower():
                color = "bright_magenta"

            panel.add_line(display_text, color)

        return panel


class BeautifulRenderer:
    def __init__(self, width: int = 100, height: int = 30):
        self.width = width
        self.height = height
        self.effects = TerminalEffects()
        self.status_display = StatusDisplay()
        self.minimap = MiniMap(18, 8)
        self.message_log = MessageLog()
        self.inventory_display = InventoryDisplay()

        # Animation state
        self.frame_count = 0
        self.last_frame_time = time.time()

    def clear_screen(self):
        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top

    def hide_cursor(self):
        print("\033[?25l", end="")

    def show_cursor(self):
        print("\033[?25h", end="")

    def move_cursor(self, x: int, y: int):
        print(f"\033[{y + 1};{x + 1}H", end="")

    def render_dungeon_area(
        self,
        dungeon,
        start_x: int = 30,
        start_y: int = 2,
        width: int = 50,
        height: int = 20,
    ) -> List[str]:
        """Render the main dungeon view with enhanced graphics"""
        lines = []

        # Create border around dungeon view
        box = self.effects.box_chars("double")

        # Top border
        top_line = box["top_left"]
        title = " 🏰 DUNGEON 🏰 "
        remaining = width - len(title)
        left_pad = remaining // 2
        right_pad = remaining - left_pad
        top_line += box["horizontal"] * left_pad + self.effects.color(
            title, "bright_magenta", style="bold"
        )
        top_line += box["horizontal"] * right_pad + box["top_right"]
        lines.append(self.effects.color(top_line, "bright_blue"))

        # Dungeon content
        for y in range(height - 2):
            line = self.effects.color(box["vertical"], "bright_blue")

            dungeon_y = y
            if dungeon_y < dungeon.height:
                for x in range(width - 2):
                    dungeon_x = x
                    if dungeon_x < dungeon.width:
                        char = " "
                        color = "white"

                        # Get dungeon cell
                        if (
                            hasattr(dungeon, "grid")
                            and dungeon_y < len(dungeon.grid)
                            and dungeon_x < len(dungeon.grid[dungeon_y])
                        ):
                            cell = dungeon.grid[dungeon_y][dungeon_x]

                            # Enhanced cell rendering
                            if hasattr(cell, "value"):
                                cell_char = cell.value
                            else:
                                cell_char = str(cell)

                            if cell_char == "█":  # Wall
                                char = "█"
                                color = self._get_wall_color(dungeon_x, dungeon_y)
                            elif cell_char == ".":  # Floor
                                char = self._get_floor_char(dungeon_x, dungeon_y)
                                color = "gray"
                            elif cell_char == "+":  # Door
                                char = "+"
                                color = "bright_yellow"
                            elif cell_char == ">":  # Stairs
                                char = ">"
                                color = "bright_cyan"

                        # Check for entities
                        entity_rendered = False
                        if hasattr(dungeon, "entities"):
                            for entity in dungeon.entities:
                                if entity.x == dungeon_x and entity.y == dungeon_y:
                                    char = entity.symbol
                                    color = entity.color
                                    # Add glow effect for player
                                    if entity.symbol == "@":
                                        char = self.effects.color(
                                            "@", "bright_yellow", style="bold"
                                        )
                                        color = None  # Already colored
                                    elif entity.symbol == "E":
                                        # Animated enemy
                                        enemy_chars = ["E", "e", "E", "ë"]
                                        char = enemy_chars[
                                            self.frame_count % len(enemy_chars)
                                        ]
                                        color = "bright_red"
                                    entity_rendered = True
                                    break

                        # Check for items
                        if not entity_rendered and hasattr(dungeon, "items"):
                            for item in dungeon.items:
                                if item.x == dungeon_x and item.y == dungeon_y:
                                    # Animated item
                                    item_chars = ["?", "¿", "?", "⁇"]
                                    char = item_chars[
                                        self.frame_count % len(item_chars)
                                    ]
                                    color = "bright_green"
                                    break

                        if color:
                            line += self.effects.color(char, color)
                        else:
                            line += char
                    else:
                        line += " "
            else:
                line += " " * (width - 2)

            line += self.effects.color(box["vertical"], "bright_blue")
            lines.append(line)

        # Bottom border
        bottom_line = (
            box["bottom_left"] + box["horizontal"] * (width - 2) + box["bottom_right"]
        )
        lines.append(self.effects.color(bottom_line, "bright_blue"))

        return lines

    def _get_wall_color(self, x: int, y: int) -> str:
        """Get varying wall colors for depth"""
        colors = ["white", "bright_white", "gray"]
        return colors[(x + y) % len(colors)]

    def _get_floor_char(self, x: int, y: int) -> str:
        """Get varying floor characters"""
        chars = ["·", ".", "˙", "⋅"]
        return chars[(x * 3 + y * 7) % len(chars)]

    def render_complete_ui(
        self,
        dungeon,
        player,
        turn_count: int,
        messages: List[str] | None = None,
        debug_info: Optional[Dict[str, Any]] = None,
    ):
        """Render the complete beautiful UI"""
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        self.frame_count += 1

        # Clear screen
        self.clear_screen()
        self.hide_cursor()

        # Add any new messages
        if messages:
            for msg in messages:
                self.message_log.add_message(msg)

        # Update animations
        self.message_log.update(dt)

        # Create panels
        status_panel = self.status_display.render_status_panel(player, turn_count)
        minimap_panel = self.minimap.render_minimap_panel(dungeon, player.x, player.y)
        messages_panel = self.message_log.render_messages_panel(50, 8)
        inventory_panel = self.inventory_display.render_inventory_panel(
            player.inventory, 25, 8
        )

        # Render status panel (left side)
        status_lines = status_panel.render()
        for i, line in enumerate(status_lines):
            self.move_cursor(0, i)
            print(line)

        # Render minimap (left side, below status)
        minimap_lines = minimap_panel.render()
        for i, line in enumerate(minimap_lines):
            self.move_cursor(0, len(status_lines) + i + 1)
            print(line)

        # Render main dungeon area (center)
        dungeon_lines = self.render_dungeon_area(dungeon, 30, 2, 50, 20)
        for i, line in enumerate(dungeon_lines):
            self.move_cursor(30, 2 + i)
            print(line)

        # Render messages panel (bottom)
        messages_lines = messages_panel.render()
        for i, line in enumerate(messages_lines):
            self.move_cursor(30, 24 + i)
            print(line)

        # Render inventory panel (right side)
        inventory_lines = inventory_panel.render()
        for i, line in enumerate(inventory_lines):
            self.move_cursor(85, 2 + i)
            print(line)

        # Render controls help (bottom right)
        self.move_cursor(85, 12)
        controls_panel = Panel(
            0, 0, 25, 11, "🎮 CONTROLS", "single", "cyan", "bright_cyan"
        )
        controls_panel.add_line("WASD - Move", "white")
        controls_panel.add_line("I - Inspect", "yellow")
        controls_panel.add_line("Space - Wait", "green")
        controls_panel.add_line("Tab - Inventory", "magenta")
        controls_panel.add_line("Enter - Command AI", "bright_yellow")
        controls_panel.add_line("K - Save", "bright_green")
        controls_panel.add_line("L - Load", "bright_cyan")
        controls_panel.add_line("H - Help", "cyan")
        controls_panel.add_line("Q - Quit", "red")

        controls_lines = controls_panel.render()
        for i, line in enumerate(controls_lines):
            self.move_cursor(85, 12 + i)
            print(line)

        # Render story debug panel (right side, below controls)
        if debug_info:
            self.move_cursor(85, 22)
            debug_panel = Panel(
                0, 0, 25, 12, "🧪 STORY DEBUG", "single", "magenta", "bright_magenta"
            )

            # Summarize debug info with truncation
            def add_kv(label: str, value: str, color: str = "white"):
                debug_panel.add_line(f"{label}: {value}", color)

            narrative_preview = (
                (str(debug_info.get("narration", ""))[:20] + "…")
                if debug_info.get("narration")
                else "-"
            )
            add_kv("Narr", narrative_preview, "bright_white")

            actions = debug_info.get("actions") or []
            add_kv("Acts", str(len(actions)), "cyan")

            pu = debug_info.get("player_updates")
            add_kv(
                "PUpd",
                ",".join(pu.keys())[:16]
                + ("…" if pu and len(",".join(pu.keys())) > 16 else "")
                if isinstance(pu, dict)
                else "-",
                "bright_green",
            )

            ru = debug_info.get("room_updates")
            if isinstance(ru, dict):
                add_kv("R.Itm", str(len(ru.get("items", []))), "green")
                add_kv("R.Enm", str(len(ru.get("enemies", []))), "red")
                add_kv("NewRm", str(bool(ru.get("new_room", False))), "yellow")
                layout = ru.get("layout")
                add_kv(
                    "Layout",
                    f"{len(layout)} rows" if isinstance(layout, list) else "-",
                    "bright_cyan",
                )
            else:
                add_kv("RUpd", "-", "gray")

            add_kv("Done", str(bool(debug_info.get("done", False))), "yellow")

            dbg_lines = debug_panel.render()
            for i, line in enumerate(dbg_lines):
                self.move_cursor(85, 22 + i)
                print(line)

        # Add title banner at top
        title_text = "⚔️ 🏰 LLM DUNGEON CRAWLER 🏰 ⚔️"
        gradient_title = self.effects.gradient_text(
            title_text,
            [
                "bright_red",
                "bright_yellow",
                "bright_green",
                "bright_cyan",
                "bright_blue",
                "bright_magenta",
            ],
        )
        self.move_cursor((self.width - len(title_text)) // 2, 0)
        print(gradient_title)
        # Hint line
        self.move_cursor(0, 1)
        hint = "Tip: Press Enter to command the AI (DnD mode)"
        print(self.effects.color(hint.ljust(self.width), "bright_yellow"))

        # Flush output
        sys.stdout.flush()

    def show_game_over(self, player, victory: bool = False):
        """Show beautiful game over screen"""
        self.clear_screen()

        if victory:
            title = "🎉 VICTORY! 🎉"
            color = "bright_green"
            message = f"{player.name} the {player.role} has conquered the dungeon!"
        else:
            title = "💀 GAME OVER 💀"
            color = "bright_red"
            message = f"{player.name} the {player.role} has fallen in battle..."

        # Center the game over screen
        panel = Panel(30, 10, 40, 10, title, "double", color, color)
        panel.add_line("", "white")
        panel.add_line(message, "white", "center")
        panel.add_line("", "white")
        panel.add_line(f"Final Level: {player.level}", "yellow", "center")
        panel.add_line(f"Gold Earned: {player.gold}", "bright_yellow", "center")
        panel.add_line("", "white")
        panel.add_line("Press any key to exit", "gray", "center")

        lines = panel.render()
        for i, line in enumerate(lines):
            self.move_cursor(30, 10 + i)
            print(line)

        sys.stdout.flush()


# Export the beautiful renderer
__all__ = [
    "BeautifulRenderer",
    "TerminalEffects",
    "Panel",
    "AnimatedProgressBar",
    "MessageLog",
]
