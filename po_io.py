# -*- coding: utf-8 -*-
"""Minimal .po (gettext) reader/writer utilities.

DRAT 1.5.2+ uses .po files instead of the old DRAT-style "XML".
Another-SDSE needs to load and save translations/comments from .po.

We implement a tiny subset of the PO format:
- msgctxt, msgid, msgstr
- translator comments (# ...)
- extracted comments (#. ...)

We intentionally rewrite the file deterministically (we don't try to preserve
all formatting). This is enough for DRAT/Poedit workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class PoEntry:
    msgctxt: str | None
    msgid: str
    msgstr: str
    translator_comments: list[str] = field(default_factory=list)
    extracted_comments: list[str] = field(default_factory=list)


def _unquote_po_string(s: str) -> str:
    """Decode a PO quoted string line: "..." with C-style escapes."""

    s = s.strip()
    if not (len(s) >= 2 and s[0] == '"' and s[-1] == '"'):
        raise ValueError(f"Invalid PO string literal: {s!r}")

    body = s[1:-1]

    # Interpret common PO escapes.
    out: list[str] = []
    i = 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue

        if i + 1 >= len(body):
            out.append("\\")
            i += 1
            continue

        n = body[i + 1]
        if n == "n":
            out.append("\n")
            i += 2
        elif n == "t":
            out.append("\t")
            i += 2
        elif n == "r":
            out.append("\r")
            i += 2
        elif n == '"':
            out.append('"')
            i += 2
        elif n == "\\":
            out.append("\\")
            i += 2
        else:
            # Unknown escape: keep literal char.
            out.append(n)
            i += 2

    return "".join(out)


def _quote_po_string(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
    return f'"{s}"'


def _read_multiline_value(lines: list[str], i: int) -> tuple[str, int]:
    """Read msgid/msgstr/msgctxt value starting at line i.

    Returns (value, next_index).
    """

    # First line contains key + value.
    parts = lines[i].split(None, 1)
    if len(parts) == 1:
        raise ValueError(f"Missing PO value at line {i + 1}: {lines[i]!r}")

    val = _unquote_po_string(parts[1])
    i += 1

    # Continuation lines are just quoted strings.
    while i < len(lines):
        s = lines[i].strip()
        if not s.startswith('"'):
            break
        val += _unquote_po_string(s)
        i += 1

    return val, i


def read_po(path: Path) -> list[PoEntry]:
    """Parse a .po file."""

    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    entries: list[PoEntry] = []

    # State for current entry.
    tc: list[str] = []
    ec: list[str] = []
    msgctxt: str | None = None
    msgid: str | None = None
    msgstr: str | None = None

    def flush():
        nonlocal tc, ec, msgctxt, msgid, msgstr
        if msgid is None and msgstr is None and msgctxt is None:
            tc = []
            ec = []
            return
        if msgid is None:
            raise ValueError(f"Invalid PO: missing msgid in {path}")
        if msgstr is None:
            msgstr = ""
        entries.append(
            PoEntry(
                msgctxt=msgctxt,
                msgid=msgid,
                msgstr=msgstr,
                translator_comments=tc,
                extracted_comments=ec,
            )
        )
        tc = []
        ec = []
        msgctxt = None
        msgid = None
        msgstr = None

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Blank line separates entries.
        if s == "":
            flush()
            i += 1
            continue

        if s.startswith("#."):
            ec.append(s[2:].lstrip())
            i += 1
            continue

        if s.startswith("#"):
            # translator comment (includes '# ')
            tc.append(s[1:].lstrip())
            i += 1
            continue

        if s.startswith("msgctxt"):
            msgctxt, i = _read_multiline_value(lines, i)
            continue

        if s.startswith("msgid"):
            msgid, i = _read_multiline_value(lines, i)
            continue

        if s.startswith("msgstr"):
            msgstr, i = _read_multiline_value(lines, i)
            continue

        # Unknown line: ignore but keep parsing.
        i += 1

    flush()

    # Drop header entry (msgid == "") if present.
    if entries and entries[0].msgid == "":
        return entries[1:]

    return entries


def write_po(path: Path, entries: Iterable[PoEntry]) -> None:
    """Write entries to a .po file (UTF-8)."""

    out: list[str] = []

    # Minimal header for PO tools.
    out.append('msgid ""')
    out.append('msgstr ""')
    out.append('"Content-Type: text/plain; charset=UTF-8\\n"')
    out.append('"Content-Transfer-Encoding: 8bit\\n"')
    out.append('')

    for e in entries:
        for c in e.extracted_comments:
            out.append(f"#. {c}" if c else "#.")
        for c in e.translator_comments:
            out.append(f"# {c}" if c else "#")

        if e.msgctxt is not None:
            out.append(f"msgctxt {_quote_po_string(e.msgctxt)}")

        out.append(f"msgid {_quote_po_string(e.msgid)}")
        out.append(f"msgstr {_quote_po_string(e.msgstr or '')}")
        out.append("")

    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def parse_context_speaker(ctx: str | None) -> tuple[str | None, str | None]:
    """Return (index, speaker) from DRAT context like '0001 | MAKOTO'."""

    if not ctx:
        return None, None
    if "|" not in ctx:
        return ctx.strip(), None
    a, b = ctx.split("|", 1)
    return a.strip(), b.strip() or None


def update_po_file(path: Path, *, translated: list[str] | None = None, comment: list[str] | None = None) -> None:
    """Update msgstr and/or translator comments from SDSE in-memory lists.

    `translated` / `comment` are lists of strings in SDSE format: '\n...\n'.
    """

    entries = read_po(path)

    if translated is not None and len(translated) != len(entries):
        raise ValueError(f"Translated line count mismatch for {path}: {len(translated)} != {len(entries)}")
    if comment is not None and len(comment) != len(entries):
        raise ValueError(f"Comment line count mismatch for {path}: {len(comment)} != {len(entries)}")

    new_entries: list[PoEntry] = []
    for i, e in enumerate(entries):
        msgstr = e.msgstr
        tc = list(e.translator_comments)

        if translated is not None:
            # SDSE stores as '\ntext\n'
            msgstr = translated[i].strip("\n").strip()

        if comment is not None:
            c = comment[i].strip("\n")
            # keep empty comments as no comment lines
            c = c.strip()
            tc = [c] if c else []

        new_entries.append(
            PoEntry(
                msgctxt=e.msgctxt,
                msgid=e.msgid,
                msgstr=msgstr,
                translator_comments=tc,
                extracted_comments=list(e.extracted_comments),
            )
        )

    write_po(path, new_entries)
