# Design: Migrate kidoni.dev from Quartz to Hugo + PaperMod

**Date:** 2026-02-26
**Status:** Approved

## Goals

Replace the Quartz v4 static site generator with Hugo + PaperMod theme. The
motivation is a simpler, more conventional setup with less TypeScript
infrastructure while preserving all current site features: code highlighting,
search, tags, light/dark mode, Giscus comments, draft filtering, and local
preview.

## Repository Layout After Migration

```
kidoni.dev/
├── hugo.yaml                      # site config (replaces quartz.config.ts + quartz.layout.ts)
├── content/
│   ├── posts/                     # all blog posts (moved from flat content/)
│   └── about.md                   # about page (sourced from current content/index.md)
├── static/
│   ├── images/                    # moved from content/images/
│   └── assets/                    # moved from content/assets/
├── themes/PaperMod/               # git submodule
├── layouts/
│   ├── partials/comments.html     # Giscus embed
│   └── shortcodes/callout.html    # replacement for Obsidian callout syntax
├── assets/css/extended/
│   └── custom.css                 # callout block styles only (no font overrides)
└── .github/workflows/deploy.yml   # replaces quartz sync commit workflow
```

**Removed entirely:** `quartz/`, `quartz.config.ts`, `quartz.layout.ts`, all
TypeScript/Node infrastructure.

## Hugo Configuration (`hugo.yaml`)

Settings carried over from the current Quartz config:

| Setting | Value |
|---|---|
| `baseURL` | `https://kidoni.dev` |
| Google Analytics | tag `G-X783PXP90Q` (Hugo first-class support) |
| `defaultTheme` | `auto` (follows OS preference, with manual toggle) |

PaperMod params enabled:

- `ShowReadingTime: true`
- `ShowBreadCrumbs: true`
- `ShowShareButtons: true`
- `ShowPostNavLinks: true`
- `ShowToc: true` (collapsible, rendered in-content on desktop)
- `comments: true`
- Search enabled via Fuse.js (requires a `content/search.md` page)

Fonts: PaperMod system font defaults — no Google Fonts, no custom font config.

## Content Migration

### What does not change

- All ~50 `.md` blog post files — content is untouched
- `draft: true/false` frontmatter — Hugo uses the same key, zero changes needed
- Tags — Hugo taxonomies pick these up automatically

### File moves

| Current | After |
|---|---|
| `content/*.md` (blog posts) | `content/posts/*.md` |
| `content/index.md` | `content/about.md` (root, not in posts/) |
| `content/images/` | `static/images/` |
| `content/assets/` | `static/assets/` |

The about page (`content/about.md`) is a standalone page placed outside
`content/posts/` so Hugo never includes it in the post list. It is added to the
site navigation menu via `hugo.yaml`.

### Image path updates

Posts currently reference images as `content/images/foo.png`. After moving
images to `static/images/`, references become `/images/foo.png`. The migration
script updates these paths automatically.

### Obsidian callout conversion

20 files contain ~35 callout blocks using Quartz/Obsidian syntax. The migration
script converts these to a custom Hugo shortcode.

**Before:**
```markdown
> [!note] Written with AI
> This post was built with Claude Code.
```

**After:**
```markdown
{{% callout type="note" title="Written with AI" %}}
This post was built with Claude Code.
{{% /callout %}}
```

Types found in the content: `note` (23), `info` (10), `warning` (1), `tip` (1).
All map 1:1. Titles are optional — callouts without titles are handled correctly.

The shortcode is rendered via `layouts/shortcodes/callout.html`. Visual styling
(border, background tint per type) lives in `assets/css/extended/custom.css`.

### Wikilinks

3 files contain `[[wikilink]]` syntax. The migration script converts these to
standard Markdown links `[wikilink](wikilink)`.

## Giscus Comments

PaperMod invokes `layouts/partials/comments.html` when `params.comments: true`.
A single custom file embeds the Giscus script using the existing configuration —
no Discussions data changes, no re-setup required.

| Giscus param | Value |
|---|---|
| `data-repo` | `kidonisoftware/kidoni` |
| `data-repo-id` | `R_kgDONduRGw` |
| `data-category` | `Announcements` |
| `data-category-id` | `DIC_kwDONduRG84ClO6M` |
| `data-input-position` | `top` |
| `data-theme` | `preferred_color_scheme` (tracks light/dark mode) |

Existing comments are preserved — Giscus maps threads by URL path, which is
unchanged.

## Search

PaperMod uses Fuse.js for client-side search. Requires:

1. `outputs.home` includes `JSON` in `hugo.yaml`
2. A `content/search.md` file with `layout: search` frontmatter
3. A menu entry pointing to `/search/`

No external service, no API keys.

## Deployment

Replaces the `quartz sync` commit pattern with a standard GitHub Actions
workflow triggered on push to `v4`.

Steps:
1. Checkout repo with `submodules: recursive` (fetches PaperMod theme)
2. Install Hugo latest (extended, for Sass support)
3. `hugo --minify` → generates `public/`
4. Deploy to GitHub Pages via native artifact upload

**Publish workflow is unchanged for day-to-day use:** write a post, `git add`,
`git commit`, `git push`. The Action builds and deploys automatically.

## Local Preview

```sh
hugo server        # production preview
hugo server -D     # include draft posts
```

Equivalent to `npx quartz build --serve`. Live reload on every file save.

## Implementation Approach

Work is done in a **git worktree** on a new branch `hugo-migration`, keeping
the live `v4` branch untouched until the new site is verified and ready to
merge.

### Ordered steps

1. Initialize Hugo site in the worktree + add PaperMod as git submodule
2. Write `hugo.yaml` with all config
3. Write and run the migration script:
   - Move posts to `content/posts/`
   - Update image paths
   - Convert Obsidian callouts to shortcode syntax
   - Fix wikilinks
4. Move assets to `static/`
5. Create `content/about.md` from `content/index.md`
6. Create `content/search.md`
7. Write `layouts/partials/comments.html` (Giscus)
8. Write `layouts/shortcodes/callout.html`
9. Write `assets/css/extended/custom.css` (callout styles)
10. Write `.github/workflows/deploy.yml`
11. Run `hugo server` and verify locally
12. Remove Quartz infrastructure files
13. Merge `hugo-migration` → `v4`
