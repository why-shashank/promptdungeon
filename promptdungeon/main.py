"""
Entry point for PromptDungeon.

This module provides the main entry point when running the package
as a script or using the promptdungeon/pd commands.
"""

import sys


def main():
    """Main entry point for PromptDungeon"""
    try:
        # Import here to handle missing dependencies gracefully
        from .cli import app

        # Show banner
        print("🏰 PromptDungeon - Where prompts become adventures! 🏰\n")

        # Run the CLI app
        app()

    except ImportError as e:
        print("❌ PromptDungeon Installation Error")
        print(f"Missing dependencies: {e}")
        print("\n💡 Try installing with:")
        print("   uv add 'promptdungeon[all]'")
        print("   # or")
        print("   pip install 'promptdungeon[all]'")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Thanks for exploring PromptDungeon!")
        sys.exit(0)

    except Exception as e:
        print(f"❌ PromptDungeon Error: {e}")
        print("💡 Try: promptdungeon --help")
        sys.exit(1)


if __name__ == "__main__":
    main()
