---
title: Taking Screenshots in Neovim with Silicon
description: Integrating the `silicon` tool with Neovim to take screenshots of code.
date: 2025-02-15
tags:
  - plugins
  - neovim
  - programming
  - blog
draft: false
---

When I started writing blogs, since my code was stored in GitHub, I would use
GitHub Gists of my code snippets to use in my blogs. I was also predominantly
using JetBrains IDEs, which have a built-in Gist-taking feature, which I love.
This was very convenient, _staying within my IDE_. Because I was also using
Medium to publish my blogs, this turned out to be very convenient because Medium
could take the URL of the Gist and nicely embed the image in the published blog.
However, because the URL is actually to some Javascript, and not to an image file
like a PNG or JPG, I could not use the Gist URL in my blog posts on my own website
quite so easily. This is in part because of the publishing tool I'm using (
[Quartz](https://github.com/jackyzha0/quartz.git)), but also because I want the
Gist to show "inline" like an embedded image.

I am also using Neovim as my editor to write my blogs now (rather than directly
in Medium). I write plain Markdown, with some Obsidian features, since Quartz
supports Obsidian-style Markdown. I also use Neovim to write code for the most
part (see my blog about [switching from JetBrains IDEs to Neovim](https://kidoni.dev/Could-I-Possibly-Switch-from-JetBrains-IDEs-to-Neovim)).
So what were my options? I could just use the Markdown formatting for code
blocks ...

````text
```rust
fn main() {
    println!("Hello, world!");
}
````

Or I could use the screenshot tool installed on my system (Ubuntu in this case),
taking a screenshot of my editor, _using the mouse_ to select the bit I wanted.
The tool automatically saves the screenshot to a file in a default directory with
a default name format. If I don't immediately rename it to something meaningful,
and instead keep taking other screenshots, I don't know what each file is a
screenshot of.

```sh
$ l
.rw-rw-r-- 1.1M ray 15 Feb 12:29 'Screenshot from 2025-02-15 12-29-14.png'
.rw-rw-r-- 1.1M ray 15 Feb 12:29 'Screenshot from 2025-02-15 12-29-23.png'
.rw-rw-r-- 1.1M ray 15 Feb 12:29 'Screenshot from 2025-02-15 12-29-32.png'
```

And to do this I have to leave Neovim. It would be very nice if I could stay
in my editing environment, which I use for both code and writing my blogs. Well,
I found a tool that lets me do just that!

## Silicon

Silicon is a command-line tool enabling making images from files, focusing on
code files. You can use it standalone, from your shell, and give it a file to
make an image from. It guesses the language from the file extension (e.g. .rs).
You can control things like the theme for the text, whether to show line numbers,
if specific lines should be highlighted, the font to use and some other knobs.

But conveniently, there are some plugins for Neovim that integrate with `silicon`.
The one I'm using is [michaelrommel/nvim-silicon](https://github.com/michaelrommel/nvim-silicon).
It requires you to install `silicon` first for your system. It is available via
`brew` so I used that (`brew install silicon`). I use Lazy.nvim as my package
manager and overall "distro", so to install and configure the plugin I have
`~/.config/nvim/lua/plugins/nvim-silicon.lua` with

```lua
-- requires `silicon` to be installed e.g. `brew install silicon`
return {
 "michaelrommel/nvim-silicon",
 lazy = true,
 cmd = "Silicon",
 config = function()
  require("nvim-silicon").setup({
   -- for list of themes available use `silicon --list-themes`
   theme = "gruvbox-dark",
   -- for list of fonts installed use `fc-list`
   font = "JetBrainsMonoNLNerdFontMono-ExtraBold",
   no_window_controls = true,
   pad_horiz = 0,
   pad_vert = 0,
   window_title = function()
    local buf_name = vim.api.nvim_buf_get_name(vim.api.nvim_get_current_buf())
    local fname = vim.fn.fnamemodify(buf_name, ":t")
    return fname
   end,
   output = function()
    local vpath = vim.fn.expand("~") .. "/Pictures/Screenshots/"
    local buf_name = vim.api.nvim_buf_get_name(vim.api.nvim_get_current_buf())
    local fname = vim.fn.fnamemodify(buf_name, ":t")
    return vpath .. fname .. "-" .. os.date("!%Y%m%d-%H%M%S") .. ".png"
   end,
  })
 end,
}
```

or, using the plugin itself to take a screenshot of the contents ...
![nvim-silicon](/images/nvim-silicon.lua-20250215-204607.png)

Which looks better?

### Plugin configuration

Let me explain some of the things I changed from the default.

- theme and font - I selected the `gruvbox-dark` theme and the
  `JetBrainsMonoNLNerdFontMono-ExtraBold` font because I think those are pleasing,
  and I use the JetBrains fonts in other IDEs and tools.
- no_window_controls - I don't want the window controls (close, minimize, maximize)
  to show up, and they were "MacOS"-style as well.
- pad_horiz and pad_vert - I don't want any padding around the image; by default
  it had room around the image that for me was just wasting space.
- window_title - I want the title of the window to be the name of the file I'm
- output - I want the output to be a file in my `~/Pictures/Screenshots/`
  directory, with the name of the current file as part of the image file name;
  by default it goes to the same directory as the current file.

With this configuration I solve most of my issues creating pleasing images of
code snippets, staying within my IDE like I could with JetBrains IDEs while also
addressing the issue of auto-generated file names so I can more easily well what
is in each file.

#### Keybindings

One last thing I did was to add a keybinding to take a screenshot. With the config
as shown, to take a screenshot you would highlight the code you want to capture
in visual mode and execute `:Silicon`. To make that a little easier, I added a
keybinding to my `~/.config/nvim/lua/config/keymaps.lua` file:

```lua
-- take a screenshot of selection with ctrl-t
vim.keymap.set(
        "v",
        "<C-t>",
        ":Silicon<CR>",
        { noremap = false, silent = false, desc = "[t]ake screenshot from selection" }
)
```

With that I can select the bit I want in visual mode and hit `ctrl-t` to take
the screenshot.

## Final thoughts

I haven't tried all the options available, like having specific lines highlighted.
I'm not quite sure how to support that within Neovim. I also was having issues
with the `silicon` command itself, for some reason, but since I have what I wanted
from within Neovim, those things don't matter at the moment.
