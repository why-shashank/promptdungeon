from __future__ import annotations

import os
import time
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
import shutil
import requests
from enum import Enum

from .engine import GameConfig
from .enhanced_visual_game import EnhancedVisualGame

console = Console()
app = typer.Typer(add_completion=False, no_args_is_help=False)


load_dotenv()


def create_title_art():
    """Display boxed ASCII title for PromptDungeon"""
    title_lines = [
        "╔" + "═" * 118 + "╗",
        "║" + " " * 118 + "║",
        "║          __________                               __    ________                                             "
        + "        ║",
        "║          \\______   \\_______  ____   _____ _______/  |_  \\______ \\  __ __  ____    ____   ____  ____   ____           ║",
        "║           |     ___/\\_  __ \\/  _ \\ /     \\\\____ \\   __\\  |    |  \\|  |  \\/    \\  / ___\\_/ __ \\/  _ \\ /    \\          ║",
        "║           |    |     |  | \\(  <_> )  Y Y  \\  |_> >  |    |    `   \\  |  /   |  \\/ /_/  >  ___(  <_> )   |  \\         ║",
        "║           |____|     |__|   \\____/|__|_|  /   __/|__|   /_______  /____/|___|  /\\___  / \\___  >____/|___|  /         ║",
        "║                                         \\/|__|                  \\/           \\/ _____/      \\/           \\/          ║",
        "║" + " " * 118 + "║",
        "║                         👾 Procedurally Generated 👾 Prompt-Powered 👾 AI-Driven 👾"
        + " " * 34
        + "║",
        "║" + " " * 118 + "║",
        "╚" + "═" * 118 + "╝",
    ]
    console.print(("\n".join(title_lines)), style="bold bright_green")


def check_terminal_size():
    """Check if terminal is large enough"""
    size = os.get_terminal_size()
    min_width, min_height = 110, 35

    if size.columns < min_width or size.lines < min_height:
        console.print(
            Panel(
                f"⚠️  [yellow]Terminal Size Warning[/yellow]\n\n"
                f"Current: [red]{size.columns}x{size.lines}[/red]\n"
                f"Recommended: [green]{min_width}x{min_height}[/green]\n\n"
                f"For the best experience, please resize your terminal window.\n"
                f"The game will still work, but the UI might be cramped.",
                title="Display Settings",
                border_style="yellow",
            )
        )

        if not Confirm.ask("Continue anyway?", default=True):
            raise typer.Exit()
        console.print()


# Status labels


class Status(Enum):
    READY = "✅ Ready"
    MISSING = "❌ Missing"
    LIMITED = "⚠️  Limited"
    INSTALLED = "⚠️ Installed"


def check_module(module_player_name):
    """Check if a module can be imported"""
    try:
        __import__(module_player_name)
        return True
    except ImportError:
        return False


def check_ollama():
    """Check if Ollama CLI is installed and service is running"""
    installed = shutil.which("ollama") is not None
    running = False

    if installed:
        try:
            res = requests.get("http://localhost:11434/api/tags", timeout=2)
            running = res.status_code == 200
        except requests.RequestException:
            pass

    return {"installed": installed, "running": running}


