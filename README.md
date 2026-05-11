# kidoni.dev

Personal blog at [kidoni.dev](https://kidoni.dev), built with
[Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod)
theme. Comments are powered by [Giscus](https://giscus.app/) via GitHub Discussions.

## Prerequisites

- [Hugo extended](https://gohugo.io/installation/) (extended variant required for Sass processing)

Install with Homebrew:

```sh
brew install hugo
```

Verify the extended variant is installed:

```sh
hugo version   # should include "extended" in the output
```

## Local Development

### Preview the site

```sh
hugo server
```

Opens a live-reloading server at http://localhost:1313. The site rebuilds automatically on every file save.

### Preview including draft posts

```sh
hugo server -D
```

### Production build

```sh
hugo --minify
```

Output is written to `public/`. This directory is not committed — the GitHub Actions workflow builds and deploys it on every push to `main`.

## Writing Posts

1. Create a new `.md` file in `content/posts/`:

   ```sh
   hugo new posts/my-new-post.md
   ```

   Or just create the file directly — there is no required scaffolding beyond the frontmatter.

2. Add frontmatter at the top of the file:

   ```yaml
   ---
   title: "My Post Title"
   description: "A short description shown in post listings."
   date: 2026-01-15
   tags:
     - rust
     - programming
   draft: true
   ---
   ```

   Set `draft: false` (or remove the field) when ready to publish.

3. Write content in standard Markdown below the frontmatter.

### Callout blocks

Use the `callout` shortcode for highlighted notes:

```markdown
{{% callout type="note" title="Optional title" %}}
Content here supports **Markdown**.
{{% /callout %}}
```

Available types: `note`, `info`, `warning`, `tip`, `question`, `important`, `danger`.

### Images

Place images in `static/images/` and reference them as:

```markdown
![alt text](/images/my-image.png)
```

### Other assets (PDFs, etc.)

Place files in `static/assets/` and link them as:

```markdown
[Download](/assets/my-file.pdf)
```

## Publishing

Push to `main` — the GitHub Actions workflow builds the site and deploys it to GitHub Pages automatically.

```sh
git add content/posts/my-new-post.md
git commit -m "feat: add post on <topic>"
git push
```

Draft posts (`draft: true`) are excluded from the production build automatically.

## Useful Commands

| Command | Description |
|---|---|
| `hugo server` | Live preview at localhost:1313 |
| `hugo server -D` | Live preview including drafts |
| `hugo --minify` | Production build to `public/` |
| `hugo list drafts` | List all draft posts |
| `hugo list all` | List all content with dates and draft status |
| `hugo --minify --templateMetrics` | Show template render times (performance debug) |

## Site Structure

```
content/
  posts/        # blog posts
  about.md      # about page (not a blog post)
  search.md     # search page
  archives.md   # archive page
static/
  images/       # images referenced in posts
  assets/       # other static files (PDFs, etc.)
layouts/
  partials/
    comments.html     # Giscus comment embed
  shortcodes/
    callout.html      # callout block shortcode
assets/css/extended/
  custom.css          # callout styles
themes/PaperMod/      # PaperMod theme (git submodule)
layouts/
  baseof.html                         # override: .Language.Direction (PaperMod deprecation workaround)
  rss.xml                             # override: site.Language.Locale (PaperMod deprecation workaround)
  _partials/templates/opengraph.html  # override: site.Language.Locale (PaperMod deprecation workaround)
scripts/
  migrate.py          # one-shot Quartz→Hugo migration script (kept for reference)
hugo.yaml             # site configuration
.github/workflows/
  deploy.yml          # GitHub Actions build + deploy
```

## Configuration

Site configuration is in `hugo.yaml`. Key settings:

- **Theme, title, base URL** — top-level fields
- **PaperMod params** — under `params:` (TOC, reading time, share buttons, comments, etc.)
- **Navigation menu** — under `menu.main:`
- **Syntax highlighting** — under `markup.highlight:` (currently Monokai)
- **Google Analytics** — under `services.googleAnalytics:`
