"""
importer.py – Import WFJ_Words entries into Anki as notes.

Reads the WoWForeverJapanese.lua SavedVariables file, compares with existing notes
(by the Key field to avoid duplicates), creates new notes, and refreshes existing ones.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from aqt import mw
from aqt.utils import showInfo, showWarning, tooltip

from . import gui, lua_parser, note_type


def make_ruby(word: str, reading: str) -> str:
    """Format word and reading into HTML ruby tags: <ruby>漢字<rt>かんじ</rt></ruby>.

    Renders furigana cleanly above kanji across all Anki templates and devices:
      - 用心, ようじん  -> <ruby>用心<rt>ようじん</rt></ruby>
      - 食べる, たべる  -> <ruby>食<rt>た</rt></ruby>べる
      - お菓子, おかし  -> お<ruby>菓子<rt>かし</rt></ruby>
    """
    if not reading or reading == word:
        return word

    # If the word contains no kanji, no furigana needed
    if not any("\u4e00" <= c <= "\u9fff" for c in word):
        return word

    # Match common prefix kana
    prefix_len = 0
    while (
        prefix_len < len(word)
        and prefix_len < len(reading)
        and word[prefix_len] == reading[prefix_len]
    ):
        prefix_len += 1

    prefix = word[:prefix_len]
    w_rem = word[prefix_len:]
    r_rem = reading[prefix_len:]

    # Match common suffix kana
    suffix_len = 0
    while (
        suffix_len < len(w_rem)
        and suffix_len < len(r_rem)
        and w_rem[-1 - suffix_len] == r_rem[-1 - suffix_len]
    ):
        suffix_len += 1

    if suffix_len > 0:
        suffix = w_rem[len(w_rem) - suffix_len :]
        w_mid = w_rem[: len(w_rem) - suffix_len]
        r_mid = r_rem[: len(r_rem) - suffix_len]
    else:
        suffix = ""
        w_mid = w_rem
        r_mid = r_rem

    if w_mid and r_mid:
        return f"{prefix}<ruby>{w_mid}<rt>{r_mid}</rt></ruby>{suffix}"
    return f"<ruby>{word}<rt>{reading}</rt></ruby>"


def _get_saved_variables_path() -> Path | None:
    """Return the configured SavedVariables path, or None if not set or missing."""
    assert mw is not None
    config = mw.addonManager.getConfig(gui.pkg_name())
    raw_path = (config or {}).get("saved_variables_path", "").strip()
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_file():
        return p
    return None


def _get_target_deck_id() -> int:
    """Return the deck ID for the configured deck, creating it if needed."""
    assert mw is not None and mw.col is not None
    config = mw.addonManager.getConfig(gui.pkg_name())
    deck_name = (config or {}).get("deck_name", "WoW Forever Japanese")
    if not deck_name:
        deck_name = "WoW Forever Japanese"

    deck = mw.col.decks.by_name(deck_name)
    if deck:
        return deck["id"]

    return mw.col.decks.id(deck_name)


def _existing_notes() -> dict[str, Any]:
    """Return a mapping of Key -> note for existing notes of this model."""
    assert mw is not None and mw.col is not None
    mid = note_type.model_id()
    if mid is None:
        return {}

    notes_by_key: dict[str, Any] = {}
    note_ids = mw.col.models.nids(mid)
    for nid in note_ids:
        note = mw.col.get_note(nid)
        key_val = ""
        if "Key" in note:
            key_val = note["Key"]
        elif note.fields:
            key_val = note.fields[0]
        if key_val:
            notes_by_key[key_val] = note
    return notes_by_key


def _clean(value: Any) -> str:
    """Convert a parsed Lua value to a clean string for an Anki field."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    s = str(value)
    return s.replace("\t", " ").replace("\r", "").replace("\n", " ")


def _format_date(epoch: Any) -> str:
    """Format an epoch timestamp as YYYY-MM-DD HH:MM."""
    if not isinstance(epoch, (int, float)):
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(epoch))
    except (OSError, ValueError):
        return ""


