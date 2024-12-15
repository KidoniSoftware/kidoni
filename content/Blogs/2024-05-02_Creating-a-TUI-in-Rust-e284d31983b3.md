---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Creating a TUI in Rust {#creating-a-tui-in-rust .p-name}

</div>

::: {.section .p-summary field="subtitle"}
Leveraging Ratatui and Crossterm to create a simple file viewing console
app!
:::

::: {.section .e-content field="body"}
::: {#ff05 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Creating a TUI in Rust {#ca0a .graf .graf--h3 .graf--leading .graf--title name="ca0a"}

<figure id="9440" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*KuGmPzsVJ5w-21GD"
class="graf-image" data-image-id="0*KuGmPzsVJ5w-21GD" data-width="5868"
data-height="3904" data-unsplash-photo-id="X4oyg7hn8es"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@etiennegirardet?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@etiennegirardet?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Etienne Girardet</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

Way back when, before nice graphical user interfaces, all we had was the
terminal. I won't waste time with a trip down memory lane. Suffice to
say there were many cool terminal-based interfaces, and some of us still
use terminals (or terminal emulators more likely). And there are still
nice terminal-based user interfaces used by many of us, even if that's
just vim or emacs.

As I continue my journey learning Rust, I thought I'd take a stab at
writing a terminal user-interface (AKA TUI). In this case I will
leverage a Rust crate called
[ratatui](https://ratatui.rs/){.markup--anchor .markup--p-anchor
data-href="https://ratatui.rs/" rel="noopener" target="_blank"}. Ratatui
provides UI widgets for building a TUI --- things like laying out your
UI, tabs, tables, scrollbars, and the like. Ratatui focuses on the UI
aspects, and leverages other crates for the low level terminal
interaction. Several are supported, but the one I chose (and the most
common?) is called
[Crossterm](https://github.com/crossterm-rs/crossterm){.markup--anchor
.markup--p-anchor data-href="https://github.com/crossterm-rs/crossterm"
rel="noopener" target="_blank"}. I am going to focus here more on
Ratatui then Crossterm, except as needed.

> Please note --- in this blog I may use "terminal" and "console"
> interchangeably. For someone who's been around a bit like me, a
> console is a terminal, not something you play video games on. :)

To showcase Ratatui (and Crossterm) I am going to create a simple text
file "viewer" --- a TUI to display a text file and scroll around. The
TUI will have a header and a footer and support some keyboard input for
scrolling. In the future I might expand on this example to add features
like syntax highlighting, large file support (right now I just load the
full file without regard to file size), mouse support, etc. This first
cut though will be simple (or simplistic depending on how you look at
it).

Here is a screenshot of the finished TUI ---

<figure id="14a9" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*Dktzag6cffVz0uanzDSfzw.png"
class="graf-image" data-image-id="1*Dktzag6cffVz0uanzDSfzw.png"
data-width="2829" data-height="1625" />
<figcaption>Simple File Viewer TUI</figcaption>
</figure>

The file name is displayed in the top left. There is a scroll bar on the
right. And there is a footer with some keyboard commands in the bottom
left and some file metadata on the bottom right.

Enough intro, let's get coding ....

### Creating the project {#248d .graf .graf--h3 .graf-after--p name="248d"}

Using `cargo`{.markup--code .markup--p-code} let's create a project and
add some dependencies.

``` {#731e .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ cargo new fileviewer-tui
$ cd fileviewer-tui
```

Rather than showing all the `cargo add`{.markup--code .markup--p-code}
commands for the required dependencies, here's the list (current
versions may vary depending on when you read this of course):

``` {#0e44 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="ini"}
[dependencies]
ratatui = "0.26.1"
crossterm = { version = "0.27.0", features = ["serde", "event-stream"] }
tokio = { version = "1.37.0", features = ["time", "macros", "rt"] }
tokio-util = { version = "0.7.10", features = ["rt"] }
futures = "0.3.30"
serde = { version = "1.0.197", features = ["derive"] }
serde_derive = "1.0.197"
chrono = "0.4.37"
signal-hook = "0.3.17"
```

