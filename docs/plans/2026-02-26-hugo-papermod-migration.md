# Hugo + PaperMod Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Quartz v4 site with Hugo + PaperMod, preserving all content and features, working in an isolated git worktree.

**Architecture:** Hugo static site with PaperMod as a git submodule. Content migrated from flat `content/` into `content/posts/`. A Python script handles in-place content transformations (callout syntax, wikilinks, image paths). A custom Giscus partial and callout shortcode replace Quartz-specific features. GitHub Actions replaces the Quartz deploy workflow.

**Tech Stack:** Hugo (latest, extended), PaperMod theme (git submodule), Python 3 + pytest (migration script only), GitHub Actions + GitHub Pages

---

### Task 1: Create git worktree

**Step 1: Use the worktree skill**

Invoke the `superpowers:using-git-worktrees` skill to create a worktree on a new branch `hugo-migration`. All subsequent tasks work in that worktree directory.

---

### Task 2: Remove Quartz git upstream

All work in this task runs from the worktree directory.

**Step 1: Remove the upstream remote**

```bash
git remote remove upstream
```

Expected: no output (success).

**Step 2: Verify**

```bash
git remote -v
```

Expected: only `origin` remains.

**Step 3: Commit the removal**

There are no files to stage — remote config lives in `.git/config` only. No commit needed here; proceed to task 3.

---

### Task 3: Remove all Quartz-specific workflow files

**Files to delete:**
- `.github/workflows/ci.yaml`
- `.github/workflows/build-preview.yaml`
- `.github/workflows/deploy-preview.yaml`
- `.github/workflows/docker-build-push.yaml`
- `.github/workflows/deploy.yml` ← the active Quartz deploy workflow

**Step 1: Delete them**

```bash
git rm .github/workflows/ci.yaml \
       .github/workflows/build-preview.yaml \
       .github/workflows/deploy-preview.yaml \
       .github/workflows/docker-build-push.yaml \
       .github/workflows/deploy.yml
```

**Step 2: Commit**

```bash
git commit -m "chore: remove Quartz CI/CD workflows"
```

---

### Task 4: Initialize Hugo site structure

**Step 1: Check Hugo is installed**

```bash
hugo version
```

If not installed: `sudo apt install hugo` or download from https://github.com/gohugoio/hugo/releases (get the **extended** variant — needed for Sass processing).

**Step 2: Initialize Hugo in the worktree root**

```bash
hugo new site . --format yaml --force
```

`--format yaml` creates `hugo.yaml` instead of `hugo.toml`.
`--force` allows init in a non-empty directory.

This creates: `archetypes/`, `assets/`, `layouts/`, `static/`, `themes/`, `hugo.yaml`.
Existing `content/` is untouched.

**Step 3: Add PaperMod as a git submodule**

```bash
git submodule add --depth=1 \
  https://github.com/adityatelange/hugo-PaperMod.git \
  themes/PaperMod
git submodule update --init --recursive
```

**Step 4: Commit**

```bash
git add .
git commit -m "feat: initialize Hugo site with PaperMod theme"
```

---

### Task 5: Move content files into Hugo structure

**Goal:** Move all blog post `.md` files into `content/posts/`, rename `content/index.md` to `content/about.md`, and move image/asset directories to `static/`.

**Step 1: Create the posts directory**

```bash
mkdir -p content/posts
```

**Step 2: Move all blog posts (everything except index.md)**

```bash
for f in content/*.md; do
  name=$(basename "$f")
  if [ "$name" != "index.md" ]; then
    git mv "$f" "content/posts/$name"
  fi
done
```

**Step 3: Rename index.md to about.md**

```bash
git mv content/index.md content/about.md
```

