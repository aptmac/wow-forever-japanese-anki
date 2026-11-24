"""
main.py – Entry point for the WoW Forever Japanese Anki add-on.

Hooks into Anki's lifecycle to:
  1. Wire the "Config" button in Anki's Add-ons manager directly to our custom UI dialog
  2. Register menu items under Tools (Import Words, Settings)
  3. Optionally auto-import on profile open
"""

from __future__ import annotations

from aqt import gui_hooks, mw
from . import gui


# Wire the "Config" button in Anki's Add-ons manager dialog to our custom GUI dialog
# instead of Anki's default raw JSON schema editor.
mw.addonManager.setConfigAction(gui.pkg_name(), gui.show_config)


def _on_profile_loaded() -> None:
    """Called when the user opens a profile."""
    gui.setup_menu()

    # Auto-import if configured
    assert mw is not None
    config = mw.addonManager.getConfig(gui.pkg_name()) or {}
    if config.get("auto_import_on_profile_open", False):
        from . import importer
        # Delay slightly so the UI is ready
        mw.progress.timer(1000, importer.run_import, False)


gui_hooks.profile_did_open.append(_on_profile_loaded)
