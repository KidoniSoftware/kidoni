---
title: Could I Possibly Switch from JetBrains IDEs to Neovim?
description: Is Neovim and IDE on par with JetBrains' IDEs and other GUI IDEs?
date: 2024-09-02
tags:
  - blog
  - Neovim
  - JetBrains
  - IDE
  - programming
draft: false
---

I have been using --- and
loving --- [JetBrains](https://www.jetbrains.com/)
[Integrated Development Environments (IDEs)](https://www.jetbrains.com/ides/)
and other tools (I like [TeamCity](https://www.jetbrains.com/teamcity/) a lot!)
since effectively version 1 of [IntelliJ IDEA](https://www.jetbrains.com/idea/)
since it was released in the early 2000s. Compared to the other IDEs I tried at
the time like [NetBeans](https://en.wikipedia.org/wiki/NetBeans), [JBuilder](https://en.wikipedia.org/wiki/JBuilder)
and [Eclipse](https://en.wikipedia.org/wiki/Eclipse_%28software%29), IntelliJ
was just better all around. But the really great thing that I liked about it in
addition to its overall look & feel was its *keyboard integration*. That's
right, *keyboard integration*.

Of course, there are other great things about IntelliJ --- its **refactoring**
support was (and is) superior to any other IDE then or since, it's **Spring
Framework** and then **Spring Boot** support and integration exceeds even
Spring's own [Eclipse-based Spring Tool Suite](https://spring.io/tools) (now
with VS Code support also. Personally I think this stems from the base upon
which it starts i.e. Eclipse.) There are many other great features and plugins,
too many to list. Let's just sum by saying I'm a big fan.

Fundamentally what it's all about is productivity. And not just productivity
writing code faster, but *writing good quality code*. That's one reason the
refactoring support is #2 after the keyboard support for me as far as the killer
feature that had me dump the other IDEs I was trying to use to be productive.
(JBuilder was my favorite until IntelliJ which makes a little sense since it
started with [Borland](https://en.wikipedia.org/wiki/Borland) who had made a
business out of good IDEs.)

But being productive when programming is still all about typing (AI code
generation from natural language input notwithstanding ... since a lot of that
is still typed in, on a keyboard). Some examples of common coding situations
where IntelliJ and its key bindings (and refactoring) make me so much more
productive are

> Some key bindings in the examples below may differ for you depending
> on which keymap you use as well as the Mac/non-Mac `<cmd>` vs `<ctrl-c>`
> issue.

- smart word (keyword, variable, method/class/etc. name, etc.) and block
selection --- using `ctrl-w` combined with the IDEs awareness of the language I
can quickly select or deselect (`shift-ctrl-w`) parts of words or code blocks.
Using Java (as I will mostly throughout with some Rust thrown in), the IDE is
"CamelCase" aware so I can easily select just "Camel" with one `ctrl-w` and if I
want the rest I can press `ctrl-w` again and select all of CamelCase. If I went
too far I can use `shift-ctrl-w` to undo smartly. So given say CamelCaseWord and
I pressed `ctrl-w` three times to select the whole word, but I just wanted
CamelCase selected, I can press `shift-ctrl-w` and it will back off to just
CamelCase. If I keep pressing `ctrl-w` IntelliJ will select progressively larger
blocks ... the current statement, the block, method, class, or deselect it with
`ctrl-shift-w`.

> Some may say that they don't like having to press `ctrl-w` two or three times
> in the above example to select the whole word, which is why you can
> enable/disable this via the IDE settings. Personally I find myself wanting to
> rename just parts of various names often that the smart `ctrl-w` *makes me
> more productive*.

- delete the current line to the clipboard --- with `ctrl-y` I can delete the
current line and have it go to the clipboard *without having to select the
current line first* (perhaps in a nod to the '\[y\]ank' in (neo)vim though this
would be more equivalent to 'dd' in vim).
- duplicate the current line --- similar to the above, without having to select
the line first, `ctrl-d` will duplicate the current line.
- rename variable/method/class refactor --- just press `shift-F6`
- extract method or variable refactor --- just press `ctrl-alt-m` or `ctrl-alt-v`
- extract constant refactoring --- say you have `log.info("` and you use `“YADA”`
a lot. Just have your cursor somewhere in that string, and press `ctrl-alt-c`
and you'll get a constant with default name the same as the string, and a prompt
for you to change the name or accept the generated one. You can also decide to
replace all such occurrences elsewhere in the file all at once at the same time.
- copy/move class/method/constant --- `F5`/`F6` create test class ---
`ctrl-shift-t` will create a new test class (e.g. in Java) in the correct Java
package, in the correct directory (e.g. src/test/java/package/name) with the
correct boilerplate.
- "surround with" --- let's say you wrote some code and you realize you should
have an if/else block around it; press --- `ctrl-alt-t` and a popup menu will
show alternatives like surround with if, if/else, try, while, synchronized, etc.

I could go on and on. Find usages, show inheritance hierarchy, extract
superclass/interface, setting breakpoints, building and running code,
debugging code, stepping over/info functions, evaluating expressions.
But the point is, *I don't have to take my hand off the keyboard* and
use a mouse. The context switch from keyboard to mouse and back impacts
your flow even if just slightly and therefore your productivity. The
more I can do just with the keyboard the more productive I am.

## Enter Neovim

I have been using Neovim recently. Prior I was using Vim, but usually for quick
and easy things ... writing a shell script or tweaking one, editing my various
dotfiles and other relatively trivial tasks when I'm in the terminal. And I'm
old enough to have used Vi on Unix before Vim and Linux existed. In fact, in the
late 80s and 90s first in college and then my first years as a professional, I
did my C development all with Vi. Looking back I'm very surprised how I managed!
You needed a hodgepodge of tools like man pages for docs on method signatures
say, `tags` to help with jumping around in your code, or something slightly more
sophisticated like `cscope`. I remember at my first job which was working on the
Unix kernel for a hardware company (everyone had their own Unix) we had "kscope"
which was a shell wrapper around `cscope` with a prebuilt `cscope` database to
help navigate the Unix kernel. In fact, with Linux there's still a Makefile
command to build the `cscope` database ...

```bash
make cscope 
```

I must say I'm glad my `cscope` days are over. These days in Linux better to
create a [compilation database](https://github.com/torvalds/linux/blob/master/scripts/clang-tools/gen_compile_commands.py)
that several IDEs support like VS Code and CLion (from JetBrains 😄)...

```bash
scripts/clang-tools/gen_compile_commands.py
```

But I never even considered switching to an editor in a terminal UI ... I mean
how could it possibly compare to IntelliJ.

Well, at least with Neovim, maybe I was wrong!

Take a look at these screenshots of my Neovim as I edit a Rust file

![code editing with doc pupup](/images/nvim-doc-popup.png)

![interactive debug session](/images/nvim-dap-view.png)

The first screenshot is an editing session, with the file in the "main" middle
part of the window, a directory tree on the left and a symbol explorer tree on
the right, and a documentation popup showing the docs for the Rust type under
the cursor. I opened the directory tree from the keyboard `<leader>E` and I
opened the symbol tree on the left with the keyboard `<leader>cs` and of course
the file itself from the terminal in the first place though naturally I could
open it directly from the editor `:e src/main.rs`. The documentation popup
dialog was just `K`.

> If you're new to (Neo)vim, the `<leader>` is the key (or keys) that are the
> prefix to indicate a command sequence is starting. There are also "modes"
> like "insert" mode where you're editing content or "normal" mode which is the
> "command" mode where keys execute commands (if mapped). I think every key
> sequence I have as examples in this post are executed in "normal" mode. These
> key sequences then depend on the definition in your config of `<leader>`
> which for me is the spacebar i.e. a single space. So if you have `<leader>cs`
> this means the key sequence `space` followed by `c` followed by `s`. This
> notion of a "leader" prefix is common in terminal apps ... e.g. `tmux`

I can switch between the directory tree and the file from the keyboard `ctrl-h`
and `ctrl-l` and the file and the symbol tree `ctrl-l` and `ctrl-h`. I could
jump to a method or type definition from the keyboard from the file directly
`<leader>gd` or by navigating the symbol tree with the normal Neovim/Vim/vi
navigation keyboard commands `hjkl` or `ctrl-f`/ `ctrl-b` / `ctrl-u` / `ctrl-d`
and even search for symbols with `/`.

And when you're done editing, you can debug from the same session, as you can
see in the second screenshot. The Neovim window shows a typical debugging UI
(`<leader>du`) with display of the in-scope variables, call stack on the left,
the execution controls on the bottom (step into/over, continue, etc). I can set
a breakpoint `<leader>db` and run with or without arguments (`<leader>da` and
`<leader>dr` respectively). It's even aware of different run configurations
available in my Rust project so it will have a popup dialog showing the options
to run. I can step into `<leader>di` a method or over or out of it (`<leader>dO`
or `<leader>do`).

There's also a pretty comprehensive Git integration, for example with
[LazyGit](https://github.com/jesseduffield/lazygit):

![Git integration in Neovim with LazyGit](/images/nvim-lazygit.png)

You can do pretty much anything here. Bringing up this view is `<leader>gg` or I
could look at just the commits that were done `<leader>gc` or just the Git log
for the current file `<leader>gl`. I can interactively stage hunks of the file
`<leader>ghs` or the whole buffer `<leader>ghS`.

You get (or is it git 😆) the idea.

You can do other cool things like doing "structural" copies e.g.
copying/changing/deleting text within or around blocks delimited by some
characters like braces or quotes or parentheses. Given

```bash
log.info("this is some message");
```

if I did `<leader>ci”` then Neovim would delete the text `this is some message`
and then place you in insert mode after the first quote so you can then enter
the replacement text.

You can comment out blocks. You can visually select regions of text. You can
work with multiple files either as panes within the same window or as tabs, and
navigate between them with fuzzy matching (by integrating [`fd`](https://github.com/sharkdp/fd)
and [`fzf`](https://github.com/junegunn/fzf)) and improved search i.e. grep (by
integrating [`rg`](https://github.com/BurntSushi/ripgrep)) including previewing
the file contents:

![searching for files with fuzzy search and content previewing](/images/nvim-fuzzy-find.png)

### What About Refactoring?

And what about the other killer feature of IntelliJ, refactoring? You get that
too. Now this all depends on your language and the plugins (as does a lot of
what I've mentioned above). But your typical languages are supported including
[Rust](https://www.rust-lang.org/) which I've been spending a lot of time with
(as you might know from reading my other recent blogs). What does differ though
is the amount of supported refactorings per language. I've compared Java and
Rust a bit, and there is more you can do with Java from what I can tell. I
haven't done an exhaustive test but Rust is still not as feature rich. That
said, JetBrains Rust IDE [RustRover](https://www.jetbrains.com/rust/) which I've
been using a lot over the last 6--9 months also struggles with some refactorings
(but it's still in Beta).

In Neovim I can do a rename --- `<leader>cr` --- in both Java and Rust for
example. But I can do an 'extract constant' refactoring in Java ( `<leader>cxc`
but not in Rust. There are also differences in what the key mapping is, out of
box, between languages. For example, to do an 'extract variable' in Java it
follows the pattern for 'extract constant' with a `v` instead of a `c` as you'd
expect --- `<leader>cxv`. With Rust I got to it via a 'source action' popup menu
...

![extract variable refactoring in Rust](/images/nvim-extract-var.png)

In the above, I had my cursor on a integer literal `65` and via `<leader>ca` I
got this popup which provided some options of what to do with `65`.

I can do some code generation with Java but not Rust ...

![Java code generation](/images/nvim-code-actions.png)

though the actions for Java are different for 'code actions' vs 'source actions'
even though the popup dialog has the same title for a 'source action' above
`<leader>cA` vs a 'code action' below `<leader>ca`. There's also some overlap,
strangely (e.g. the last option in both, "Change modifiers to final where
possible" ... a refactoring I approve of!).

![additional code generation](/images/nvim-codegen.png)

## What's the Verdict?

Is Neovim on par with JetBrains' IDEs like IntelliJ and RustRover or other IDEs
like Eclipse or VS Code or whatever GUI-based IDE?

What about the perhaps simpler question whether Neovim is even an **I**DE?

And will I switch to Neovim?

In part the answers to these questions, particularly the parity question, could
come down to simple preference. It somewhat reminds me of the Vi vs Emacs
question many had and probably still have. Some people just like the terminal.
Some (younger) people don't even know why a terminal is called a terminal or
even that it's not really a terminal at all but an emulator of one. Depending on
what you're building, a terminal-based IDE might not be a good thing since it
can only be "integrated" with text and you don't have any WYSIWYG kind of output.
On the other hand, some "backend" developers or systems software (kernel,
embedded) are using terminals almost exclusively in part because in some
situations/environments you can only use a terminal (emulator).

So, what about me? To some extent using Neovim is nostalgic, since when I
started, as I mentioned, all I had was Vi (I never got into Emacs though I've
used it). So being able to use Neovim and being productive and not having to use
any other IDE makes me feel good. And with themes and [(nerd) fonts](https://www.nerdfonts.com/)
and other such things (e.g. status line plugins) you can make it look as good as
a GUI.

![nvim status line](/images/nvim-status-line.png)

What I need to do is spend some time adjusting the key bindings because some of
them are too verbose for me. For example, with debugging in IntelliJ and
RustRover (and JetBrains' other IDEs) I can step into with `F7` and step over
with `F8` vs `<leader>di` and `<leader>dO`... so one key vs 3 or four. The other
benefit of remapping some of these key sequences beyond KISS is my muscle memory.
As I've been using JetBrains' IDEs and IntelliJ in particular for over 20 years
I'm used to using certain keys for certain actions and having to learn and
remember new key mappings is one of the reasons I'm currently not as productive
in Neovim as I am in IntelliJ/RustRover (and WebStorm, GoLand, CLion).

I also need to do some key remapping for some of those currently painful
differences I mentioned between the language plugins features so the same
sequence initiates the same action no matter the language (to the extent
possible given language differences ... no need for "extract superclass" in Rust).

So may answer to will I switch is ... stay tuned. 😃

------------------------------------------------------------------------

Curious about what my Neovim config is that I showed above. It's
currently mostly out-of-the-box [LazyVim](https://www.lazyvim.org/).
I've done a little customization so far e.g. to add language plugins for things
like Java and Rust and setting the theme. You can take a look at it in [GitHub](https://github.com/raysuliteanu/dotfiles).