**Step 4: Move image and asset directories to static/**

```bash
git mv content/images static/images
git mv content/assets static/assets
```

**Step 5: Commit**

```bash
git commit -m "chore: reorganize content into Hugo directory structure"
```

---

### Task 6: Write migration script tests (TDD)

The migration script transforms file content in-place. Write tests before the script.

**Files:**
- Create: `scripts/test_migrate.py`
- Create: `scripts/migrate.py` (empty stub — tests must fail first)

**Step 1: Create the stub**

```bash
mkdir -p scripts
touch scripts/migrate.py
```

**Step 2: Write the tests**

Create `scripts/test_migrate.py`:

```python
"""Tests for the Quartz → Hugo content migration script."""
import pytest
from migrate import convert_callouts, convert_wikilinks, fix_image_paths


# ── Callout conversion ────────────────────────────────────────────────────────

def test_callout_note_no_title():
    lines = [
        "> [!note]",
        "> This is note content.",
        "",
        "Normal paragraph.",
    ]
    result = convert_callouts(lines)
    assert '{{% callout type="note" %}}' in result
    assert "This is note content." in result
    assert "{{% /callout %}}" in result
    assert "Normal paragraph." in result

def test_callout_note_with_title():
    lines = [
        "> [!note] Written with AI",
        "> This post was built with Claude Code.",
    ]
    result = convert_callouts(lines)
    assert '{{% callout type="note" title="Written with AI" %}}' in result
    assert "This post was built with Claude Code." in result
    assert "{{% /callout %}}" in result

def test_callout_info_with_title():
    lines = [
        "> [!info] An aside on the architecture.",
        "> Some info content.",
    ]
    result = convert_callouts(lines)
    assert 'type="info"' in result
    assert 'title="An aside on the architecture."' in result

def test_callout_warning():
    lines = ["> [!warning]", "> Be careful here."]
    result = convert_callouts(lines)
    assert 'type="warning"' in result

def test_callout_tip():
    lines = ["> [!tip]", "> Use this shortcut."]
    result = convert_callouts(lines)
    assert 'type="tip"' in result

def test_callout_multiline_content():
    lines = [
        "> [!note]",
        "> Line one.",
        "> Line two.",
        "> Line three.",
        "",
    ]
    result = convert_callouts(lines)
    assert "Line one." in result
    assert "Line two." in result
    assert "Line three." in result
    # Content lines should not retain the '> ' prefix
    assert all(not l.startswith("> ") for l in result)

def test_non_callout_blockquote_unchanged():
    lines = ["> This is a plain blockquote.", "> Not a callout."]
    result = convert_callouts(lines)
    assert result == lines

def test_multiple_callouts_in_file():
    lines = [
        "> [!note]",
        "> First callout.",
        "",
        "Some text.",
        "",
        "> [!info] Title",
        "> Second callout.",
    ]
    result = convert_callouts(lines)
    result_str = "\n".join(result)
    assert result_str.count("{{% callout") == 2
    assert result_str.count("{{% /callout %}}") == 2

def test_callout_type_is_lowercased():
    lines = ["> [!NOTE]", "> Content."]
    result = convert_callouts(lines)
    assert 'type="note"' in result


# ── Wikilink conversion ───────────────────────────────────────────────────────

def test_wikilink_simple():
    result = convert_wikilinks("See [[language]] for details.")
    assert result == "See [language](language) for details."

def test_wikilink_aliased():
    result = convert_wikilinks("See [[target|display text]] here.")
    assert result == "See [display text](target) here."

def test_wikilink_multiple():
    result = convert_wikilinks("[[one]] and [[two]].")
    assert "[one](one)" in result
    assert "[two](two)" in result

def test_no_wikilinks_unchanged():
    content = "Normal [markdown link](https://example.com) here."
    assert convert_wikilinks(content) == content


# ── Image path conversion ─────────────────────────────────────────────────────

def test_image_path_with_content_prefix():
    result = fix_image_paths("![alt](content/images/foo.png)")
    assert result == "![alt](/images/foo.png)"

def test_image_path_already_correct():
    result = fix_image_paths("![alt](/images/foo.png)")
    assert result == "![alt](/images/foo.png)"

def test_image_path_with_slash_prefix():
    result = fix_image_paths("![alt](/content/images/foo.png)")
    assert result == "![alt](/images/foo.png)"

def test_non_image_links_unchanged():
    content = "[link text](https://example.com)"
    assert fix_image_paths(content) == content
```

**Step 3: Run tests to confirm they all fail**

```bash
cd scripts && python -m pytest test_migrate.py -v 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError` — `migrate` module doesn't exist yet.

---

### Task 7: Write migration script

**File:** `scripts/migrate.py`

**Step 1: Write the implementation**

```python
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


def convert_callouts(lines: list[str]) -> list[str]:
    """Convert Obsidian callout blocks to Hugo {{% callout %}} shortcodes."""
    result = []
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
                result.append(f'{{{{%callout type="{callout_type}" title="{title}" %}}}}')
            else:
                result.append(f'{{{{%callout type="{callout_type}" %}}}}')
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
```

**Step 2: Run tests to confirm they pass**

```bash
cd scripts && python -m pytest test_migrate.py -v
```

Expected: all tests PASS.

**Step 3: Commit**

```bash
git add scripts/
git commit -m "feat: add content migration script with tests"
```

---

### Task 8: Run migration script on content

**Step 1: Run the script from the repo root**

```bash
python scripts/migrate.py
```

Expected: output listing each modified file, e.g.:
```
  migrated: A-take-on-Pin-in-Rust.md
  migrated: Java-stream-gatherer-interface.md
  ...
Done. N file(s) updated.
```

**Step 2: Sanity check a few files**

```bash
grep -l "callout" content/posts/*.md | head -3
```

Open one of those files and confirm the `{{% callout %}}` shortcode is present and the `> [!note]` syntax is gone.

**Step 3: Commit**

```bash
git add content/posts/
git commit -m "chore: apply content migration (callouts, wikilinks, image paths)"
```

---

### Task 9: Write `hugo.yaml`

**File:** `hugo.yaml` (replace the stub created by `hugo new site`)

```yaml
baseURL: https://kidoni.dev/
title: kidoni.dev
theme: PaperMod
languageCode: en-US
paginate: 10
enableRobotsTxt: true
buildDrafts: false

outputs:
  home:
    - HTML
    - RSS
    - JSON  # required for PaperMod Fuse.js search

minify:
  disableXML: true
  minifyOutput: true

params:
  env: production
  title: kidoni.dev
  description: Software development blog covering Rust, Java, and systems programming.
  author: Ray Suliteanu

  defaultTheme: auto       # follows OS light/dark preference
  disableThemeToggle: false

  ShowReadingTime: true
  ShowShareButtons: true
  ShowPostNavLinks: true
  ShowBreadCrumbs: true
  ShowCodeCopyButtons: true
  ShowRssButtonInSectionTermList: true
  UseHugoToc: true
  comments: true
  showtoc: true
  tocopen: false

  homeInfoParams:
    Title: kidoni.dev
    Content: Software development blog covering Rust, Java, and systems programming.

  socialIcons:
    - name: github
      url: https://github.com/raysuliteanu

  fuseOpts:
    isCaseSensitive: false
    shouldSort: true
    location: 0
    distance: 1000
    threshold: 0.4
    minMatchCharLength: 0
    limit: 10
    keys:
      - title
      - permalink
      - summary
      - content

menu:
  main:
    - identifier: about
      name: About
      url: /about/
      weight: 10
    - identifier: search
      name: Search
      url: /search/
      weight: 20
    - identifier: tags
      name: Tags
      url: /tags/
      weight: 30
    - identifier: archives
      name: Archives
      url: /archives/
      weight: 40

markup:
  highlight:
    noClasses: false
    anchorLineNos: false
    codeFences: true
    guessSyntax: true
    lineNos: false
    style: monokai

services:
  googleAnalytics:
    ID: G-X783PXP90Q
```

**Commit:**

```bash
git add hugo.yaml
git commit -m "feat: add Hugo site configuration"
```

---

### Task 10: Create standalone pages

These are non-blog pages placed at the root of `content/` so Hugo never includes them in the posts list.

**Step 1: Update `content/about.md` frontmatter**

Open `content/about.md`. The current frontmatter is:

```yaml
---
title: Welcome to kidoni.dev
date: 2025-02-01
---
```

Update it to:

```yaml
---
title: About
---
```

Remove `date` (unnecessary for a static page) and update the title.

**Step 2: Create `content/search.md`**

```markdown
---
title: Search
layout: search
---
```

**Step 3: Create `content/archives.md`**

```markdown
---
title: Archives
layout: archives
---
```

**Step 4: Commit**

```bash
git add content/about.md content/search.md content/archives.md
git commit -m "feat: add about, search, and archives pages"
```

---

### Task 11: Create Giscus comments partial

**File:** `layouts/partials/comments.html`

```bash
mkdir -p layouts/partials
```

```html
<script src="https://giscus.app/client.js"
  data-repo="kidonisoftware/kidoni"
  data-repo-id="R_kgDONduRGw"
  data-category="Announcements"
  data-category-id="DIC_kwDONduRG84ClO6M"
  data-mapping="pathname"
  data-strict="0"
  data-reactions-enabled="1"
  data-emit-metadata="0"
  data-input-position="top"
  data-theme="preferred_color_scheme"
  data-lang="en"
  crossorigin="anonymous"
  async>
</script>
```

`data-theme="preferred_color_scheme"` means Giscus automatically follows the user's light/dark OS preference — no manual wiring to PaperMod's theme toggle needed.

**Commit:**

```bash
git add layouts/
git commit -m "feat: add Giscus comments partial"
```

---

### Task 12: Create callout shortcode and styles

**Step 1: Create the shortcode**

```bash
mkdir -p layouts/shortcodes
```

File: `layouts/shortcodes/callout.html`

```html
{{- $type  := .Get "type"  | default "note" -}}
{{- $title := .Get "title" -}}
<div class="callout callout-{{ $type }}">
  {{- with $title }}
  <div class="callout-title">{{ . }}</div>
  {{- end }}
  <div class="callout-content">{{ .Inner }}</div>
</div>
```

Note: `.Inner` is used without `| markdownify` because the `{{% %}}` shortcode delimiters (used in the migrated posts) cause Hugo to render the inner content as Markdown before passing it to the shortcode.

**Step 2: Create callout styles**

```bash
mkdir -p assets/css/extended
```

File: `assets/css/extended/custom.css`

```css
/* Callout blocks (converted from Obsidian/Quartz [!note] syntax) */
.callout {
  border-left: 4px solid;
  border-radius: 4px;
  padding: 0.75rem 1rem;
  margin: 1.25rem 0;
}

