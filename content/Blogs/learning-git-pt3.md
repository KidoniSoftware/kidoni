---
title: Learning Git Internals with Rust
description: Part 3 - Rust refactoring
date: 08-20-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: true
---

In this post we continue our journey with Rust and Git. If you haven't
read the previous posts, you can find them here

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object

> At the end of Part 2 I said the next blog would be on
> `cat-file`{.markup--code .markup--blockquote-code}. Sorry for the bait
> and switch, but I wanted to do this refactoring, so I snuck this in.
> We'll definitely get to `cat-file`{.markup--code
> .markup--blockquote-code} next time.

While this post is mostly standalone, there are aspects of the prior
posts that will probably help to understand this post better.

This series is about Rust as much as Git, since my purpose is to learn
Rust, more so than to learn Git. So in this post, what I'm going to do
is take my single `main.rs`{.markup--code .markup--p-code} file and
refactor it into several files. I will create a `commands`{.markup--code
.markup--p-code} module, and move each implemented command into a
separate module within `commands`{.markup--code .markup--p-code}. I will
also separate out utility functions into a `util`{.markup--code
.markup--p-code} module.

<figure id="384a" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*OhQjPz-I_nmLBZOBpJkl9A.png"
class="graf-image" data-image-id="1*OhQjPz-I_nmLBZOBpJkl9A.png"
data-width="736" data-height="531" />
<figcaption>refactored into modules</figcaption>
</figure>

The directory structure becomes

<figure id="c7b6" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*OI_pZ-tl0qjDw6gjHLkohA.png"
class="graf-image" data-image-id="1*OI_pZ-tl0qjDw6gjHLkohA.png"
data-width="234" data-height="213" />
<figcaption>module directory structure</figcaption>
</figure>

The `main()`{.markup--code .markup--p-code} method becomes extremely
basic (`use`{.markup--code .markup--p-code} statements elided).

<figure id="357f" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>refactored main.rs</figcaption>
</figure>

You could argue --- based on my module diagram above --- that the
`mod util`{.markup--code .markup--p-code} belongs in
`commands/mod.rs`{.markup--code .markup--p-code} which is probably
valid. I left it as it is for now, to see what other utility methods I
might have later. Depending how I embellish this as I work on these
blogs, I might move it.

The `util.rs`{.markup--code .markup--p-code} file now has the common
functions --- functions that are not specific to any one command. Most
of the functions are exposed as `pub(crate)`{.markup--code
.markup--p-code} but a few are private to the `util`{.markup--code
.markup--p-code} module. Rather than embedding the file here, you can
[view it on
GitHub](https://github.com/raysuliteanu/blog-examples/blob/f29760510562a12d9590601e6ba415e3b9ae82a8/rust-git/src/util.rs){.markup--anchor
.markup--p-anchor
data-href="<https://github.com/raysuliteanu/blog-examples/blob/f29760510562a12d9590601e6ba415e3b9ae82a8/rust-git/src/util.rs>"
rel="noopener" target="\_blank"}.

The `commands`{.markup--code .markup--p-code} module defined in
`commands/mod.rs`{.markup--code .markup--p-code} is also relatively
simple at this point. Other than defining the other command modules, it
has the `struct Git`{.markup--code .markup--p-code} and
`enum Commands`{.markup--code .markup--p-code} types.

<figure id="de9e" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>commands module file</figcaption>
</figure>

Then as shown above, we have a file for each command module. Each module
has the implementation details for the specific command, moved from the
old `main.rs`{.markup--code .markup--p-code}. I will not replicate the
code here, but you can [view it on
GitHub](https://github.com/raysuliteanu/blog-examples/tree/main/rust-git/src/commands){.markup--anchor
.markup--p-anchor
data-href="<https://github.com/raysuliteanu/blog-examples/tree/main/rust-git/src/commands>"
rel="noopener" target="\_blank"}.

Each file/module follows the same pattern --- basically the struct for
the command's arguments and a `pub(crate)`{.markup--code
.markup--p-code} function called by `main()`{.markup--code
.markup--p-code} with any additional private functions needed by that
handler function, if any, since most are in the `util`{.markup--code
.markup--p-code} module. There are some functions in some of the command
modules which could be moved to `util`{.markup--code .markup--p-code}
since they are completely generic and not specific to Git, but if
they're only used (currently) by one command I've left them in that
command module.

The `hash_object`{.markup--code .markup--p-code} command is one example.
The `generate_hash()`{.markup--code .markup--p-code} and
`encode_obj_content()`{.markup--code .markup--p-code} methods are
completely generic, but I've left them where they are for now.

<figure id="b7c4" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>private functions in hash_object.rs</figcaption>
</figure>

That about covers the refactoring. Now we'll get back to Git ... next
blog will cover the `cat-file`{.markup--code .markup--p-code} command as
I had indicated in Part 2.
:::
:::
:::

::: {#39bf .section .section .section--body .section--last}
::: section-divider

---

:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
As always, please comment if you notice anything I could do better with
my Rust coding as I'm doing this to learn Rust better. If there are
idiomatic things that I could do that I'm not, let me know! And any
other comments on the content or possible future content, let me know!

Please clap and/or follow and/or [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="<https://www.buymeacoffee.com/raysuliteanu>"
rel="noopener ugc nofollow noopener" target="\_blank"} if you liked this
blog. Thanks!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [August 20, 2024](https://medium.com/p/09aa49320a81).

[Canonical
link](https://medium.com/@raysuliteanu/learning-git-internals-with-rust-09aa49320a81){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
