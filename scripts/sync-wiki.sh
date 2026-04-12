#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_REPO="git@github.com:tim-oe/SonicModBus.wiki.git"
WIKI_DIR="${REPO_ROOT}/.wiki"
DOCS_SRC="${REPO_ROOT}/docs"
MD_OUT="${DOCS_SRC}/_build/markdown"

echo "==> Building Sphinx markdown (sphinx-markdown-builder)..."
cd "${DOCS_SRC}"
poetry run sphinx-build -M markdown . _build -a

if [ ! -d "${MD_OUT}" ] || [ -z "$(ls -A "${MD_OUT}" 2>/dev/null)" ]; then
    echo "    No output in ${MD_OUT} — is sphinx_markdown_builder in docs/conf.py?"
    exit 1
fi

# Builder can collapse ```python`` fences; source is canonical.
cp "${DOCS_SRC}/getting-started.md" "${MD_OUT}/getting-started.md"

echo "==> Cloning wiki repo..."
rm -rf "${WIKI_DIR}"
git clone "${WIKI_REPO}" "${WIKI_DIR}" 2>/dev/null || {
    echo "    Wiki repo not found — create a page on GitHub first: https://github.com/tim-oe/SonicModBus/wiki"
    exit 1
}

echo "==> Syncing markdown into wiki clone..."
find "${WIKI_DIR}" -mindepth 1 -maxdepth 1 ! -name ".git" -exec rm -rf {} +
cp -a "${MD_OUT}/." "${WIKI_DIR}/"
if [ -f "${WIKI_DIR}/index.md" ]; then
    mv "${WIKI_DIR}/index.md" "${WIKI_DIR}/Home.md"
fi

echo "==> Expanding flattened Args/Raises (sphinx-markdown-builder quirk)..."
poetry run python "${REPO_ROOT}/scripts/wiki_postprocess.py" "${WIKI_DIR}"

echo "==> Fixing wiki links + sidebar..."
cd "${REPO_ROOT}"
poetry run python - "$WIKI_DIR" <<'PY'
"""GitHub wiki URLs use leaf slugs only; Sphinx emits path-like URLs under markdown_http_base."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def wiki_base() -> str:
    return os.environ.get(
        "SONICMODBUS_WIKI_BASE", "https://github.com/tim-oe/SonicModBus/wiki"
    ).rstrip("/")


def flatten_github_wiki_links(text: str, base: str) -> str:
    def repl(m: re.Match[str]) -> str:
        tail = m.group(1)
        if tail.startswith("#") or not tail.strip("/"):
            return m.group(0)
        if "#" in tail:
            path, frag = tail.split("#", 1)
            leaf = path.strip("/").split("/")[-1]
            return f"{base}/{leaf}#{frag}" if leaf else m.group(0)
        leaf = tail.strip("/").split("/")[-1]
        return f"{base}/{leaf}"

    return re.sub(re.escape(base) + r"(/[^)\s]*)", repl, text)


def write_sidebar(wiki_root: Path) -> None:
    b = wiki_base()
    lines = [
        "**Documentation**",
        "",
        f"* [Home]({b}/Home)",
        f"* [Getting started]({b}/getting-started)",
        f"* [API overview]({b}/api)",
        f"* [Publishing]({b}/publishing)",
        "",
        "**API — module index**",
        "",
        f"* [Module index]({b}/index)",
        "",
        "**API — modules**",
        "",
    ]
    apidocs = wiki_root / "apidocs"
    if apidocs.is_dir():
        for p in sorted(apidocs.rglob("*.md")):
            rel = p.relative_to(wiki_root).with_suffix("")
            if rel.as_posix() == "apidocs/index":
                continue
            name = rel.name
            lines.append(f"* [{name}]({b}/{name})")
        lines.append("")
    (wiki_root / "_Sidebar.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    wiki_root = Path(sys.argv[1]).resolve()
    base = wiki_base()
    write_sidebar(wiki_root)
    for path in sorted(wiki_root.rglob("*.md")):
        if path.name == "_Sidebar.md":
            continue
        text = path.read_text(encoding="utf-8")
        fixed = flatten_github_wiki_links(text, base)
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")


if __name__ == "__main__":
    main()
PY

echo "==> Pushing to wiki..."
cd "${WIKI_DIR}"
git add -A
if git diff --cached --quiet; then
    echo "    No changes to push (wiki already matches this build)."
else
    git commit -m "sync docs from main repo"
    default_branch="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)"
    if [ -n "${default_branch}" ]; then
        git push origin "HEAD:${default_branch}"
    else
        git push origin HEAD:master 2>/dev/null || git push origin HEAD:main
    fi
    echo "    Wiki updated."
fi

rm -rf "${WIKI_DIR}"
echo "==> Done."
