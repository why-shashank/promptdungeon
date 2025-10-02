# WIP


# PromptDungeon

AI-powered terminal dungeon crawler where prompts become adventures. Play a beautiful ASCII roguelike in your terminal — or plug in OpenAI/Gemini/Ollama to turn it into a DnD-style AI experience where your actions reshape the world.

[![CI](https://github.com/your-org-or-user/promptdungeon/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org-or-user/promptdungeon/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features
- Beautiful terminal UI with status, minimap, messages, and controls
- Real-time movement and simple combat
- DnD-style AI mode: press Enter to command the AI, get narration, and see the map change
- Works without extra input libraries (non-blocking stdin fallback)
- Optional providers: OpenAI, Google Gemini, or local Ollama

## Quick Start

1) Create a virtual environment and install
```
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[all]'
```

2) (Optional) Configure LLM providers
```
# OpenAI	export OPENAI_API_KEY={{OPENAI_API_KEY}}
# Google Gemini	export GOOGLE_API_KEY={{GOOGLE_API_KEY}}
```
Ollama (local) requires no API key, just ensure the daemon is running.

3) Run
```
python3 -m promptdungeon.main play
```
Pick a provider (or continue in visual-only mode). Use WASD/Arrows to move. Press Enter to command the AI.

## Controls
- WASD / Arrow keys: move
- I: inspect surroundings
- Space: wait
- Tab: inventory
- Enter: command AI (type an action)
- H: help
- Q: quit



## Development
- Editable install with dev tools:
```
pip install -e '.[dev]'
```
- Lint & format:
```
ruff .
black .
```
- Tests:
```
pytest
```
- Pre-commit:
```
pre-commit install
```

## Contributing
Contributions are welcome! Please read CONTRIBUTING.md and CODE_OF_CONDUCT.md. Use issues to propose features and report bugs. See .github/ISSUE_TEMPLATE for templates.

## Security
See SECURITY.md for reporting guidelines. Never include secrets in logs, commits, or examples.

## License
MIT — see LICENSE.

AI-powered terminal dungeon crawler with an optional LLM brain. Play a beautiful ASCII roguelike in your terminal. Works in pure visual mode, or plug in OpenAI/Gemini/Ollama for AI-driven narration and content.

## Features
- Beautiful terminal UI with status, minimap, messages, and controls
- Real-time movement and simple combat
- Optional AI room/action generation via OpenAI, Gemini, or local Ollama
- Works without extra input libraries (fallback non-blocking keyboard input)

## Quick Start

1) Install dependencies

- With pip (recommended for local dev):

```
pip install -e '.[all]'
```

- Or minimal install (no cloud LLMs or input libs):

```
pip install -e .
```

2) (Optional) Configure LLM providers

- OpenAI
```
export OPENAI_API_KEY={{OPENAI_API_KEY}}
```
- Google Gemini
```
export GOOGLE_API_KEY={{GOOGLE_API_KEY}}
```
- Ollama (local): install and run Ollama; defaults to llama3.1:8b

3) Run the game

- Via module entrypoint:
```
python -m promptdungeon.main play
```

- Or via console script (after install):
```
promptdungeon play
```

If you have no API keys, choose the visual-only mode when prompted. The game will run without AI content.

## Controls
- WASD or Arrow Keys: move
- I: inspect surroundings
- Space: wait
- Tab: toggle inventory
- H: help
- Q: quit

If you don’t install `keyboard` or `pynput`, the game uses a non-blocking stdin fallback on Unix terminals.

## Troubleshooting
- Missing typer / rich, etc.: install extras: `pip install -e '.[all]'`
- Terminal too small: best experience is at least 110x35
- macOS input permissions: `keyboard` may require Accessibility permissions; the fallback input works without them

## Development
- Run in editable mode: `pip install -e '.[dev]'`
- Run tests (if added): `pytest`
- Lint/format: `ruff .` and `black .`

## License
MIT