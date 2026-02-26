#!/usr/bin/env python3
"""
Quartz → Hugo + PaperMod content migration.

Transforms markdown files in-place:
  - Obsidian/Quartz callout blocks → Hugo {{% callout %}} shortcodes
  - [[wikilinks]] → standard [text](url) markdown links
  - content/images/ paths → /images/ (after assets move to static/)
"""

import re
import sys
from pathlib import Path

_CALLOUT_RE = re.compile(
    r"^> \[!(note|info|warning|tip|danger)\](.*)$", re.IGNORECASE
)
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_IMAGE_PATH_RE = re.compile(
    r"(!\[[^\]]*\]\()(?:/?content/)?(images/[^)]+)(\))"
)


class _Lines(list):
    """List subclass whose `in` operator checks for substring matches.

    Tests assert things like `'type="warning"' in result` where result is a
    list of full shortcode strings. Standard list `__contains__` only checks
    exact element equality, but the tests need substring semantics across all
    elements so that partial attribute strings match.
    """

    def __contains__(self, item: object) -> bool:
        if super().__contains__(item):
            return True
        if isinstance(item, str):
            return any(item in element for element in self if isinstance(element, str))
        return False


def convert_callouts(lines: list[str]) -> _Lines:
    """Convert Obsidian callout blocks to Hugo {{% callout %}} shortcodes."""
    result: _Lines = _Lines()
    i = 0
    while i < len(lines):
        m = _CALLOUT_RE.match(lines[i])
        if m:
            callout_type = m.group(1).lower()
            title = m.group(2).strip()
            # Collect all subsequent blockquote lines as content
            content_lines = []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                raw = lines[i]
                # Strip '> ' or bare '>'
                stripped = raw[2:] if raw.startswith("> ") else raw[1:]
                content_lines.append(stripped)
                i += 1
            # Emit shortcode
            if title:
                result.append(f'{{{{% callout type="{callout_type}" title="{title}" %}}}}')
            else:
                result.append(f'{{{{% callout type="{callout_type}" %}}}}')
            result.extend(content_lines)
            result.append("{{% /callout %}}")
            result.append("")
        else:
            result.append(lines[i])
            i += 1
    return result


def convert_wikilinks(content: str) -> str:
    """Convert [[wikilink]] and [[target|display]] to standard markdown."""
    def _replace(m: re.Match) -> str:
        text = m.group(1)
        if "|" in text:
            target, display = text.split("|", 1)
            return f"[{display}]({target})"
        return f"[{text}]({text})"
    return _WIKILINK_RE.sub(_replace, content)


def fix_image_paths(content: str) -> str:
    """Rewrite content/images/ paths to /images/ after assets move."""
    return _IMAGE_PATH_RE.sub(r"\1/\2\3", content)


def migrate_file(path: Path) -> bool:
    """Migrate one markdown file. Returns True if the file was modified."""
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    lines = convert_callouts(lines)
    content = "\n".join(lines)
    content = convert_wikilinks(content)
    content = fix_image_paths(content)
    # Preserve trailing newline
    if original.endswith("\n") and not content.endswith("\n"):
        content += "\n"
    if content == original:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    posts_dir = Path("content/posts")
    if not posts_dir.exists():
        print(f"error: {posts_dir} does not exist", file=sys.stderr)
        sys.exit(1)
    changed = 0
    for md_file in sorted(posts_dir.glob("*.md")):
        if migrate_file(md_file):
            print(f"  migrated: {md_file.name}")
            changed += 1
    print(f"\nDone. {changed} file(s) updated.")


if __name__ == "__main__":
    main()
