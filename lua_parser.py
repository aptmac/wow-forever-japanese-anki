"""
lua_parser.py – Parse WoW SavedVariables Lua files into Python dicts.

WoW writes SavedVariables as a Lua assignment:  WFJ_Words = { ... }
This parser handles the subset of Lua used by WoW's serialiser:
  - string literals (double-quoted, with backslash escapes)
  - number literals (integer and float, including negative)
  - boolean literals (true / false)
  - nil
  - table constructors with [key] = value and sequential entries
  - single-line and block comments

It does NOT handle the full Lua grammar — only what WoW generates.
"""

from __future__ import annotations

import re
from typing import Any

# ── Tokeniser ────────────────────────────────────────────────────────────────

_TOKENS = re.compile(
    r"""
    (?P<comment>   --\[\[.*?\]\]  |  --[^\n]* )       |  # block / line comment
    (?P<string>    "(?:[^"\\]|\\.)*"                   |  # double-quoted string
                   '(?:[^'\\]|\\.)*'                   |  # single-quoted string
                   \[\[.*?\]\]       )                 |  # long string
    (?P<number>    -?0[xX][0-9a-fA-F]+                 |  # hex
                   -?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?   )|  # decimal
    (?P<bool>      \btrue\b | \bfalse\b               )|  # boolean
    (?P<nil>       \bnil\b                            )|  # nil
    (?P<ident>     [A-Za-z_]\w*                       )|  # identifier
    (?P<punct>     [={}\[\],;]                        )|  # punctuation
    (?P<ws>        \s+                                )   # whitespace
    """,
    re.VERBOSE | re.DOTALL,
)

_ESCAPES = {
    "\\\\": "\\",
    '\\"': '"',
    "\\'": "'",
    "\\n": "\n",
    "\\t": "\t",
    "\\r": "\r",
    "\\a": "\a",
    "\\b": "\b",
    "\\f": "\f",
    "\\0": "\0",
}


def _unescape(s: str) -> str:
    """Unescape a Lua string literal (strip outer quotes first)."""
    if s.startswith("[[") and s.endswith("]]"):
        return s[2:-2]
    s = s[1:-1]  # strip quotes
    for esc, ch in _ESCAPES.items():
        s = s.replace(esc, ch)
    # numeric escapes: \ddd
    s = re.sub(r"\\(\d{1,3})", lambda m: chr(int(m.group(1))), s)
    return s


class _Lexer:
    """Lazy token stream over Lua source."""

    def __init__(self, text: str) -> None:
        self._tokens = [
            m
            for m in _TOKENS.finditer(text)
            if m.lastgroup not in ("ws", "comment")
        ]
        self._pos = 0

    def peek(self) -> tuple[str, str] | None:
        if self._pos >= len(self._tokens):
            return None
        m = self._tokens[self._pos]
        return (m.lastgroup, m.group())  # type: ignore[return-value]

    def advance(self) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of input")
        self._pos += 1
        return tok

    def expect(self, kind: str, value: str | None = None) -> str:
        tok = self.advance()
        if tok[0] != kind or (value is not None and tok[1] != value):
            raise ValueError(f"expected ({kind}, {value!r}), got {tok}")
        return tok[1]


# ── Parser ───────────────────────────────────────────────────────────────────


def _parse_value(lex: _Lexer) -> Any:
    tok = lex.peek()
    if tok is None:
        raise ValueError("unexpected end of input while expecting a value")
    kind, raw = tok

    if kind == "string":
        lex.advance()
        return _unescape(raw)
    if kind == "number":
        lex.advance()
        if "." in raw or "e" in raw.lower() and "x" not in raw.lower():
            return float(raw)
        return int(raw, 0)
    if kind == "bool":
        lex.advance()
        return raw == "true"
    if kind == "nil":
        lex.advance()
        return None
    if kind == "punct" and raw == "{":
        return _parse_table(lex)
    # a bare identifier used as value (shouldn't happen in SV files)
    if kind == "ident":
        lex.advance()
        return raw

    raise ValueError(f"unexpected token: {tok}")


def _parse_table(lex: _Lexer) -> dict | list:
    """Parse a Lua table constructor.

    Returns a dict when the table has explicit keys, or a list when it's
    purely sequential.  Mixed tables get dict keys ``1, 2, ...`` for the
    sequential part.
    """
    lex.expect("punct", "{")
    result: dict[Any, Any] = {}
    seq_index = 1  # Lua arrays are 1-based
    has_explicit_key = False

    while True:
        tok = lex.peek()
        if tok is None:
            raise ValueError("unterminated table")
        if tok == ("punct", "}"):
            lex.advance()
            break

        # [key] = value
        if tok == ("punct", "["):
            lex.advance()
            key = _parse_value(lex)
            lex.expect("punct", "]")
            lex.expect("punct", "=")
            value = _parse_value(lex)
            result[key] = value
            has_explicit_key = True
        else:
            # could be  ident = value  or  just value
            tok2_kind, tok2_raw = tok
            if tok2_kind == "ident":
                lex.advance()
                nxt = lex.peek()
                if nxt and nxt == ("punct", "="):
                    lex.advance()
                    value = _parse_value(lex)
                    result[tok2_raw] = value
                    has_explicit_key = True
                else:
                    # it was a bare value (put the identifier back as a value)
                    # Actually we already consumed it; treat the ident as a value
                    result[seq_index] = tok2_raw
                    seq_index += 1
            else:
                value = _parse_value(lex)
                result[seq_index] = value
                seq_index += 1

        # skip optional comma / semicolon
        tok = lex.peek()
        if tok and tok[0] == "punct" and tok[1] in (",", ";"):
            lex.advance()

    # If purely sequential (keys 1..n), return a list
    if not has_explicit_key and all(isinstance(k, int) for k in result):
        return [result[i] for i in sorted(result)]
    return result


# ── Public API ───────────────────────────────────────────────────────────────


def parse_saved_variables(text: str) -> dict[str, Any]:
    """Parse a WoW SavedVariables file.

    Returns a dict mapping each top-level variable name to its value.

    Example::

        data = parse_saved_variables(Path("WFJ_Words.lua").read_text("utf-8"))
        entries = data["WFJ_Words"]["entries"]
    """
    lex = _Lexer(text)
    result: dict[str, Any] = {}

    while lex.peek() is not None:
        name = lex.expect("ident")
        lex.expect("punct", "=")
        value = _parse_value(lex)
        result[name] = value

    return result