def _entry_to_fields(entry: dict) -> dict[str, str]:
    """Map a WFJ_Words entry to Anki note field values."""
    is_english = entry.get("lang") == "en"

    meaning = _clean(entry.get("meaning", ""))
    ja_sentence = _clean(entry.get("jaSentence", ""))
    if is_english and ja_sentence:
        meaning = f"{meaning}<br>{ja_sentence}"

    word = _clean(entry.get("word", ""))
    raw_reading = _clean(entry.get("reading", ""))
    lemma = _clean(entry.get("lemma", ""))

    if is_english:
        reading_field = word
    else:
        reading_field = make_ruby(word, raw_reading)

    sentence = _clean(entry.get("sentence", ""))
    saved_word = _clean(entry.get("word", ""))
    if saved_word and saved_word in sentence:
        sentence = sentence.replace(saved_word, f"<b>{saved_word}</b>", 1)

    return {
        "Key": _clean(entry.get("key", "")),
        "Reading": reading_field,
        "Sentence": sentence,
        "Back": meaning,
        "Meaning": meaning,
        "Kanji": word,
        "Word": word,
        "DictionaryForm": lemma,
        "Source": _clean(entry.get("source", "")),
        "QuestID": _clean(entry.get("questId", "")),
        "QuestTitle": _clean(entry.get("questTitle", "")),
        "SavedDate": _format_date(entry.get("saved")),
    }


def run_import() -> None:
    """Main import entry point. Called from the UI."""
    assert mw is not None and mw.col is not None

    sv_path = _get_saved_variables_path()
    if sv_path is None:
        showWarning(
            "SavedVariables file not configured or not found.\n\n"
            "Please link your WoWForeverJapanese.lua file:\n"
            "Tools → WoW Forever Japanese: Settings…\n\n"
            "It is located at:\n"
            "World of Warcraft\\<flavor>\\WTF\\Account\\<ACCOUNT>\\SavedVariables\\WoWForeverJapanese.lua"
        )
        gui.show_config()
        return

    # Read and parse
    try:
        text = sv_path.read_text("utf-8", errors="replace")
        data = lua_parser.parse_saved_variables(text)
    except Exception as e:
        showWarning(f"Error reading {sv_path}:\n{e}")
        return

    words_data = data.get("WFJ_Words")
    if not isinstance(words_data, dict):
        showWarning(
            f"WFJ_Words not found in {sv_path.name}.\n\n"
            "Make sure you have saved at least one word in-game and "
            "logged out (or typed /reload) so the file is saved to disk."
        )
        return

    entries = words_data.get("entries")
    if not isinstance(entries, (list, dict)):
        showInfo("No words found in the word bank. Save some words in-game first!")
        return

    # Normalise dict with numeric keys to list
    if isinstance(entries, dict):
        entries = [entries[k] for k in sorted(entries) if isinstance(entries[k], dict)]

    if not entries:
        showInfo("No words found in the word bank.")
        return

    # Get or create the note type and deck
    model = note_type.get_or_create_model()
    deck_id = _get_target_deck_id()

    # Find existing notes so we can either add new or refresh fields on existing
    existing_notes = _existing_notes()

    added = 0
    refreshed = 0
    errors = 0

    mw.col.decks.select(deck_id)

    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            continue

        key = _clean(raw_entry.get("key", ""))
        if not key:
            errors += 1
            continue

        fields = _entry_to_fields(raw_entry)

        if key in existing_notes:
            # Refresh fields if needed
            note = existing_notes[key]
            changed = False
            for field_name, value in fields.items():
                if field_name in note and note[field_name] != value:
                    note[field_name] = value
                    changed = True
            if changed:
                try:
                    if hasattr(mw.col, "update_note"):
                        mw.col.update_note(note)
                    refreshed += 1
                except Exception:
                    pass
            continue

        try:
            note = mw.col.new_note(model)
            for field_name, value in fields.items():
                if field_name in note:
                    note[field_name] = value

            note.note_type()
            mw.col.add_note(note, deck_id)
            added += 1
            existing_notes[key] = note
        except Exception:
            errors += 1

    # Report
    parts = []
    if added:
        parts.append(f"✅ {added} new card{'s' if added != 1 else ''} imported")
    if refreshed:
        parts.append(f"🔄 {refreshed} existing card{'s' if refreshed != 1 else ''} refreshed")
    if not added and not refreshed:
        parts.append(f"All cards are up to date ({len(existing_notes)} in deck).")
    if errors:
        parts.append(f"⚠️ {errors} error{'s' if errors != 1 else ''}")

    msg = "\n".join(parts)
    tooltip(msg, period=5000)
    mw.reset()
