"""
note_type.py – The Anki note type (model) for WoW Forever Japanese cards.

Card format:
  Front:
    - Word with furigana rendered above kanji (BIZ UDGothic 48px)
    - Mined sentence underneath with target word highlighted (BIZ UDGothic 24px)

  Back:
    - Front content ({{FrontSide}})
    - Answer (<hr id=answer> then English meaning in gold)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import anki.models  # noqa: F401
from anki.models import NotetypeDict
from aqt import mw

MODEL_NAME = "WoW Forever Japanese"

FIELDS = [
    "Key",             # unique key from the WoW addon (kind:id:word)
    "Reading",         # target word with ruby furigana: <ruby>用心<rt>ようじん</rt></ruby>
    "Sentence",        # mined sentence from WoW with word highlighted in bold
    "Back",            # answer / English translation
    "Meaning",         # alias for Back
    "Kanji",           # bare word (Kanji)
    "Word",            # alias for Kanji
    "DictionaryForm",  # lemma / dictionary form
    "Source",          # where the word came from: quest, gossip, etc.
    "QuestTitle",      # quest title in Japanese (if from a quest)
    "SavedDate",       # when the word was saved (YYYY-MM-DD HH:MM)
]

_SHARED_CSS = """\
.card {
    font-family: arial, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #ffffff;
    background-color: #2d2d2d;
    padding: 24px;
}

b {
    color: #ffd700;
}

ruby rt {
    font-size: 0.5em;
    color: #cccccc;
}

hr#answer {
    border: none;
    border-top: 1px solid #555555;
    margin: 20px 0;
}
"""

_FRONT = """\
<div style='font-family: "BIZ UDGothic", sans-serif; font-size: 48px;'>{{Reading}}</div>

<br>

<div style='font-family: "BIZ UDGothic", sans-serif; font-size: 24px;'>{{Sentence}}</div>
"""

_BACK = """\
{{FrontSide}}

<hr id=answer>

<div style='font-size: 24px; color: #ffd700; margin-top: 16px;'>{{Back}}</div>
{{#QuestTitle}}<div style='font-size: 16px; color: #888888; margin-top: 14px;'>📜 {{QuestTitle}}</div>{{/QuestTitle}}
"""


def get_or_create_model() -> NotetypeDict:
    """Return the WoW Forever Japanese note type, creating or updating it."""
    assert mw is not None
    col = mw.col
    assert col is not None

    model = col.models.by_name(MODEL_NAME)
    if model is not None:
        # Ensure all fields exist
        existing_names = {f["name"] for f in model["flds"]}
        for field_name in FIELDS:
            if field_name not in existing_names:
                field = col.models.new_field(field_name)
                col.models.add_field(model, field)

        # Update styling & templates
        model["css"] = _SHARED_CSS
        if model["tmpls"]:
            model["tmpls"][0]["name"] = "Recognition"
            model["tmpls"][0]["qfmt"] = _FRONT
            model["tmpls"][0]["afmt"] = _BACK

        if hasattr(col.models, "save"):
            col.models.save(model)
        elif hasattr(col.models, "update_dict"):
            col.models.update_dict(model)

        return model

    # Create new model
    model = col.models.new(MODEL_NAME)
    for field_name in FIELDS:
        field = col.models.new_field(field_name)
        col.models.add_field(model, field)

    tmpl = col.models.new_template("Recognition")
    tmpl["qfmt"] = _FRONT
    tmpl["afmt"] = _BACK
    col.models.add_template(model, tmpl)

    model["css"] = _SHARED_CSS
    model["sortf"] = 0  # Sort by Key

    if hasattr(col.models, "save"):
        col.models.save(model)
    elif hasattr(col.models, "add_dict"):
        col.models.add_dict(model)

    return model


def model_id() -> int | None:
    """Return the model ID if it exists, else None."""
    assert mw is not None and mw.col is not None
    model = mw.col.models.by_name(MODEL_NAME)
    return model["id"] if model else None
