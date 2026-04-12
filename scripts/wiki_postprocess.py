"""Post-process Sphinx markdown for GitHub wiki.

sphinx-markdown-builder emits Google/NumPy-style ``Args:`` / ``Raises:`` sections as
a single paragraph. This module re-expands them into bullet lists so the wiki is
readable (see sync-wiki.sh).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Parameter names in Google-style docstrings (snake_case).
_ARGS_BOUNDARY = re.compile(r" (?=[a-z_][a-z0-9_]*: )")
# Exception names (PascalCase + optional trailing colon boundary).
_RAISES_BOUNDARY = re.compile(r" (?=[A-Z][a-zA-Z0-9_]*: )")


def _split_name_description(parts: list[str]) -> list[tuple[str, str]] | None:
    out: list[tuple[str, str]] = []
    for raw in parts:
        chunk = raw.strip()
        if ":" not in chunk:
            return None
        idx = chunk.index(":")
        name, desc = chunk[:idx].strip(), chunk[idx + 1 :].strip()
        if not name:
            return None
        out.append((name, desc))
    return out if out else None


def _expand_field_line(
    line: str, header: str, pattern: re.Pattern[str]
) -> str | None:
    m = re.match(rf"^(\s*){re.escape(header)}:\s*(.+)$", line)
    if not m:
        return None
    indent, body = m.group(1), m.group(2)
    parts = pattern.split(body.strip())
    pairs = _split_name_description(parts)
    if pairs is None:
        return None
    lines = [f"{indent}{header}:", "", *[f"{indent}- **{n}**: {d}" for n, d in pairs]]
    return "\n".join(lines)


def fix_google_style_fields_line(line: str) -> str:
    """Expand one line if it is a flattened Args:/Raises: field line."""
    for header, pat in (("Args", _ARGS_BOUNDARY), ("Raises", _RAISES_BOUNDARY)):
        expanded = _expand_field_line(line, header, pat)
        if expanded is not None:
            return expanded
    return line


def fix_google_style_fields(text: str) -> str:
    """Expand flattened Args:/Raises: lines; skip fenced code blocks."""
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            out.append(fix_google_style_fields_line(line))
        else:
            out.append(line)
    return "\n".join(out)


def postprocess_wiki_tree(wiki_root: Path) -> None:
    for path in sorted(wiki_root.rglob("*.md")):
        if path.name == "_Sidebar.md":
            continue
        original = path.read_text(encoding="utf-8")
        fixed = fix_google_style_fields(original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: wiki_postprocess.py <wiki_root>", file=sys.stderr)
        sys.exit(2)
    postprocess_wiki_tree(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
