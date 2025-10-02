"""
PromptDungeon - AI-powered visual dungeon crawler.

Where prompts become adventures! A terminal-based roguelike game that combines
classic dungeon crawling with AI-generated content and stunning ASCII graphics.

Example:
    >>> from promptdungeon import PromptDungeon
    >>> game = PromptDungeon()
    >>> game  # doctest: +ELLIPSIS
    <promptdungeon.enhanced_visual_game.EnhancedVisualGame object at ...>
"""

__version__ = "0.1.0"
__author__ = "Shashank Shankar Jha"
__email__ = "shashankshankar77@gmail.com"
__description__ = "AI-powered visual dungeon crawler where prompts become adventures"

__all__ = [
    "__version__",
    "PromptDungeon",
    "BeautifulRenderer",
    "GameEngine",
    "LLMProvider",
]

# Import main classes for easy access. All optional dependencies are handled
# within the individual modules, so these imports should not crash even if
# optional packages (keyboard/pynput/etc.) are missing.
try:
    from .beautiful_ui_engine import BeautifulRenderer
    from .engine import GameEngine
    from .enhanced_visual_game import EnhancedVisualGame as PromptDungeon
    from .llm import LLMProvider
except Exception as e:  # pragma: no cover
    # Gracefully degrade if something unexpected occurs during import.
    import warnings

    warnings.warn(f"Some PromptDungeon features unavailable: {e}")

    # Provide stub classes so `import promptdungeon` still works.
    class PromptDungeon:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PromptDungeon optional features unavailable. Install extras: pip install 'promptdungeon[all]'"
            )

    class BeautifulRenderer:  # type: ignore
        ...

    class GameEngine:  # type: ignore
        ...

    class LLMProvider:  # type: ignore
        ...
