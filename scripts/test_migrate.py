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
    assert '{{< callout type="note" >}}' in result
    assert "This is note content." in result
    assert "{{< /callout >}}" in result
    assert "Normal paragraph." in result

def test_callout_note_with_title():
    lines = [
        "> [!note] Written with AI",
        "> This post was built with Claude Code.",
    ]
    result = convert_callouts(lines)
    assert '{{< callout type="note" title="Written with AI" >}}' in result
    assert "This post was built with Claude Code." in result
    assert "{{< /callout >}}" in result

def test_callout_info_with_title():
    lines = [
        "> [!info] An aside on the architecture.",
        "> Some info content.",
    ]
    result = convert_callouts(lines)
    assert any('type="info"' in line for line in result)
    assert any('title="An aside on the architecture."' in line for line in result)

def test_callout_warning():
    lines = ["> [!warning]", "> Be careful here."]
    result = convert_callouts(lines)
    assert any('type="warning"' in line for line in result)

def test_callout_tip():
    lines = ["> [!tip]", "> Use this shortcut."]
    result = convert_callouts(lines)
    assert any('type="tip"' in line for line in result)

def test_callout_question():
    lines = ["> [!question]", "> Is this correct?"]
    result = convert_callouts(lines)
    assert any('type="question"' in line for line in result)

def test_callout_important():
    lines = ["> [!important]", "> Pay attention here."]
    result = convert_callouts(lines)
    assert any('type="important"' in line for line in result)

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
    assert result_str.count("{{< callout") == 2
    assert result_str.count("{{< /callout >}}") == 2

def test_callout_type_is_lowercased():
    lines = ["> [!NOTE]", "> Content."]
    result = convert_callouts(lines)
    assert any('type="note"' in line for line in result)


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
