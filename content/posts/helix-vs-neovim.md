---
title: My Take on Helix and Neovim
description: How do I like Helix and how does it compare to Neovim at this stage?
date: 2025-06-14
tags:
  - blog
  - tools
  - neovim
  - vim
  - helix
  - editors
draft: false
---

I am a long time GUI IDE user, and most of that time I've used [JetBrains](https://www.jetbrains.com/)
IDEs, in particular IntelliJ IDEA. But prior to using GUIs, I used `vi` (yes
`vi`, not `vim`!). Over this period of using GUIs, I would still use `vim` (now
actual `vim`, yes) when I needed quick and dirty stuff ... looking at or editing
some config file from a terminal, for example. Then six months or so ago, I
started using NeoVim. I documented some of my experience with NeoVim vis a vis
IntelliJ in [this](Could-I-Possibly-Switch-from-JetBrains-IDEs-to-Neovim.md)
blog. Since that time, I have been using NeoVim almost exclusively. This had
more to do with the [keyboard](https://www.zsa.io/moonlander) I've been using
over that period than any real dissatisfaction with IntelliJ (or RustRover).
Maybe I'll write a blog on that at some point.

In any case, I've been following the development of the [Helix](https://helix-editor.com)
editor, in part because I've been learning Rust and like to look at serious
Rust projects. One thing that intrigued me as an editor however was the way
Helix flips the action/selection approach of `(n)vi(m)` to a selection/action
approach, based on the [Kakoune](https://github.com/mawww/kakoune) editor's
influence on the project. I will discuss more of that below.

Given all this, I decided to follow up my earlier NeoVim/JetBrains blog by
writing this Helix/NeoVim pseudo-review. I don't feel it's a real review
since I'm not making any recommendations per se, just noting some key things
about Helix, and where things stand compared with NeoVim.

So let's jump in!

## Introduction to Helix

Helix is an editor built for the terminal, in Rust. It's lineage includes the
aforementioned Kakoune as well as NeoVim. A focus is also on ease-of-use,
including configuration. It has many of the things you'd expect in an editor,
with completion, syntax-aware highlighting, language server support. But it
lacks some things you'd want, like a plugin capability.

### Installation

You can install with common package managers such as `brew`, `apt`, `packman`
etc. on Mac/Win/Linux.

It's also easy to build with `cargo` from [source](https://docs.helix-editor.com/building-from-source.html).
I actually do both, a packaged install view `brew` and build from source, to
access some of the "nightly" features.

#### Build from source

Because I have both a packaged install and do the build from source, I need to
manage the Helix `runtime` directory that includes stuff that is, well, needed
at runtime. I didn't want my source build to use the same runtime files that
the packaged build uses, even though it's read-only. There is a `runtime`
directory in the root of the source tree. What I decided to do is do a regular
`cargo build --release` and then have a simple shell script to launch the
resulting binary.

```sh
cargo build --release
HELIX_RUNTIME=$(pwd)/runtime target/release/hx        [1]
```

> [1] is what I have a script to do, effectively; the main point is, set the
> HELIX_RUNTIME environment, whether in a script, manually as shown above, or
> via an shell RC file or equivalent.

#### Running Helix

The binary as you hopefully noticed is called `hx`. It has many of the
command-line flags that you would expect, and some missing that might be
useful.

```sh
hx --help
helix-term 25.01.1 (e7ac2fcd)
Blaž Hrastnik <blaz@mxxn.io>
A post-modern text editor.

USAGE:
    hx [FLAGS] [files]...

ARGS:
    <files>...    Sets the input file to use, position can also be specified via file[:row[:col]]

FLAGS:
    -h, --help                     Prints help information
    --tutor                        Loads the tutorial
    --health [CATEGORY]            Checks for potential errors in editor setup
                                   CATEGORY can be a language or one of 'clipboard', 'languages'
                                   or 'all'. 'all' is the default if not specified.
    -g, --grammar {fetch|build}    Fetches or builds tree-sitter grammars listed in languages.toml
    -c, --config <file>            Specifies a file to use for configuration
    -v                             Increases logging verbosity each use for up to 3 times
    --log <file>                   Specifies a file to use for logging
                                   (default file: /home/ray/.cache/helix/helix.log)
    -V, --version                  Prints version information
    --vsplit                       Splits all given files vertically into different windows
    --hsplit                       Splits all given files horizontally into different windows
    -w, --working-dir <path>       Specify an initial working directory
    +N                             Open the first given file at line number N
```

One flag I felt was missing was the `-R` like in NeoVim to open the file(s)
read-only. There also isn't a way (that I know of) to run an `hx` command on
startup like in NeoVim. I do recommend the tutorial, which you can open from
the command line with `--tutor` or from within `hx` via `:tutor`. The
`--health` command line option is similar to NeoVim's `checkhealth` but is only
available via the command line.

## Configuration

Helix uses `TOML` for configuration. The main config file is
`~/.config/helix/config.toml` which can be opened from within `hx` using the
`:config-open` command. You can also have a per-workspace configuration which
you can access via `:config-open-workspace`, which will override the main
config file. You can reload the configuration from within Helix with
`:config-reload`.

## Modal Editor

Helix like NeoVim is a modal editor, and the modes are mostly the same, with a
`normal` mode for commands and `input` mode for editing. The `select` mode in
Helix is like `visual` mode in NeoVim. The `<ESC>` key is as with NeoVim,
getting you back to `normal` mode.

## Motions and Common Actions

For the most part, the motions are the same. The `hjkl` keys behave the
same. Keys like `i` and `I` or `p` and `P` are the same. You copy/yank with `y`.
To create a new line and move to insert mode, you use `o` and `O` as with NeoVim.
But some things are different if you are used to NeoVim. I will discuss one of
the biggest differences in the next [section](#actionselection-vs-selectionaction),
but some things that continue to trip up my muscle memory are:

- moving to the beginning and end of line are different. The differences make
  sense, but still trip one up. To move to the beginning of a line you use `gh`.
  To move to the end of a line you use `gl`.
- while moving to the beginning of a file is the same as with `gg`;
  however, moving to the end of the file is `ge` not `G`.
- pasting with `p` and `P` as I mentioned earlier is the same ... except that
  that is for pasting what was yanked from within `hx`. If you have configured
  `hx` to support the system clipboard, pasting from there is `<sp>p` or `<sp>P`.
- `x` in `hx` selects the current line, rather than deleting the current
  character as in . Instead you use `d` to delete a character (which makes
  more sense).
- while `c` is the same to perform a change, `C` is not the same. See the
  discussion of multi-cursors later.

> Helix has an equivalent to NeoVim's `which-key` plugin built-in, to provide
> menu-like information about available keybindings. But Helix also provides
> available commands and some help text for the selected command.

![helix-command-completion](/images/helix-command-help.png)

## Action/Selection vs Selection/Action

One of the biggest differences in the core editing functionality in Helix vis
a vis NeoVim is how editing actions are performed. In NeoVim, the model is
`action` -> `selection`. In other words, you specify the action, such as
'change' (`c`) and then you specify what to perform the action on - the
'selection' (e.g. `w`). In Helix it's the opposite - you select what you want to
operate on, and then you specify the action ... `selection` -> `action`. This
difference comes from the `Kakoune` heritage. This definitely takes some getting
use to. One thing stays the same ... mostly: just as in NeoVim, Helix supports
adding a number with the selection to select multiple things, but you have to
explicitly be in `select` mode first.

| hx    | nvim | Description                                            |
| ----- | ---- | ------------------------------------------------------ |
| wc    | cw   | change word from cursor to end of word                 |
| v3wc  | 3cw  | change word from the cursor to the end of the 3rd word |
| rc    | rc   | change the current character to an 'c'                 |
| v3lrc | 4rc  | replace 4 characters with the letter 'c'               |

Some things in Helix are more consistent, dropping baggage in NeoVim from its
parentage. For example, to delete the current line, it's still `selection`/`action`
in Helix ... `xd` (where `x` selects the current line and then `d` deletes it),
whereas in NeoVim you'd use `dd`. Or to yank the current line, in Helix you'd
use `xy` vs NeoVim's `yy`. So while generally there is an `action`/`selection`
model in NeoVim, it's inconsistent, which is one of the things Helix was trying
to address.

## Multi-cursor features

One of the really cool things in Helix is the multi-cursor capabilities it has
built in. (See section 5 of the Helix tutorial.) You can very easily make the single
cursor into multiple cursors with the `C` command in `normal` mode. It can seem
a little strange at first. `C` creates a single additonal cursor on the next line
that has text at the same column. Once you have "split" the cursor so there are
now 2 cursors, if you use the standard `hjkl` commands _both cursors move_. But
the movement now takes into account the text per line. So if one cursor is in
the middle of a line, if the lines the cursors are on are of different lengths,
using `l` will move the first cursor left, but the second cursor, when it
reaches the end of the line it's on, will wrap to the first character of the
next line. Basically, once you've created the additional cursor(s) with `C`,
each cursor "respects" the line it's on with respect to movement or other
actions. So now if you want to modify the text, you perform actions as usual.
If you want to add text at each cursor, simply perform the action as if you had
just one cursor.

To "collapse" the multiple cursors back to just one cursor, use the `,` command.

{{% callout type="warning" %}}
Make sure you exit this multi-cursor mode with `,`. It can bite you otherwise
since the other cursors may not all be visible in your current buffer view.
If you forget and start editing at where you think the cursor is at, you
could be editing other places at the same time! This applies as much to the
multi-selection stuff below.
{{% /callout %}}


You can use counts with the `C` command as you would other selection actions.
So `4C` would create 4 cursors - _in addition to the current cursor_ - for
5 total. `C` creates cursors _after_ the current cursor. To create them above
the current cursor use `Alt-C`.

### Helix `C` vs NeoVim `<ctrl>v`

In NeoVim you can select columns of text with `<ctrl>v`. But there are limits
to what you can do once you've selected content. NeoVim doesn't really have
multiple cursors out-of-box. You need a plugin like [`multicursors.nvim`](https://github.com/smoka7/multicursors.nvim).
Not all actions are possible with `<ctrl>v`. But Helix comes with some excellent
multi-cursor features. As a quick example, let's say we had the following text

```text
foo
bar
baz
```

Let's say we wanted to make it into an unordered list in Markdown i.e. add `-`
in front of each line. In Helix, (once your cursor is on `f` of `foo`) you
would do `2Ci-`. In NeoVim, it would seem I could use `<ctrl>v2ji-` but at
least for me it doesn't work. On the other hand, I can use `<ctrl>v` to replace
selected characters. In Helix it's consistent - to replace rather than insert,
just use `r` rather than `i`: `2Cr_` to replace selected characters with '\_'.

## Multi-selection features

Similar to the multi-cursor features, you can select multiple items and then
operate on them all at the same time. Effectively you're using a search to
determine how to create multiple cursors.

Let's say you wanted to change every word "helix" to "hx" in this whole document.

- select the entire document e.g. `v%` or `x%`
- use the `s` command which will show `select:` in the status line, prompting
  what to search for
- enter `helix` and press `<enter>`
- this will create a cursor at each occurence of the word
- use `c` to indicate the change action and type `hx`
- et voila

> In NeoVim this would be achieved with e.g. ":%s/helix/hx/g". In Helix it feels
> a little more like you have more fine-grained control, but that's just me.
> Functionally the two are equivalent.

You can also use a regex pattern to select the text to operate on.

### Easily Aligning Content

Another feature I found compelling was the easy way you can align some text. I
can't find a similar way to do it in NeoVim (again, maybe my fu is weak). Let's
say you had some text like

```text
Commands|Description
Start|Start it
Stop|Stop it
Restart|Restart it
Kill|Kill it
```

You want to "right align" the commands so the text looks like

```text
Commands|Description
   Start|Start it
    Stop|Stop it
 Restart|Restart it
    Kill|Kill it
```

What you would do is move your cursor to the start of the line with "Commands"
and do `4Cw&`.

> If anyone know how to do this "easily" in NeoVim, please let me know in the
> comments. I'm always looking to improve my NeoVim-fu!

{{% callout type="note" %}}
It seems you can only align to the right. I can't figure out how to "left
align". If you know how, let me know!
{{% /callout %}}


## Writing & Testing Code

I began using NeoVim more when I started using it as my primary IDE. So
naturally as I looked more at Helix I wanted to see how well it does as an IDE.
The bottom line is, so-so. It has the basics like syntax highlighting, completion
and code navigation (go to references, definitions, etc.) and some more advanced
stuff like basic refactoring. The symbol picker is nice out-of-box with Helix -
`<space>s` to open a picker for symbols in the current file; `<space>S` for a
fuzzy finder picker for all symbols in the workspace. The NeoVim equivalent
(using the LazyVim distro) is `<leader>ss` or `<leader>sS`. Very similar, though
NeoVim has more of a tree structure with icons to indicate symbol type and also
text color coding, while Helix has plain text e.g 'module', 'method':

![code symbols](/images/hx-vs-nvim-code-symbols.png)

Even so, as a full IDE Helix still has some way to go:

- you can't run your application
- you can't debug
- you can't run tests
- there's no terminal

There are also differences per language in what is supported. For example, the
`]T` command says 'goto next test' in the `which-key`-esque description, but
nothing happens for Java. With Rust, it selects the test method.

A lot of that if not all of it is on the roadmap, but nevertheless it's still
todo. You could write some key bindings to help with some of that, but even so
it's limited. For example, I created a key binding to execute `cargo test`:

```toml
[keys.normal.space]
t = [
    ':new',
    ':insert-output cargo test',
]
```

With this I can to `<space>t` in `normal` mode which will put the output of
`cargo test` into a new scratch buffer. This works fine ... if you're in a
Rust project directory. While Helix is able to start an appropriate LSP (if
configured), so it's aware if you're in a Rust workspace or a Java workspace
or what not, there's no way (that I know of) to have different key bindings
based on that. So if I'm in a Java project and press `<space>t` Helix will
still run `cargo test`, given the above key binding.

Another problem with the key mapping as I have it is that it's "blocking" -
while `cargo test` is running, Helix can seem to be hanging. Depending on the
state of your workspace, this may or may not happen all the time. But if
`cargo` or `mvn` or what not needs to download a lot of dependencies and
recompile a lot of stuff, it can seem like Helix is hung.

### Key Bindings Per Workspace

One way you could achieve running different tools for different languages is
using Helix's per-workspace configuration I mentioned in the [configuration](#configuration)
section earlier. You could put a `.helix/config.toml` file in each project
root directory and put the key binding configuration you want for that project
there. This would allow you to have `<space>t` map to `cargo test` in your
Rust project, `mvn test` in a Maven project, `gradle test` in a Gradle project,
etc. The downside is that you'd have to manually add the same config file in
each project, though you could script that to symlink them all to the same file
you place somewhere.

```sh
cd ~/src
mkdir .helix && cd .helix
hx config-rust.toml # put your `cargo test` and any other `cargo` bindings here
hx config-mvn.toml # put your `mvn test` and any other `mvn` bindings here
hx config-gradle.toml # put your `gradle test` and any other `gradle` bindings here
cd ~/src/my-rust-project
setup-helix-config.sh rust
```

```sh
#!/bin/bash
#
# setup-helix-config.sh
# Create .helix in current dir and symlink to a config in ~/src/.helix
#
if [ $# -ne 1 ]; then
    echo "Usage: $0 <rust|mvn|gradle>"
    exit 1
fi

case "$1" in
    rust|mvn|gradle)
        config_type="$1"
        ;;
    *)
        echo "Error: Invalid argument. Must be one of: rust, mvn, gradle"
        exit 1
        ;;
esac

mkdir -p .helix

echo "ln -sf $HOME/src/.helix/config-${config_type}.toml .helix/config.toml"
ln -sf $HOME/src/.helix/config-${config_type}.toml .helix/config.toml
```

A workaround, though obviously not ideal. But I set that up and it works as
intended.

## Writing Markdown

I'm writing this blog post in Helix. Like any other "language" Helix is aware
of the file type and does appropriate syntax highlighting. But that's about
the extent of the built-in support at this stage. There is no in-line preview
like some NeoVim plugins provide (e.g. `MeanderingProgrammer/render-markdown.nvim`).
You can integrate an external preview along with a key binding. For example,
I set up this:

```toml
# config.toml
[keys.normal]
M = ':lsp-workspace-command open-preview'
```

```toml
# language.toml
[language](language)
name = "markdown"
language-servers = ["marksman", "mpls"]

[language-server.mpls]
command = "mpls"
args = ["--enable-emoji", "--no-auto", "--enable-wikilinks"]
```

And installed the `mpls` [Markdown Preview Language Server](https://github.com/mhersson/mpls).
I had go installed already so I used that method, but there are other download
methods.

```sh
go install github.com/mhersson/mpls@latest
```

> Make sure the resulting `mpls` executable is in your PATH

The limitation described above about executing `cargo` tests exists here as
well - the key binding of `M` is not specific to Markdown files, so if you
use `M` on a non-Markdown file you'll set an error about no such LSP command
`open-preview`.

I could of course do something like I did for `cargo`, `mvn` et al above for
this Mardkown keybinding.

## Missing Stuff

Some things are not implemented yet in Helix. Obviously it's a newer project.

- you have to install LSPs manually. There is no equivalent to Mason.
- as I alluded to earlier, there is no terminal support or mode within Helix;
  you'll have to use a terminal multiplexer like `tmux` or features from your shell
  for splits or tabs
- only basic Git support and no other VCSs
- no plugin system
- while some configuration is simpler in Helix, as discussed above, there are
  still limitations, both in terms of what is configurable and how configurable
  it is.

## Summing Up

I hope this gives a feel for Helix as it stands as of this writing, version
25.01.1. I like Helix. I think there is a lot of promise. That said, it's not
at a point where you could drop NeoVim (or whatever you use) if you're looking
for an IDE for coding. Depending on what you're used to or looking for, even
using Helix for writing Markdown is somewhat limited compared to NeoVim as
noted.

The challenges I see in adoption of Helix come mostly from the long legacy of
`(n)vi(m)`. I have _35 years_ of muscle memory with `(n)vi(m)` motions I need
to "re-map", but even someone who started with `vim` or even `nvim`, the basic
difference of `selection/action` vs. `action/selection`, `d` vs `x`, etc. are a
long time pain.

For someone who never really used `(n)vi(m)` and is coming from something like
`VS Code` but wants to learn a terminal modal editor, going right to
Helix might be easier - in many ways it's simpler and more consistent as I
described. NeoVim can be a handful to configure to be a good IDE, even with
distros like LazyVim and its brethren.

For me personally, I will keep my eye on Helix, but I'm not switching from NeoVim
(or IntelliJ or RustRover). Maybe I'll try my hand at contributing to Helix.

> [!question]
> What do you think of Helix? I'd love to hear your experiences! Leave them in
> the comments.