The main requirements are the first two, `ratatui`{.markup--code
.markup--p-code} and `crossterm`{.markup--code .markup--p-code} but as
you'll see later, I'm leveraging an example from the Ratatui
documentation to set up a generic, application-independent async console
event handling capability that allows separation between console events
and application code. The console events are handled and sent to the
application code (the TUI itself) over an event channel asynchronously
using `tokio`{.markup--code .markup--p-code} .

As such, the structure of our example application is

<figure id="bc94" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*sgSBdvURViMrcwVLMATubg.png"
class="graf-image" data-image-id="1*sgSBdvURViMrcwVLMATubg.png"
data-width="399" data-height="460" />
<figcaption>Application Structure</figcaption>
</figure>

### Understanding Terminal Interaction {#8f87 .graf .graf--h3 .graf-after--figure name="8f87"}

When a user is interacting with a terminal session with a keyboard,
while the keys pressed may be "echoed" and shown in the terminal,
nothing is "really" happening until you press the
`<enter>`{.markup--code .markup--p-code}key. The terminal is in a
line-oriented/buffered mode. Fancy terminals (again, really terminal
emulators) and shells may do things like suggesting command completion,
but even so, nothing actually is run until you press
`<enter>`{.markup--code .markup--p-code}.

But in a TUI, you don't want to have to hit enter after every action you
want to take. Imagine if you want to "page down" having to press
`<page down><enter>`{.markup--code .markup--p-code} or to move up or
down a line having to do something like
`<up arrow><enter>`{.markup--code .markup--p-code} --- what a pain that
would be. So one thing that needs to happen is to tell the terminal to
switch to a mode where every keystroke should be presented to the TUI
immediately. This is called "raw" mode. At the same time, you need to be
sure to switch back to the buffered mode when your TUI exits (or
crashes!).

### Crossterm {#1df2 .graf .graf--h3 .graf-after--p name="1df2"}

This is where Crossterm comes in --- plus much more of course. Crossterm
handles the details of working with terminals, and multiple types of
terminals (hence the name). In our TUI, as part of the initialization,
we use Crossterm to switch into this immediate mode we want for our TUI.
We also set up a hook to ensure if our TUI panics, the terminal is reset
properly and not left in a weird state.

All the Crossterm code is contained/encapsulated in
`src/tui.rs`{.markup--code .markup--p-code} (or mostly --- I have a
dependency in `src/main.rs`{.markup--code .markup--p-code} on a
Crossterm enum which I could clean up). In `tui.rs`{.markup--code
.markup--p-code} we have a `struct Tui`{.markup--code .markup--p-code}
that exposes an API with methods like