def check_dependencies():
    """Check for optional dependencies and display their status"""
    status = {
        "keyboard": check_module("keyboard"),
        "pynput": check_module("pynput"),
        "openai": check_module("openai"),
        "google_ai": check_module("google.generativeai"),
        "claude": check_module("anthropic"),
    }

    ollama_status = check_ollama()

    depedency_table = Table(title="🔧 Dependencies Status", show_header=True)
    depedency_table.add_column("Component", style="cyan", width=20)
    depedency_table.add_column("Status", width=12)
    depedency_table.add_column("Notes", style="dim")

    if status["keyboard"]:
        depedency_table.add_row(
            "Input (keyboard)", Status.READY.value, "Best performance"
        )
    elif status["pynput"]:
        depedency_table.add_row(
            "Input (pynput)", Status.READY.value, "Good alternative"
        )
    else:
        depedency_table.add_row(
            "Input", Status.LIMITED.value, "Install 'keyboard' or 'pynput'"
        )

    if status["openai"]:
        depedency_table.add_row("OpenAI", Status.READY.value, "Requires API key")
    else:
        depedency_table.add_row("OpenAI", Status.MISSING.value, "pip install openai")

    if status["google_ai"]:
        depedency_table.add_row("Google Gemini", Status.READY.value, "Requires API key")
    else:
        depedency_table.add_row(
            "Google Gemini", Status.MISSING.value, "pip install google-generativeai"
        )
    if status["claude"]:
        depedency_table.add_row(
            "Claude (Anthropic)", Status.READY.value, "Requires API key"
        )
    else:
        depedency_table.add_row(
            "Claude (Anthropic)", Status.MISSING.value, "pip install anthropic"
        )

    if ollama_status["installed"]:
        if ollama_status["running"]:
            depedency_table.add_row(
                "Ollama (Local)", Status.READY.value, "Service is running"
            )
        else:
            depedency_table.add_row(
                "Ollama (Local)", Status.INSTALLED.value, "Start the Ollama service"
            )
    else:
        depedency_table.add_row(
            "Ollama (Local)", Status.MISSING.value, "Install from https://ollama.com"
        )

    console.print(Panel(depedency_table, border_style="blue"))
    console.print()


def get_player_info():
    console.print(
        Panel(
            "⚔️ [bold bright_cyan]Create Your Character[/bold bright_cyan] ⚔️",
            border_style="bright_cyan",
        )
    )

    player_name = Prompt.ask(
        "[bright_white]Hero player_name[/bright_white]",
        default="Adventurer",
        show_default=True,
    )

    # Character class selection
    console.print("\n🧙 [bold]Choose Your Class:[/bold]")

    classes_table = Table(show_header=False, show_edge=False)
    classes_table.add_column("Num", width=5, style="bright_yellow")
    classes_table.add_column("Class", width=12, style="bright_white")
    classes_table.add_column("Health", width=8, style="red")
    classes_table.add_column("Mana", width=8, style="blue")
    classes_table.add_column("Special Ability", style="green")

    classes = [
        ("1", "Warrior", "120❤️", "30💙", "Extra damage & defense"),
        ("2", "Mage", "70❤️", "80💙", "Powerful spells & magic"),
        ("3", "Rogue", "80❤️", "35💙", "Critical hits & stealth"),
        ("4", "Cleric", "100❤️", "60💙", "Healing & holy magic"),
        ("5", "Ranger", "90❤️", "40💙", "Ranged combat & tracking"),
    ]

    for num, cls, health, mana, special in classes:
        classes_table.add_row(num, cls, health, mana, special)

    console.print(classes_table)
    console.print()

    class_choice = Prompt.ask(
        "Select class number", choices=["1", "2", "3", "4", "5"], default="1"
    )

    class_player_names = ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"]
    selected_class = class_player_names[int(class_choice) - 1]

    console.print(
        f"\n✨ [bold bright_green]{player_name} the {selected_class}[/bold bright_green] - Ready for adventure!"
    )

    return player_name, selected_class