.callout-title {
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.callout-content > *:last-child {
  margin-bottom: 0;
}

.callout-note {
  border-color: var(--primary);
  background-color: color-mix(in srgb, var(--primary) 8%, transparent);
}

.callout-info {
  border-color: #3b82f6;
  background-color: color-mix(in srgb, #3b82f6 8%, transparent);
}

.callout-warning {
  border-color: #f59e0b;
  background-color: color-mix(in srgb, #f59e0b 8%, transparent);
}

.callout-tip {
  border-color: #10b981;
  background-color: color-mix(in srgb, #10b981 8%, transparent);
}
```

**Commit:**

```bash
git add layouts/shortcodes/ assets/
git commit -m "feat: add callout shortcode and styles"
```

---

### Task 13: Write GitHub Actions deploy workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy Hugo to GitHub Pages

on:
  push:
    branches: [v4]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive   # fetches PaperMod theme
          fetch-depth: 0          # needed for .GitInfo and lastmod dates

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: latest
          extended: true          # required for Sass/SCSS processing

      - name: Build
        run: hugo --minify

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    needs: build
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Commit:**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: add Hugo GitHub Pages deploy workflow"
```

---

### Task 14: Verify local build

**Step 1: Run a clean Hugo build**

```bash
hugo --minify 2>&1 | tail -5
```

Expected output ends with something like:
```
| EN
---+------
Pages            | 55
Paginator pages  |  0
Non-page files   |  0
Static files     |  X
Processed images |  0
Aliases          |  2
Cleaned          |  0

Total in XX ms
```

If there are `WARN` or `ERROR` lines, fix them before continuing.

**Step 2: Run local dev server**

```bash
hugo server -D
```

Open http://localhost:1313 and verify:
- [ ] Home page loads with post list
- [ ] A post with a callout renders the styled callout box (not raw `{{% callout %}}` text)
- [ ] Code blocks have syntax highlighting and a copy button
- [ ] Dark/light mode toggle works
- [ ] Tags page at `/tags/` lists all tags
- [ ] Search page at `/search/` has a working search input
- [ ] Archives page at `/archives/` lists posts by year
- [ ] About page at `/about/` shows the about content (not in post list)
- [ ] Giscus comment widget renders at the bottom of a post
- [ ] A post with `draft: true` in frontmatter does NOT appear in production build

**Step 3: Verify draft posts are excluded from production**

```bash
hugo list drafts
```

Then build without `-D` and confirm the draft count matches posts missing from `public/`:

```bash
hugo --minify --quiet && ls public/posts/ | wc -l
```

Draft posts should not appear in `public/posts/`.

---

### Task 15: Remove Quartz infrastructure files

Once the local build is verified, remove all Quartz-specific files.

**Step 1: Remove Quartz source and config**

```bash
git rm -r quartz/
git rm quartz.config.ts quartz.layout.ts
```

**Step 2: Remove Node.js files**

```bash
git rm package.json package-lock.json
git rm -r node_modules/ 2>/dev/null || true
```

If `node_modules/` is in `.gitignore` and not tracked, skip the last line.

**Step 3: Update .gitignore**

Open `.gitignore` and replace any Quartz/Node entries with Hugo equivalents:

```
# Hugo
public/
resources/
.hugo_build.lock

# Node (legacy — no longer needed)
node_modules/
```

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: remove Quartz infrastructure (source, config, node files)"
```

---

### Task 16: Push worktree branch and open PR

**Step 1: Push the branch**

```bash
git push -u origin hugo-migration
```

**Step 2: Open a PR from `hugo-migration` → `v4`**

```bash
gh pr create \
  --base v4 \
  --title "feat: migrate from Quartz to Hugo + PaperMod" \
  --body "Replaces Quartz v4 with Hugo + PaperMod theme.

## Changes
- Hugo site with PaperMod theme (git submodule)
- All 50 posts migrated to \`content/posts/\`
- Obsidian callout syntax converted to Hugo shortcodes
- Static assets moved to \`static/\`
- Giscus comments preserved (same repo/category IDs)
- GitHub Actions deploy workflow replaces Quartz sync
- Quartz upstream remote removed
- All Quartz source files, Node.js toolchain removed

## Verify before merging
- [ ] GitHub Actions build passes
- [ ] All posts render correctly
- [ ] Callout boxes display with correct styling
- [ ] Giscus loads on posts
- [ ] Search works
- [ ] Tags, Archives, About pages work
"
```
