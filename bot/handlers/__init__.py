from importlib import import_module

from pyrogram.client import Client

# Handlers modules to load
HANDLER_MODULES = [
    "bot.handlers.common",
    # "bot.handlers.auth",
    # "bot.handlers.tasks",
    # "bot.handlers.finance",
    # "bot.handlers.google",
]


def register_all_handlers(app: Client) -> None:
    """Register all handlers with the client."""
    for module_name in HANDLER_MODULES:
        try:
            module = import_module(module_name)
            if hasattr(module, "register_handlers"):
                module.register_handlers(app)
        except Exception as e:
            print(f"Error registering handlers from {module_name}: {e}")


__all__ = ["register_all_handlers"]
