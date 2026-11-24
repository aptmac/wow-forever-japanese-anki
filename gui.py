"""
gui.py – Settings dialog for the WoW Forever Japanese Anki add-on.

Provides:
  - A configuration dialog to choose the target deck and SavedVariables path
  - Menu items under Tools
  - Custom config action hooked to Anki's Add-ons manager "Config" button
"""

from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from aqt.utils import showInfo, showWarning


def pkg_name() -> str:
    """Return the addon package name recognized by Anki's addon manager."""
    if mw and hasattr(mw.addonManager, "addon_from_module"):
        return mw.addonManager.addon_from_module(__name__)
    return __name__.split(".")[0]


class ConfigDialog(QDialog):
    """Configuration dialog for the add-on."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("WoW Forever Japanese — Deck Settings")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # ── Deck Selection (Primary control) ─────────────────────────────
        deck_group = QGroupBox("Target Deck")
        deck_layout = QVBoxLayout(deck_group)

        deck_desc = QLabel("Choose the Anki deck to send your WoW cards into:")
        deck_layout.addWidget(deck_desc)

        self._deck_combo = QComboBox()
        self._deck_combo.setEditable(False)
        self._populate_decks()
        deck_layout.addWidget(self._deck_combo)

        layout.addWidget(deck_group)

        # ── SavedVariables Path ──────────────────────────────────────────
        path_group = QGroupBox("WoW SavedVariables File (Required)")
        path_layout = QVBoxLayout(path_group)

        path_desc = QLabel(
            "Select your WoWForeverJapanese.lua file from your account's SavedVariables folder:\n"
            "World of Warcraft\\<flavor>\\WTF\\Account\\<ACCOUNT>\\SavedVariables\\WoWForeverJapanese.lua\n\n"
            "(Note: This is NOT Main.lua or .toc in Interface\\AddOns; WoW saves your banked words to SavedVariables upon /reload or logout.)"
        )
        path_desc.setWordWrap(True)
        path_layout.addWidget(path_desc)

        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select your SavedVariables\\WoWForeverJapanese.lua...")
        path_row.addWidget(self._path_edit)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(browse_btn)
        path_layout.addLayout(path_row)

        layout.addWidget(path_group)

        # ── Options ──────────────────────────────────────────────────────
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self._auto_import_cb = QCheckBox(
            "Automatically import new words when opening Anki profile"
        )
        options_layout.addWidget(self._auto_import_cb)

        layout.addWidget(options_group)

        # ── Buttons ──────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_decks(self) -> None:
        """Fill the deck dropdown with all existing decks in the collection."""
        self._deck_combo.clear()
        if mw is not None and mw.col is not None:
            if hasattr(mw.col.decks, "all_names"):
                deck_names = sorted(mw.col.decks.all_names())
            else:
                decks = mw.col.decks.all_names_and_ids()
                deck_names = sorted([getattr(d, "name", d["name"]) for d in decks])
            for name in deck_names:
                self._deck_combo.addItem(name)

    def _browse_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select WoWForeverJapanese.lua",
            "",
            "Lua files (*.lua);;All files (*.*)",
        )
        if path:
            self._path_edit.setText(path)

    def _load_config(self) -> None:
        if mw is None:
            return
        config = mw.addonManager.getConfig(pkg_name()) or {}
        self._path_edit.setText(config.get("saved_variables_path", ""))

        deck_name = config.get("deck_name", "WoW Forever Japanese")
        idx = self._deck_combo.findText(deck_name)
        if idx >= 0:
            self._deck_combo.setCurrentIndex(idx)
        else:
            # If the configured deck doesn't exist yet, append it so it's visible & selected
            self._deck_combo.addItem(deck_name)
            self._deck_combo.setCurrentIndex(self._deck_combo.count() - 1)

        self._auto_import_cb.setChecked(config.get("auto_import_on_profile_open", False))

    def _save_and_close(self) -> None:
        if mw is None:
            return
        path = self._path_edit.text().strip()
        if not path:
            showWarning("Please select your WoWForeverJapanese.lua file before saving.")
            return
        from pathlib import Path
        p = Path(path)
        if not p.is_file():
            showWarning(f"File not found:\n{path}\n\nPlease select a valid WoWForeverJapanese.lua file.")
            return

        config = mw.addonManager.getConfig(pkg_name()) or {}
        config["saved_variables_path"] = path
        config["deck_name"] = self._deck_combo.currentText().strip() or "WoW Forever Japanese"
        config["auto_import_on_profile_open"] = self._auto_import_cb.isChecked()
        mw.addonManager.writeConfig(pkg_name(), config)
        self.accept()


def show_config() -> None:
    """Open the configuration dialog."""
    if mw is None:
        return
    if mw.col is None:
        showInfo("Please open an Anki profile before configuring the deck.")
        return
    dialog = ConfigDialog(mw)
    dialog.exec()


def setup_menu() -> None:
    """Add menu items under Tools."""
    assert mw is not None

    # Import action
    import_action = QAction("WoW Forever Japanese: Import Words", mw)
    import_action.triggered.connect(_on_import)
    mw.form.menuTools.addAction(import_action)

    # Settings action
    config_action = QAction("WoW Forever Japanese: Settings…", mw)
    config_action.triggered.connect(show_config)
    mw.form.menuTools.addAction(config_action)


def _on_import() -> None:
    from . import importer
    importer.run_import()