def configure_llm(available_providers: list):
    """Configure LLM provider with beautiful interface"""
    if not available_providers:
        console.print(
            Panel(
                "🤖 [yellow]No cloud LLM providers detected[/yellow]\n\n"
                "The game will run in visual-only mode, or you can:\n"
                "• Install OpenAI: [cyan]pip install openai[/cyan]\n"
                "• Install Gemini: [cyan]pip install google-generativeai[/cyan]\n"
                "• Use Ollama for local AI (no API key needed)\n\n"
                "Would you like to continue with visual-only mode?",
                title="LLM Configuration",
                border_style="yellow",
            )
        )

        if not Confirm.ask("Continue without LLM features?", default=True):
            raise typer.Exit()

        return None, None

    console.print(
        Panel(
            "🤖 [bold bright_cyan]AI Configuration[/bold bright_cyan]\n\n"
            "Choose your AI provider for dynamic content generation:",
            border_style="bright_cyan",
        )
    )

    # Show available providers
    providers_table = Table(show_header=False, show_edge=False)
    providers_table.add_column("Option", width=8, style="bright_yellow")
    providers_table.add_column("Provider", width=15, style="bright_white")
    providers_table.add_column("Quality", width=10, style="green")
    providers_table.add_column("Cost", width=10, style="cyan")
    providers_table.add_column("Setup", style="dim")

    options = ["ollama"]  # Always available
    providers_table.add_row("1", "Ollama (Local)", "Good", "Free", "No API key needed")

    option_num = 2
    if "OpenAI" in available_providers:
        options.append("openai")
        providers_table.add_row(
            str(option_num), "OpenAI GPT", "Excellent", "Paid", "Requires API key"
        )
        option_num += 1

    if "Gemini" in available_providers:
        options.append("gemini")
        providers_table.add_row(
            str(option_num),
            "Google Gemini",
            "Very Good",
            "Free tier",
            "Requires API key",
        )
        option_num += 1

    console.print(providers_table)
    console.print()

    choice = Prompt.ask(
        "Select AI provider",
        choices=[str(i) for i in range(1, len(options) + 1)],
        default="1",
    )

    selected_provider = options[int(choice) - 1]

    # Check for API keys if needed
    api_key_status = None
    if selected_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            console.print(
                Panel(
                    "⚠️  [yellow]OpenAI API Key Required[/yellow]\n\n"
                    "Set your API key with:\n"
                    "[cyan]export OPENAI_API_KEY='your-key-here'[/cyan]\n\n"
                    "Or create a .env file with:\n"
                    "[cyan]OPENAI_API_KEY=your-key-here[/cyan]",
                    border_style="yellow",
                )
            )
            api_key_status = "missing"
        else:
            api_key_status = "found"

    elif selected_provider == "gemini":
        if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
            console.print(
                Panel(
                    "⚠️  [yellow]Google API Key Required[/yellow]\n\n"
                    "Set your API key with:\n"
                    "[cyan]export GOOGLE_API_KEY='your-key-here'[/cyan]\n\n"
                    "Or create a .env file with:\n"
                    "[cyan]GOOGLE_API_KEY=your-key-here[/cyan]",
                    border_style="yellow",
                )
            )
            api_key_status = "missing"
        else:
            api_key_status = "found"

    return selected_provider, api_key_status


def show_game_start_sequence(player_name: str, player_class: str, provider: str):
    """Show beautiful game start sequence"""
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Initialize LLM
        if provider:
            task1 = progress.add_task(
                f"🤖 Initializing {provider.upper()} AI...", total=None
            )
            time.sleep(1)
            progress.update(task1, completed=100, description="✅ AI Ready")

        # Generate world
        task2 = progress.add_task("🏰 Generating dungeon layout...", total=None)
        time.sleep(1.5)
        progress.update(task2, completed=100, description="✅ Dungeon Created")

        # Initialize character
        task3 = progress.add_task(
            f"⚔️  Preparing {player_name} the {player_class}...", total=None
        )
        time.sleep(1)
        progress.update(task3, completed=100, description="✅ Hero Ready")

        # Final setup
        task4 = progress.add_task("✨ Finalizing magical enchantments...", total=None)
        time.sleep(0.8)
        progress.update(task4, completed=100, description="✅ Adventure Begins")

    console.print()
    console.print(
        Panel(
            f"🎉 [bold bright_green]Ready to Adventure![/bold bright_green] 🎉\n\n"
            f"Hero: [bright_cyan]{player_name} the {player_class}[/bright_cyan]\n"
            f"AI Provider: [yellow]{provider.upper() if provider else 'Visual Mode'}[/yellow]\n\n"
            f"💡 [dim]Pro Tips:[/dim]\n"
            f"• Use [bright_white]WASD[/bright_white] or arrow keys to move\n"
            f"• Press [bright_white]I[/bright_white] to inspect surroundings\n"
            f"• Press [bright_white]Tab[/bright_white] to toggle inventory\n"
            f"• Press [bright_white]Q[/bright_white] to quit anytime",
            title="🚀 Launch Ready",
            border_style="bright_green",
        )
    )

    countdown_text = "Starting in: "
    for i in range(3, 0, -1):
        console.print(
            f"\r{countdown_text}[bold bright_yellow]{i}[/bold bright_yellow]", end=""
        )
        time.sleep(1)

    console.print(f"\r{countdown_text}[bold bright_green]GO![/bold bright_green]")
    time.sleep(0.5)


@app.callback()
def main_callback():
    """🏰 Beautiful LLM-powered visual dungeon crawler with stunning terminal UI."""


