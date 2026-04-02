#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_REPO="git@github.com:tim-oe/SonicModBus.wiki.git"
WIKI_DIR="${REPO_ROOT}/.wiki"
DOCS_SRC="${REPO_ROOT}/docs"

echo "==> Building Sphinx docs..."
cd "${DOCS_SRC}"
poetry run sphinx-build -M markdown . _build 2>/dev/null || {
    echo "    (markdown builder not available, copying source .md files directly)"
}

echo "==> Cloning wiki repo..."
rm -rf "${WIKI_DIR}"
git clone "${WIKI_REPO}" "${WIKI_DIR}" 2>/dev/null || {
    echo "    Wiki repo not found — initialize it by creating a page on GitHub first."
    echo "    https://github.com/tim-oe/SonicModBus/wiki"
    exit 1
}

echo "==> Syncing markdown files to wiki..."
# Copy source markdown files (these are already GitHub-wiki-compatible MyST markdown)
for md_file in "${DOCS_SRC}"/*.md; do
    [ -f "${md_file}" ] || continue
    base="$(basename "${md_file}")"

    # index.md becomes Home.md for GitHub wiki
    if [ "${base}" = "index.md" ]; then
        dest="${WIKI_DIR}/Home.md"
    else
        dest="${WIKI_DIR}/${base}"
    fi

    # Strip MyST toctree directives (not supported by GitHub wiki)
    sed '/^```{toctree}/,/^```$/d' "${md_file}" > "${dest}"
    echo "    ${base} -> $(basename "${dest}")"
done

echo "==> Pushing to wiki..."
cd "${WIKI_DIR}"
git add -A
if git diff --cached --quiet; then
    echo "    No changes to push."
else
    git commit -m "sync docs from main repo"
    git push origin master
    echo "    Wiki updated."
fi

rm -rf "${WIKI_DIR}"
echo "==> Done."
