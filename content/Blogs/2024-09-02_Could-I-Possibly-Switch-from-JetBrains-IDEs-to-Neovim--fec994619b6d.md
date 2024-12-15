---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Could I Possibly Switch from JetBrains IDEs to Neovim? {#could-i-possibly-switch-from-jetbrains-ides-to-neovim .p-name}

</div>

::: {.section .p-summary field="subtitle"}
Is Neovim and IDE on par with JetBrains' IDEs and other GUI IDEs?
:::

::: {.section .e-content field="body"}
::: {#c87f .section .section .section--body .section--first}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Could I Possibly Switch from JetBrains IDEs to Neovim? {#7993 .graf .graf--h3 .graf--leading .graf--title name="7993"}

<figure id="172b" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*kMc1YtwCTbkAAwE5"
class="graf-image" data-image-id="0*kMc1YtwCTbkAAwE5" data-width="6000"
data-height="4000" data-unsplash-photo-id="XJXWbfSo2f0"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@lucabravo?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@lucabravo?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Luca Bravo</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

I have been using --- and
loving --- [JetBrains](https://www.jetbrains.com/){.markup--anchor
.markup--p-anchor data-href="https://www.jetbrains.com/" rel="noopener"
target="_blank"} [Integrated Development Environments
(IDEs)](https://www.jetbrains.com/ides/){.markup--anchor
.markup--p-anchor data-href="https://www.jetbrains.com/ides/"
rel="noopener" target="_blank"} and other tools (I like
[TeamCity](https://www.jetbrains.com/teamcity/){.markup--anchor
.markup--p-anchor data-href="https://www.jetbrains.com/teamcity/"
rel="noopener" target="_blank"} a lot!) since effectively version 1 of
[IntelliJ IDEA](https://www.jetbrains.com/idea/){.markup--anchor
.markup--p-anchor data-href="https://www.jetbrains.com/idea/"
rel="noopener" target="_blank"} since it was released in the early
2000s. Compared to the other IDEs I tried at the time like
[NetBeans](https://en.wikipedia.org/wiki/NetBeans){.markup--anchor
.markup--p-anchor data-href="https://en.wikipedia.org/wiki/NetBeans"
rel="noopener" target="_blank"},
[JBuilder](https://en.wikipedia.org/wiki/JBuilder){.markup--anchor
.markup--p-anchor data-href="https://en.wikipedia.org/wiki/JBuilder"
rel="noopener" target="_blank"} and
[Eclipse](https://en.wikipedia.org/wiki/Eclipse_%28software%29){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Eclipse_(software)"
rel="noopener" target="_blank"}, IntelliJ was just better all around.
But the really great thing that I liked about it in addition to its
overall look & feel was its **keyboard integration**. That's right,
*keyboard integration*.

Of course, there are other great things about IntelliJ --- its
**refactoring** support was (and is) superior to any other IDE then or
since, it's **Spring Framework** and then **Spring Boot** support and
integration exceeds even Spring's own [Eclipse-based Spring Tool
Suite](https://spring.io/tools){.markup--anchor .markup--p-anchor
data-href="https://spring.io/tools" rel="noopener" target="_blank"} (now
with VS Code support also. Personally I think this stems from the base
upon which it starts i.e. Eclipse.) There are many other great features
and plugins, too many to list. Let's just sum by saying I'm a big fan.

Fundamentally what it's all about is productivity. And not just
productivity writing code faster, but *writing good quality code*.
That's one reason the refactoring support is #2 after the keyboard
support for me as far as the killer feature that had me dump the other
IDEs I was trying to use to be productive. (JBuilder was my favorite
until IntelliJ which makes a little sense since it started with
[Borland](https://en.wikipedia.org/wiki/Borland){.markup--anchor
.markup--p-anchor data-href="https://en.wikipedia.org/wiki/Borland"
rel="noopener" target="_blank"} who had made a business out of good
IDEs.)

But being productive when programming is still all about typing (AI code
generation from natural language input notwithstanding ... since a lot
of that is still typed in, on a keyboard). Some examples of common
coding situations where IntelliJ and its key bindings (and refactoring)
make me so much more productive are

> Some key bindings in the examples below may differ for you depending
> on which keymap you use as well as the Mac/non-Mac
> `<cmd>`{.markup--code .markup--blockquote-code} vs
> `<ctrl-c>`{.markup--code .markup--blockquote-code} issue.

-   [smart word (keyword, variable, method/class/etc. name, etc.) and
    block selection --- using `ctrl-w`{.markup--code .markup--li-code}
    combined with the IDEs awareness of the language I can quickly
    select or deselect (`shift-ctrl-w`{.markup--code .markup--li-code})
    parts of words or code blocks. Using Java (as I will mostly
    throughout with some Rust thrown in), the IDE is "CamelCase" aware
    so I can easily select just "Camel" with one `ctrl-w`{.markup--code
    .markup--li-code} and if I want the rest I can press
    `ctrl-w`{.markup--code .markup--li-code} again and select all of
    CamelCase. If I went too far I can use `shift-ctrl-w`{.markup--code
    .markup--li-code} to undo smartly. So given say CamelCaseWord and I
    pressed `ctrl-w`{.markup--code .markup--li-code} three times to
    select the whole word, but I just wanted CamelCase selected, I can
    press `shift-ctrl-w`{.markup--code .markup--li-code} and it will
    back off to just CamelCase. If I keep pressing
    `ctrl-w`{.markup--code .markup--li-code} IntelliJ will select
    progressively larger blocks ... the current statement, the block,
    method, class, or deselect it with `ctrl-shift-w`{.markup--code
    .markup--li-code}.]{#bdbf}

> Some may say that they don't like having to press
> `ctrl-w`{.markup--code .markup--blockquote-code} two or three times in
> the above example to select the whole word, which is why you can
> enable/disable this via the IDE settings. Personally I find myself
> wanting to rename just parts of various names often that the smart
> `ctrl-w`{.markup--code .markup--blockquote-code} *makes me more
> productive*.

-   [delete the current line to the clipboard --- with
    `ctrl-y`{.markup--code .markup--li-code} I can delete the current
    line and have it go to the clipboard *without having to select the
    current line first* (perhaps in a nod to the '\[y\]ank' in (neo)vim
    though this would be more equivalent to 'dd' in vim).]{#2bd9}
-   [duplicate the current line --- similar to the above, without having
    to select the line first, `ctrl-d`{.markup--code .markup--li-code}
    will duplicate the current line.]{#60da}
-   [rename variable/method/class refactor --- just press
    `shift-F6`{.markup--code .markup--li-code}]{#bd1b}
-   [extract method or variable refactor --- just press
    `ctrl-alt-m`{.markup--code .markup--li-code} or
    `ctrl-alt-v`{.markup--code .markup--li-code}]{#b264}
-   [extract constant refactoring --- say you have
    `log.info("{} ...", "YADA")`{.markup--code .markup--li-code} and you
    use `“YADA”`{.markup--code .markup--li-code} a lot. Just have your
    cursor somewhere in that string, and press
    `ctrl-alt-c`{.markup--code .markup--li-code} and you'll get a
    constant with default name the same as the string, and a prompt for
    you to change the name or accept the generated one. You can also
    decide to replace all such occurrences elsewhere in the file all at
    once at the same time.]{#ed6e}
-   [copy/move class/method/constant --- `F5`{.markup--code
    .markup--li-code}/`F6`{.markup--code .markup--li-code}]{#ca0a}
-   [create test class --- `ctrl-shift-t`{.markup--code
    .markup--li-code} will create a new test class (e.g. in Java) in the
    correct Java package, in the correct directory (e.g.
    src/test/java/package/name) with the correct boilerplate.]{#5515}
-   ["surround with" --- let's say you wrote some code and you realize
    you should have an if/else block around it;
    press --- `ctrl-alt-t`{.markup--code .markup--li-code} and a popup
    menu will show alternatives like surround with if, if/else, try,
    while, synchronized, etc.]{#8ce1}

I could go on and on. Find usages, show inheritance hierarchy, extract
superclass/interface, setting breakpoints, building and running code,
debugging code, stepping over/info functions, evaluating expressions.
But the point is, *I don't have to take my hand off the keyboard* and
use a mouse. The context switch from keyboard to mouse and back impacts
your flow even if just slightly and therefore your productivity. The
more I can do just with the keyboard the more productive I am.

### Enter Neovim {#5b2a .graf .graf--h3 .graf-after--p name="5b2a"}

I have been using Neovim recently. Prior I was using Vim, but usually
for quick and easy things ... writing a shell script or tweaking one,
editing my various dotfiles and other relatively trivial tasks when I'm
in the terminal. And I'm old enough to have used Vi on Unix before Vim
and Linux existed. In fact, in the late 80s and 90s first in college and
then my first years as a professional, I did my C development all with
Vi. Looking back I'm very surprised how I managed! You needed a
hodgepodge of tools like man pages for docs on method signatures say,
`tags`{.markup--code .markup--p-code} to help with jumping around in
your code, or something slightly more sophisticated like
`cscope`{.markup--code .markup--p-code}. I remember at my first job
which was working on the Unix kernel for a hardware company (everyone
had their own Unix) we had "kscope" which was a shell wrapper around
`cscope`{.markup--code .markup--p-code} with a prebuilt
`cscope`{.markup--code .markup--p-code} database to help navigate the
Unix kernel. In fact, with Linux there's still a Makefile command to
build the `cscope`{.markup--code .markup--p-code} database ...

``` {#065b .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$  make cscope 
```

I must say I'm glad my `cscope`{.markup--code .markup--p-code} days are
over. These days in Linux better to create a [compilation
database](https://github.com/torvalds/linux/blob/master/scripts/clang-tools/gen_compile_commands.py){.markup--anchor
.markup--p-anchor
data-href="https://github.com/torvalds/linux/blob/master/scripts/clang-tools/gen_compile_commands.py"
rel="noopener" target="_blank"} that several IDEs support like VS Code
and CLion (from JetBrains 😄)...

``` {#3e9f .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ scripts/clang-tools/gen_compile_commands.py
```

But I never even considered switching to an editor in a terminal UI ...
I mean how could it possibly compare to IntelliJ.

Well, at least with Neovim, maybe I was wrong!

Take a look at these screenshots of my Neovim as I edit a Rust file

<figure id="c0cf" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*Ydnz1w7rAepL4jb9dUadQQ.png"
class="graf-image" data-image-id="1*Ydnz1w7rAepL4jb9dUadQQ.png"
data-width="2443" data-height="1119" />
<figcaption>Neovim editing session with documentation popup</figcaption>
</figure>

<figure id="5bfd" class="graf graf--figure graf-after--figure">
<img
src="https://cdn-images-1.medium.com/max/800/1*zmF7Sv8iV6lrt8fkKyyavA.png"
class="graf-image" data-image-id="1*zmF7Sv8iV6lrt8fkKyyavA.png"
data-width="2443" data-height="1119" />
<figcaption>Neovim interactive debugging session</figcaption>
</figure>

The first screenshot is an editing session, with the file in the "main"
middle part of the window, a directory tree on the left and a symbol
explorer tree on the right, and a documentation popup showing the docs
for the Rust type under the cursor. I opened the directory tree from the
keyboard `<leader>E`{.markup--code .markup--p-code} and I opened the
symbol tree on the left with the keyboard `<leader>cs`{.markup--code
.markup--p-code} and of course the file itself from the terminal in the
first place though naturally I could open it directly from the
editor `:e src/main.rs`{.markup--code .markup--p-code}. The
documentation popup dialog was just `K`{.markup--code .markup--p-code}.

> If you're new to (Neo)vim, the `<leader>`{.markup--code
> .markup--blockquote-code} is the key (or keys) that are the prefix to
> indicate a command sequence is starting. There are also "modes" like
> "insert" mode where you're editing content or "normal" mode which is
> the "command" mode where keys execute commands (if mapped). I think
> every key sequence I have as examples in this post are executed in
> "normal" mode. These key sequences then depend on the definition in
> your config of `<leader>`{.markup--code .markup--blockquote-code}
> which for me is the spacebar i.e. a single space. So if you have
> `<leader>cs`{.markup--code .markup--blockquote-code} this means the
> key sequence `space`{.markup--code .markup--blockquote-code} followed
> by `c`{.markup--code .markup--blockquote-code} followed by
> `s`{.markup--code .markup--blockquote-code}. This notion of a "leader"
> prefix is common in terminal apps ... e.g. `tmux`{.markup--code
> .markup--blockquote-code}

I can switch between the directory tree and the file from the keyboard
`ctrl-h`{.markup--code .markup--p-code} and `ctrl-l`{.markup--code
.markup--p-code} and the file and the symbol tree `ctrl-l`{.markup--code
.markup--p-code} and `ctrl-h`{.markup--code .markup--p-code}. I could
jump to a method or type definition from the keyboard from the file
directly `<leader>gd`{.markup--code .markup--p-code} or by navigating
the symbol tree with the normal Neovim/Vim/vi navigation keyboard
commands `hjkl`{.markup--code .markup--p-code} or `ctrl-f`{.markup--code
.markup--p-code}/ `ctrl-b`{.markup--code .markup--p-code} /
`ctrl-u`{.markup--code .markup--p-code} / `ctrl-d`{.markup--code
.markup--p-code} and even search for symbols with `/`{.markup--code
.markup--p-code}.

And when you're done editing, you can debug from the same session, as
you can see in the second screenshot. The Neovim window shows a typical
debugging UI (`<leader>du`{.markup--code .markup--p-code}) with display
of the in-scope variables, call stack on the left, the execution
controls on the bottom (step into/over, continue, etc). I can set a
breakpoint `<leader>db`{.markup--code .markup--p-code} and run with or
without arguments (`<leader>da`{.markup--code .markup--p-code} and
`<leader>dr`{.markup--code .markup--p-code} respectively). It's even
aware of different run configurations available in my Rust project so it
will have a popup dialog showing the options to run. I can step into
`<leader>di`{.markup--code .markup--p-code} a method or over or out of
it ( `<leader>dO`{.markup--code .markup--p-code} or
`<leader>do`{.markup--code .markup--p-code}).

There's also a pretty comprehensive Git integration, for example with
[LazyGit](https://github.com/jesseduffield/lazygit){.markup--anchor
.markup--p-anchor data-href="https://github.com/jesseduffield/lazygit"
rel="noopener" target="_blank"}:

<figure id="7a60" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*tVgvr9VmSGBTUdgoD5bbqQ.png"
class="graf-image" data-image-id="1*tVgvr9VmSGBTUdgoD5bbqQ.png"
data-width="2443" data-height="1119" />
<figcaption>Git via LazyGit in Neovim</figcaption>
</figure>

You can do pretty much anything here. Bringing up this view is
`<leader>gg`{.markup--code .markup--p-code} or I could look at just the
commits that were done `<leader>gc`{.markup--code .markup--p-code} or
just the Git log for the current file `<leader>gl`{.markup--code
.markup--p-code}. I can interactively stage hunks of the file
`<leader>ghs`{.markup--code .markup--p-code} or the whole buffer
`<leader>ghS`{.markup--code .markup--p-code}.

You get (or is it git 😆) the idea.

You can do other cool things like doing "structural" copies e.g.
copying/changing/deleting text within or around blocks delimited by some
characters like braces or quotes or parentheses. Given

``` {#ed8a .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="java"}
log.info("this is some message");
```

if I did `<leader>ci”`{.markup--code .markup--p-code} then Neovim would
delete the text `this is some message`{.markup--code .markup--p-code}
and then place you in insert mode after the first quote so you can then
enter the replacement text.

You can comment out blocks. You can visually select regions of text. You
can work with multiple files either as panes within the same window or
as tabs, and navigate between them with fuzzy matching (by integrating
[`fd`{.markup--code
.markup--p-code}](https://github.com/sharkdp/fd){.markup--anchor
.markup--p-anchor data-href="https://github.com/sharkdp/fd"
rel="noopener" target="_blank"} and [`fzf`{.markup--code
.markup--p-code}](https://github.com/junegunn/fzf){.markup--anchor
.markup--p-anchor data-href="https://github.com/junegunn/fzf"
rel="noopener" target="_blank"}) and improved search i.e. grep (by
integrating [`rg`{.markup--code
.markup--p-code}](https://github.com/BurntSushi/ripgrep){.markup--anchor
.markup--p-anchor data-href="https://github.com/BurntSushi/ripgrep"
rel="noopener" target="_blank"}) including previewing the file contents:

<figure id="3718" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*He-9UbvyabsV_9PRJOFXIQ.png"
class="graf-image" data-image-id="1*He-9UbvyabsV_9PRJOFXIQ.png"
data-width="1996" data-height="935" />
<figcaption>Searching for files with fuzzy filename matching and preview
of content</figcaption>
</figure>

#### What About Refactoring? {#7ce3 .graf .graf--h4 .graf-after--figure name="7ce3"}

And what about the other killer feature of IntelliJ, refactoring? You
get that too. Now this all depends on your language and the plugins (as
does a lot of what I've mentioned above). But your typical languages are
supported including [Rust](https://www.rust-lang.org/){.markup--anchor
.markup--p-anchor data-href="https://www.rust-lang.org/" rel="noopener"
target="_blank"} which I've been spending a lot of time with (as you
might know from reading my other recent blogs). What does differ though
is the amount of supported refactorings per language. I've compared Java
and Rust a bit, and there is more you can do with Java from what I can
tell. I haven't done an exhaustive test but Rust is still not as feature
rich. That said, JetBrains Rust IDE
[RustRover](https://www.jetbrains.com/rust/){.markup--anchor
.markup--p-anchor data-href="https://www.jetbrains.com/rust/"
rel="noopener" target="_blank"} which I've been using a lot over the
last 6--9 months also struggles with some refactorings (but it's still
in Beta).

In Neovim I can do a rename --- `<leader>cr`{.markup--code
.markup--p-code} --- in both Java and Rust for example. But I can do an
'extract constant' refactoring in Java ( `<leader>cxc`{.markup--code
.markup--p-code} but not in Rust. There are also differences in what the
key mapping is, out of box, between languages. For example, to do an
'extract variable' in Java it follows the pattern for 'extract constant'
with a `v`{.markup--code .markup--p-code} instead of a `c`{.markup--code
.markup--p-code} as you'd expect --- `<leader>cxv`{.markup--code
.markup--p-code}. With Rust I got to it via a 'source action' popup
menu ...

<figure id="d90d" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*m8sCiHrIq0hgCAYx_exdhg.png"
class="graf-image" data-image-id="1*m8sCiHrIq0hgCAYx_exdhg.png"
data-width="1054" data-height="420" />
<figcaption>Rust extract variable in Neovim</figcaption>
</figure>

In the above, I had my cursor on a integer literal `65`{.markup--code
.markup--p-code} and via `<leader>ca`{.markup--code .markup--p-code} I
got this popup which provided some options of what to do with
`65`{.markup--code .markup--p-code}.

I can do some code generation with Java but not Rust ...

<figure id="07b2" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*nOJQ4lf5ted4ZCzRd0v-9Q.png"
class="graf-image" data-image-id="1*nOJQ4lf5ted4ZCzRd0v-9Q.png"
data-width="1054" data-height="420" />
<figcaption>Java code actions in Neovim</figcaption>
</figure>

though the actions for Java are different for 'code actions' vs 'source
actions' even though the popup dialog has the same title for a 'source
action' above `<leader>cA`{.markup--code .markup--p-code} vs a 'code
action' below `<leader>ca`{.markup--code .markup--p-code}. There's also
some overlap, strangely (e.g. the last option in both, "Change modifiers
to final where possible" ... a refactoring I approve of!).

<figure id="8d5f" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*U885mdICaM-_AIXLi6oGgA.png"
class="graf-image" data-image-id="1*U885mdICaM-_AIXLi6oGgA.png"
data-width="1054" data-height="420" />
</figure>

### What's the Verdict? {#56b3 .graf .graf--h3 .graf-after--figure name="56b3"}

Is Neovim on par with JetBrains' IDEs like IntelliJ and RustRover or
other IDEs like Eclipse or VS Code or whatever GUI-based IDE?

What about the perhaps simpler question whether Neovim is even an
**I**DE?

And will I switch to Neovim?

In part the answers to these questions, particularly the parity
question, could come down to simple preference. It somewhat reminds me
of the Vi vs Emacs question many had and probably still have. Some
people just like the terminal. Some (younger) people don't even know why
a terminal is called a terminal or even that it's not really a terminal
at all but an emulator of one. Depending on what you're building, a
terminal-based IDE might not be a good thing since it can only be
"integrated" with text and you don't have any WYSIWYG kind of output. On
the other hand, some "backend" developers or systems software (kernel,
embedded) are using terminals almost exclusively in part because in some
situations/environments you can only use a terminal (emulator).

So, what about me? To some extent using Neovim is nostalgic, since when
I started, as I mentioned, all I had was Vi (I never got into Emacs
though I've used it). So being able to use Neovim and being productive
and not having to use any other IDE makes me feel good. And with themes
and [(nerd) fonts](https://www.nerdfonts.com/){.markup--anchor
.markup--p-anchor data-href="https://www.nerdfonts.com/" rel="noopener"
target="_blank"} and other such things (e.g. status line plugins) you
can make it look as good as a GUI.

<figure id="7731" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*UX760XBKzYSQDNO5XwqwEg.png"
class="graf-image" data-image-id="1*UX760XBKzYSQDNO5XwqwEg.png"
data-width="1440" data-height="48" />
<figcaption>Customized Neovim status line</figcaption>
</figure>

What I need to do is spend some time adjusting the key bindings because
some of them are too verbose for me. For example, with debugging in
IntelliJ and RustRover (and JetBrains' other IDEs) I can step into with
`F7`{.markup--code .markup--p-code} and step over with
`F8`{.markup--code .markup--p-code} vs `<leader>di`{.markup--code
.markup--p-code} and `<leader>dO`{.markup--code .markup--p-code}... so
one key vs 3 or four. The other benefit of remapping some of these key
sequences beyond KISS is my muscle memory. As I've been using JetBrains'
IDEs and IntelliJ in particular for over 20 years I'm used to using
certain keys for certain actions and having to learn and remember new
key mappings is one of the reasons I'm currently not as productive in
Neovim as I am in IntelliJ/RustRover (and WebStorm, GoLand, CLion).

I also need to do some key remapping for some of those currently painful
differences I mentioned between the language plugins features so the
same sequence initiates the same action no matter the language (to the
extent possible given language differences ... no need for "extract
superclass" in Rust).

So may answer to will I switch is ... stay tuned. 😃
:::
:::
:::

::: {#5f64 .section .section .section--body .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
Curious about what my Neovim config is that I showed above. It's
currently mostly out-of-the-box
[LazyVim](https://www.lazyvim.org/){.markup--anchor .markup--p-anchor
data-href="https://www.lazyvim.org/" rel="noopener" target="_blank"}.
I've done a little customization so far e.g. to add language plugins for
things like Java and Rust and setting the theme. You can take a look at
it in
[GitHub](https://github.com/raysuliteanu/configs/tree/trunk/.config/nvim){.markup--anchor
.markup--p-anchor
data-href="https://github.com/raysuliteanu/configs/tree/trunk/.config/nvim"
rel="noopener" target="_blank"}.

If you liked this post please 👏. If you want to keep up with my posts,
please follow. If you're feeling generous, [buy me a
coffee](http://buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="http://buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"} ☕️. And no matter what, have a great
day! Cheers.
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [September 2, 2024](https://medium.com/p/fec994619b6d).

[Canonical
link](https://medium.com/@raysuliteanu/could-i-possibly-switch-from-jetbrains-ides-to-neovim-fec994619b6d){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