@app.command()
def play(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="AI provider to use (ollama|openai|gemini). Defaults to auto-detect.",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Model player_name override for selected provider.",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Deterministic random seed for reproducible sessions.",
    ),
    log_ai: bool = typer.Option(
        False,
        "--log-ai/--no-log-ai",
        help="Log raw AI turns to logs/ai_turns.log",
    ),
):
    """Play the enhanced visual dungeon crawler."""
    # Load environment (.env) if present so API keys can be read
    try:
        load_dotenv()
    except Exception:
        pass

    # Terminal sizing (best-effort, don't crash in non-TTY)
    try:
        check_terminal_size()
    except OSError:
        # Non-interactive envs may not have a valid TTY size
        pass

    # Dependency info
    dep_status, available_llms = check_dependencies()

    # Player setup
    player_name, role = get_player_info()

    # LLM selection (optional)
    selected_provider = None
    api_key_status = None
    if provider is not None:
        # If explicitly provided, respect it even if not detected
        selected_provider = provider.lower()
    else:
        # Offer selection only if something is available
        _, available_llms = dep_status, available_llms
        if available_llms:
            selected_provider, api_key_status = configure_llm(available_llms)

    # Show start sequence
    show_game_start_sequence(player_name, role, selected_provider or "visual")

    # Create game
    llm_instance = None
    if selected_provider:
        try:
            from .llm import autodetect_provider

            llm_instance = autodetect_provider(selected_provider, model_override=model)
            # Pass logging preference via env for StorySystem
            if log_ai:
                os.environ["PD_LOG_AI"] = "1"
        except Exception as e:
            console.print(
                Panel(
                    f"Failed to initialize provider '{selected_provider}': {e}",
                    border_style="red",
                    title="LLM Error",
                )
            )
            llm_instance = None

    game = EnhancedVisualGame(
        width=60,
        height=20,
        llm_provider=llm_instance,
        config=GameConfig(player_name=player_name, role=role),
    )
    game.initialize_game(player_name=player_name, player_class=role, seed=seed)
    try:
        game.run()
    except Exception as e:
        console.print(Panel(f"Unexpected error: {e}", border_style="red"))
        raise
    """🎮 Launch the full interactive dungeon crawler experience"""
    load_dotenv(override=False)

    try:
        # Welcome screen
        show_welcome_screen()

        # Terminal size check
        check_terminal_size()

        # Dependencies check
        status, llm_providers = check_dependencies()

        # Player creation
        player_name, player_class = get_player_info()

        # LLM configuration
        provider, api_status = configure_llm(llm_providers)

        if provider and api_status == "missing":
            console.print("\n[yellow]Continuing without AI features...[/yellow]")
            provider = None

        # Game start sequence
        show_game_start_sequence(player_name, player_class, provider)

        # Initialize game
        console.clear()
        console.print("🎮 [bold bright_cyan]Entering the dungeon...[/bold bright_cyan]")

        # Create enhanced game
        game = EnhancedVisualGame(width=60, height=20)

        # Initialize LLM if available
        llm_provider = None
        if provider:
            try:
                llm_provider = autodetect_provider(provider_hint=provider)
                console.print("✅ AI system online")
            except Exception as e:
                console.print(f"⚠️  AI system unavailable: {e}")
                time.sleep(1)

        # Initialize and run game
        game.initialize_game(player_name, player_class)
        time.sleep(1)  # Brief pause before starting

        game.run()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Adventure interrupted. Safe travels![/yellow]")
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {e}[/red]")
        console.print("[dim]Check your terminal size and dependencies.[/dim]")
        raise typer.Exit(code=1)


@app.command()
def demo():
    """🎯 Quick demo with default settings (no LLM required)"""
    console.print("🚀 [bold bright_cyan]Demo Mode - Quick Start[/bold bright_cyan]")
    console.print("Starting with default character and no AI features...\n")

    try:
        game = EnhancedVisualGame(width=50, height=18)
        game.initialize_game("Demo Hero", "Warrior")

        console.print("💡 Demo Tips:")
        console.print("• This is pure visual mode - no AI generation")
        console.print("• Use WASD to move around the dungeon")
        console.print("• Fight enemies and collect items")
        console.print("• Press Q to quit anytime\n")

        input("Press Enter to start demo...")
        game.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo ended.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")


