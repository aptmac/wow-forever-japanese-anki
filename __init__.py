# WoW Forever Japanese → Anki
#
# An Anki add-on that imports banked words from the WoW Forever Japanese addon
# into Anki as flashcards. Words are saved in-game via the word bank feature
# (Core/Words.lua) and stored as WoW SavedVariables. This add-on reads that
# Lua file and creates Anki notes with the word, reading, meaning, and example
# sentence from the game.
#
# Copyright (c) 2026 aptmac
# SPDX-License-Identifier: MIT

from . import main  # noqa: F401 – Anki discovers add-ons by importing __init__