-   [start/stop]{#73d0}
-   [enter/exit]{#1766}
-   [suspend/resume]{#291e}

It also exposes terminal events like an Iterator by providing a
`next()`{.markup--code .markup--p-code} method (more on that later).

> As I mentioned earlier, this Tui struct is taken from the Ratatui
> documentation
> [here](https://ratatui.rs/how-to/develop-apps/terminal-and-event-handler/){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://ratatui.rs/how-to/develop-apps/terminal-and-event-handler/"
> rel="noopener" target="_blank"}.

To switch into the raw mode, the Tui struct exposes the
`enter()`{.markup--code .markup--p-code} method, wrapping Crossterm
functions:

<figure id="93ba" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Line 2 is the key line, calling `enable_raw_mode()`{.markup--code
.markup--p-code}. The Tui struct contains support for copy/paste and
mouse interaction as configurable options which by default are off (and
not currently used in my example app).

The `enter()`{.markup--code .markup--p-code} method also calls the
`start()`{.markup--code .markup--p-code} method on the Tui struct. This
method sets up and starts the async event loop, spawning a thread using
Tokio, handling events from Crossterm and making them available to the
application over an event channel (there's a diagram later). Rather than
creating a gist of the entire `start()`{.markup--code .markup--p-code}
method, just look at it
[here](https://github.com/raysuliteanu/blog-examples/blob/3c0dcbca2fec3d623da1196181dd90d5e78bb92d/rust-tui-example/src/tui.rs#L86){.markup--anchor
.markup--p-anchor
data-href="https://github.com/raysuliteanu/blog-examples/blob/3c0dcbca2fec3d623da1196181dd90d5e78bb92d/rust-tui-example/src/tui.rs#L86"
rel="noopener" target="_blank"} in GitHub (where you can see the [full
example
code](https://github.com/raysuliteanu/blog-examples/tree/main/rust-tui-example){.markup--anchor
.markup--p-anchor
data-href="https://github.com/raysuliteanu/blog-examples/tree/main/rust-tui-example"
rel="noopener" target="_blank"} as well).

### FileViewer With Ratatui {#4715 .graf .graf--h3 .graf-after--p name="4715"}

Since I said I was going to focus on Ratatui and not Crossterm, let's
switch now and focus on our user functionality.

As with any UI framework, laying out the widgets is a big part of the
task, and getting it right can be difficult. Ratatui exposes layout
"controls" similar to other frameworks, whether it's a web framework or
a desktop framework. Within the layout(s) you set up various "blocks" to
hold components like "paragraph" or "text" and various properties like
margins and padding and text styles (color, font, etc). Here is a sketch
of the UI layout

<figure id="03c7" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*IVfZK8Yrd9KAnIuan2PZlQ.png"
class="graf-image" data-image-id="1*IVfZK8Yrd9KAnIuan2PZlQ.png"
data-width="1075" data-height="549" />
<figcaption>FileViewer layout sketch</figcaption>
</figure>

Setting up the Ratatui UI as shown in the sketch can be seen in the
`ui()`{.markup--code .markup--p-code} method in
`src/main.rs`{.markup--code .markup--p-code} :

<figure id="dc56" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Anyone who has worked with UI frameworks can make sense of a lot of
this, just adjusting to the terminology used by Ratatui and the
available widgets. To call a few things out

-   [Lines 4--10: this sets up the main two blocks --- the main file
    viewing block and the footer block. Calling
    `split(area)`{.markup--code .markup--li-code} on line 10 gives us an
    array to access each block later.]{#c2ab}
-   [Lines 14--23: fills out the main block with the file content we
    loaded as part of the app initialization. It sets the block title to
    the filename and we set the current scroll position. As noted in the
    comment on line 22, we need to make sure whitespace isn't stripped
    out from the file to preserve indenting.]{#f918}
-   [Lines 25--33: a scrollbar widget is considered a stateful widget in
    Ratatui. We create the scrollbar as a vertical scrollbar on the
    right of the screen, and we provide a place for Ratatui to store the
    scrollbar state (line 32).]{#b0ca}
-   [The rest of the method sets up the footer, with paragraph widgets
    on either end of the footer block.]{#c562}

Ok, so we have our UI constructed, now what? Who calls this
`ui()`{.markup--code .markup--p-code} method and how do we interact with
the app?

First let's show the app-specific struct that is passed to the
`ui()`{.markup--code .markup--p-code} method, used to store and display
the file content.

<figure id="f80f" class="graf graf--figure graf--iframe graf-after--p">

</figure>

-   [line 2: path to the file to view, specified on the terminal command
    line when launching the app (e.g.
    `$ fileviewer src/main.rs`{.markup--code .markup--li-code} ) to
    display in the main block as shown earlier]{#f814}
-   [line 3: a vector containing Ratatui `Line`{.markup--code
    .markup--li-code} widgets holding the file data to display in the
    main paragraph (line 19 of the earlier gist)]{#5fe6}
-   [line 4: `std::fs::Metadata`{.markup--code .markup--li-code} for the
    footer content]{#b38a}
-   [line 5: which `Line`{.markup--code .markup--li-code} in the
    `data`{.markup--code .markup--li-code} vector is the current
    line]{#63cf}
-   [line 6: the aforementioned scrollbar state using
    `ratatui::widgets::scrollbar::ScrollbarState`{.markup--code
    .markup--li-code}]{#9e3f}
-   [line 7: a flag indicating the user wants to quit the app]{#7ebb}

Moving on to the main application processing loop (as opposed to the
`struct Tui`{.markup--code .markup--p-code} terminal event processing
loop discussed earlier), we repeatedly update the UI and handle events
until the user presses `Q/q`{.markup--code .markup--p-code} or
`ESC`{.markup--code .markup--p-code}

<figure id="9450" class="graf graf--figure graf--iframe graf-after--p">

</figure>

This is in the `main()`{.markup--code .markup--p-code} function in
`src/main.rs`{.markup--code .markup--p-code} . (On either side of the
loop shown here is where the Tui struct is created and
`enter()`{.markup--code .markup--p-code} and `exit()`{.markup--code
.markup--p-code} are called.) So what's going on here?

-   [lines 3--5: (re)draw the UI periodically to refresh what the user
    sees. (This is controlled by some properties on
    `struct Tui`{.markup--code .markup--li-code} called tick rate and
    refresh rate.)]{#42c5}
-   [line 7: now that we have the UI drawn/updated, let's block until we
    have some terminal event. Recall from earlier I mentioned that
    `struct Tui`{.markup--code .markup--li-code} implemented
    `next()`{.markup--code .markup--li-code} . This calls
    `recv()`{.markup--code .markup--li-code} on a Tokio
    `UnboundedChannel`{.markup--code .markup--li-code} to get messages
    sent by the terminal event processing thread, which itself gets
    events from Crossterm.]{#336d}

<figure id="59b1" class="graf graf--figure graf-after--li">
<img
src="https://cdn-images-1.medium.com/max/800/1*qjHOYHruhSBS0hPWxeFs1w.png"
class="graf-image" data-image-id="1*qjHOYHruhSBS0hPWxeFs1w.png"
data-width="819" data-height="259" />
<figcaption>event handling</figcaption>
</figure>

-   [lines 8--11: when we have a `tui::Event`{.markup--code
    .markup--li-code} we call `handle_event()`{.markup--code
    .markup--li-code} to turn the `tui::Event`{.markup--code
    .markup--li-code} into our own file viewing app event type,
    discarding any events we don't care about. Then we perform any state
    update we need to perform. This is done in a while loop because it's
    possible that one state change causes another, but in the current
    implementation that doesn't happen, so that while loop is
    technically superfluous.]{#1b91}
-   [lines 14--16: one possible state change is that the user pressed
    the `q/Q/ESC`{.markup--code .markup--li-code} key and so the
    `quit`{.markup--code .markup--li-code} flag was set to true, in
    which case we exit the loop and the file viewer app. Another
    possible state change is that the user did some scrolling up or
    down, in which case `FileData.vertical_scroll`{.markup--code
    .markup--li-code} was changed. When we go back to the beginning of
    the loop to line 4, the UI will be refreshed and the view position
    of the main paragraph will get updated.]{#083f}

The `handle_event()`{.markup--code .markup--p-code} and
`update()`{.markup--code .markup--p-code} methods are pretty basic
things, and I suggest looking at the
[main.rs](https://github.com/raysuliteanu/blog-examples/blob/main/rust-tui-example/src/main.rs){.markup--anchor
.markup--p-anchor
data-href="https://github.com/raysuliteanu/blog-examples/blob/main/rust-tui-example/src/main.rs"
rel="noopener" target="_blank"} file if you're interested, rather than
elaborating on them here.

### Wrapping Up {#a406 .graf .graf--h3 .graf-after--p name="a406"}

There are many things I can still do to this basic first cut at a simple
file viewing TUI, as I mentioned at the start. But this was a good
learning experience for me, in several different Rust crates and I hope
it was interesting to you as well! If you enjoyed it, please let me
know! If you have any suggestions are particularly any specific Rust
aspects where I've exposed my rookie Rust knowledge, let me know that
too!

Claps are appreciated and feel free to [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="https://www.buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"}!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [May 2, 2024](https://medium.com/p/e284d31983b3).

[Canonical
link](https://medium.com/@raysuliteanu/creating-a-tui-in-rust-e284d31983b3){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