@app.command()
def install():
    """📦 Install recommended dependencies for the best experience"""
    console.print(
        Panel(
            "📦 [bold bright_cyan]Dependency Installation Guide[/bold bright_cyan]\n\n"
            "For the full experience, install these packages:",
            title="Setup Guide",
            border_style="bright_cyan",
        )
    )

    depedency_table = Table(show_header=True)
    depedency_table.add_column("Package", style="bright_white", width=20)
    depedency_table.add_column("Purpose", style="cyan", width=25)
    depedency_table.add_column("Install Command", style="green")

    depedency_table.add_row(
        "keyboard", "Real-time input (Linux/Win)", "pip install keyboard"
    )
    depedency_table.add_row("pynput", "Cross-platform input", "pip install pynput")
    depedency_table.add_row("openai", "OpenAI GPT integration", "pip install openai")
    depedency_table.add_row(
        "google-generativeai", "Google Gemini AI", "pip install google-generativeai"
    )
    depedency_table.add_row("colorama", "Better Windows colors", "pip install colorama")

    console.print(depedency_table)
    console.print()

    console.print("[bold bright_yellow]💡 Quick Install Commands:[/bold bright_yellow]")
    console.print()
    console.print("🎮 [bright_cyan]For best gaming experience:[/bright_cyan]")
    console.print("[green]pip install keyboard pynput colorama[/green]")
    console.print()
    console.print("🤖 [bright_cyan]For AI features (choose one):[/bright_cyan]")
    console.print("[green]pip install openai[/green]  # For OpenAI GPT")
    console.print("[green]pip install google-generativeai[/green]  # For Google Gemini")
    console.print()
    console.print("🚀 [bright_cyan]Install everything:[/bright_cyan]")
    console.print(
        "[green]pip install keyboard pynput colorama openai google-generativeai[/green]"
    )
    console.print()

    console.print(
        Panel(
            "💎 [bold]Pro Tip:[/bold] After installing, set up your API keys:\n\n"
            "[green]export OPENAI_API_KEY='your-openai-key'[/green]\n"
            "[green]export GOOGLE_API_KEY='your-google-key'[/green]\n\n"
            "Or create a [cyan].env[/cyan] file with these values.",
            title="API Setup",
            border_style="yellow",
        )
    )


@app.command()
def status():
    """📊 Check system status and configuration"""
    console.print(
        Panel(
            "📊 [bold bright_cyan]System Status Check[/bold bright_cyan]",
            border_style="bright_cyan",
        )
    )

    # Terminal info
    size = os.get_terminal_size()
    console.print(
        f"🖥️  Terminal Size: [bright_white]{size.columns}x{size.lines}[/bright_white]"
    )

    if size.columns >= 110 and size.lines >= 35:
        console.print("   ✅ Perfect size for beautiful UI")
    elif size.columns >= 80 and size.lines >= 25:
        console.print("   ⚠️  Adequate size, but larger is better")
    else:
        console.print("   ❌ Too small - please resize for best experience")

    console.print()

    # Check dependencies again
    _, _ = check_dependencies()

    # Environment variables
    console.print("🔑 [bold]API Keys Status:[/bold]")
    api_table = Table(show_header=False, show_edge=False)
    api_table.add_column("Provider", width=15, style="cyan")
    api_table.add_column("Status", width=12)
    api_table.add_column("Variable", style="dim")

    if os.getenv("OPENAI_API_KEY"):
        api_table.add_row("OpenAI", "✅ Configured", "OPENAI_API_KEY")
    else:
        api_table.add_row("OpenAI", "❌ Missing", "OPENAI_API_KEY")

    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        api_table.add_row("Google Gemini", "✅ Configured", "GOOGLE_API_KEY")
    else:
        api_table.add_row("Google Gemini", "❌ Missing", "GOOGLE_API_KEY")

    api_table.add_row("Ollama", "✅ Always Ready", "(Local AI)")

    console.print(api_table)
    console.print()

    console.print(
        "🎮 [bold bright_green]Ready to play![/bold bright_green] Use [cyan]aigame play[/cyan] to start."
    )


if __player_name__ == "__main__":
    app()
