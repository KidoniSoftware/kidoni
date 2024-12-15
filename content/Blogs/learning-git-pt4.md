---
title: Learning Git Internals with Rust
description: Part 4 - cat-file
created: 08-25-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: true
---

In this post we'll cover the Git `cat-file`{.markup--code
.markup--p-code} command. Previous posts in this series are

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object
- [Part 3](learning-git-pt3) — refactoring

The Git [`cat-file`{.markup--code
.markup--p-code}](https://git-scm.com/docs/git-cat-file){.markup--anchor
.markup--p-anchor data-href="<https://git-scm.com/docs/git-cat-file>"
rel="noopener" target="\_blank"} command let's you dump the contents of a
Git object. You cannot view Git object files directly since they are
compressed as well as having headers, as we saw in the second post on
`hash-object`{.markup--code .markup--p-code}. The
`cat-file`{.markup--code .markup--p-code} command is essentially the
inverse of the `hash-object`{.markup--code .markup--p-code} command.

With `cat-file`{.markup--code .markup--p-code} you have four primary
options with respect to viewing the file:

- [pretty-print the content --- the `-p`{.markup--code
  .markup--li-code} command-line option]{#a3c2}
- [print the type of the object --- the `-t`{.markup--code
  .markup--li-code} command-line option]{#e63d}
- [print the size of the object --- the `-s`{.markup--code
  .markup--li-code} command-line option]{#89f1}
- [check for the existence of the object --- the `-e`{.markup--code
  .markup--li-code} command-line option]{#3947}

Each option is exclusive of the others --- you can only specify one. I
will show how this is achieved using `clap`{.markup--code
.markup--p-code} (well, one way). There are other things you can do,
such as batch (i.e. bulk) operations, but I will not cover that in this
post. You can learn more
[here](https://git-scm.com/docs/git-cat-file#_batch_output){.markup--anchor
.markup--p-anchor
data-href="<https://git-scm.com/docs/git-cat-file#_batch_output>"
rel="noopener" target="\_blank"}.

### Handling the command-line options {#e9e2 .graf .graf--h3 .graf-after--p name="e9e2"}

#### Preparatory Work {#502a .graf .graf--h4 .graf-after--h3 name="502a"}

As mentioned, the `-e`{.markup--code .markup--p-code} option just tests
for the existence of the object and the process return code should be 0
if found, 1 if there's a problem --- standard Unix. At the same time I
wanted to keep the details local to the command, and have the
`main()`{.markup--code .markup--p-code} method be ignorant. There was
also some code duplication creeping in with respect to the error
handling, so what I have done is included the [`thiserror`{.markup--code
.markup--p-code}](https://docs.rs/thiserror/latest/thiserror/){.markup--anchor
.markup--p-anchor
data-href="<https://docs.rs/thiserror/latest/thiserror/>" rel="noopener"
target="\_blank"} crate, and defined my own error enum:

<figure id="b718" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>new Result and Error types</figcaption>
</figure>

So far the commands I have implemented have only had two
errors --- either an underlying I/O error (e.g. couldn't open a file) or
something wrong with the provided object id from the user. The
`thiserror`{.markup--code .markup--p-code} crate makes it easy to define
custom error types. I [wrote a
blog](https://medium.com/dev-genius/improving-your-error-handling-in-rust-5d348a6d9286){.markup--anchor
.markup--p-anchor
data-href="<https://medium.com/dev-genius/improving-your-error-handling-in-rust-5d348a6d9286>"
target="\_blank"} on it, so I won't go into details here. Check it out if
you like.

For convenience I also created some type aliases for custom
`Result`{.markup--code .markup--p-code} types, rather than using the
`std::io::Result`{.markup--code .markup--p-code} everywhere as I had
been doing.

The `main()`{.markup--code .markup--p-code} method changed to have the
return type be `std::process::ExitCode`{.markup--code .markup--p-code}
and I return the exit code explicitly based on the result.

<figure id="9936" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>updated main()</figcaption>
</figure>

I then changed all the return signatures from the various command
handlers to return `GitCommandResult`{.markup--code .markup--p-code}
e.g.

```{#fa97 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="rust"}
pub(crate) fn cat_file_command(args: CatFileArgs) -> GitCommandResult {
...
```

> At some point I will probably refactor these command entry points such
> that there is a trait for a command, to make it explicit that each
> handler should take `args`{.markup--code .markup--blockquote-code} and
> return a `GitCommandResult`{.markup--code .markup--blockquote-code}
> but it's not worth it at this point.

I also went through and pretty much everywhere replaced
`io::Result`{.markup--code .markup--p-code} with
`GitResult`{.markup--code .markup--p-code}.

#### Clap Changes {#e5e5 .graf .graf--h4 .graf-after--p name="e5e5"}

With that work out of the way, I updated the `CatFileArgs`{.markup--code
.markup--p-code} struct so that the `-e/-p/-s/-t`{.markup--code
.markup--p-code} options were mutually exclusive. To do this in
`clap`{.markup--code .markup--p-code} you can use groups. One way to do
that is to add a `group`{.markup--code .markup--p-code} option to the
`#[arg]`{.markup--code .markup--p-code} definition as so:

<figure id="68ba" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>enhanced CatFileArgs struct</figcaption>
</figure>

Here I added `group = "operation"`{.markup--code .markup--p-code} to
group these mutually exclusive options together. You can read more about
the `clap`{.markup--code .markup--p-code} group support
[here](https://docs.rs/clap/latest/clap/_derive/_tutorial/chapter_3/index.html#argument-relations){.markup--anchor
.markup--p-anchor
data-href="<https://docs.rs/clap/latest/clap/_derive/_tutorial/chapter_3/index.html#argument-relations>"
rel="noopener" target="\_blank"}. As you may have noticed if you read the
earlier blogs, I also added doc comments for each struct field. This is
one way to tell `clap`{.markup--code .markup--p-code} what to use to
print the help text. Here I just copied the text from the Git
`cat-file`{.markup--code .markup--p-code} help text.

### Pretty-Print Option {#a184 .graf .graf--h3 .graf-after--p name="a184"}

All of the options require the same up front work ... finding the object
based on the object id and reading it. At that point, the options for
existence, type and size are trivial. For existence, we don't even need
to read the file --- we just need to see if we can find it. So I short
circuit that in the `cat_file_command()`{.markup--code .markup--p-code}

<figure id="b083" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>short circuit with -e option</figcaption>
</figure>

If it's not the `-e`{.markup--code .markup--p-code} option, then I read
the file. At that point, the only interesting thing is printing the
content. For the size and type options, I just print those values.

<figure id="d6cd" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>handling cat-file command line options</figcaption>
</figure>

So let's focus on the pretty-printing. Here, the `blob`{.markup--code
.markup--p-code} and `commit`{.markup--code .markup--p-code} types are
the same and trivial --- the content is just printed out. Where it gets
more involved is handling the `tree`{.markup--code .markup--p-code}
object. This is because each entry in the tree object is variable length
and so the overall object size is variable length.

Each entry of the tree object contains the file permissions (standard
Unix `mode`{.markup--code .markup--p-code} octal format) and a filename.
The filename makes the row and resulting full Git object variable
length. The file name is terminated by a null-byte and then there's the
20-byte object hash:

```{#e48c .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="plaintext"}
[filemode][SP][filename]\0[hash-bytes]<repeat>
```

The pretty-printed output of a tree object looks like

```{#828d .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git cat-file -p 897d5c0a70cdd0bbc115d30ca9bbb6f1dc361268                                                                                                                                                           1 ↵
100644 blob 25eaa3bf19c719f454216e163cf0a072c6393783    .gitignore
100644 blob 02e4d202dcf03fcb985fcebe0af2c01b81b65f29    .gitmodules
100644 blob 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64    LICENSE
100644 blob b0b9c6aa63576d05442ee254a9563c64286ff079    README.md
```

Note that the output contains the object type (second column), but
that's not part of the content of the tree object entries themselves. So
we have to look up each given object to find the object type, to be able
to properly output each row.

Here's the full implementation:

<figure id="e47c" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>parsing and printing the tree object</figcaption>
</figure>

The code iterates through the `content`{.markup--code .markup--p-code}
buffer, maintaining an index `consumed`{.markup--code .markup--p-code}
as data gets parsed. First the file mode and name is found by first
finding the null byte to find the end of the file name and then
splitting that on the `b' '`{.markup--code .markup--p-code} separator.
Next (line 14) the object id gets parsed. Given the object id, the code
looks up the object to get the object type. The extracted tree info is
printed to `stdout`{.markup--code .markup--p-code}. Repeat while there
is still content.

This is a pretty straightforward, brute-force approach. Could it be
optimized? Perhaps. In particular, extracting the object type currently
requires reading the entire referenced object (line 17) so it can parse
the header; the rest of the object content is discarded.

That said, this implementation of the `cat-file`{.markup--code
.markup--p-code} command works for `blob`{.markup--code
.markup--p-code}, `commit`{.markup--code .markup--p-code} and
`tree`{.markup--code .markup--p-code} objects and the `-e`{.markup--code
.markup--p-code}, `-s`{.markup--code .markup--p-code},
`-t`{.markup--code .markup--p-code} and `-p`{.markup--code
.markup--p-code} options.
:::
:::
:::

::: {#2e92 .section .section .section--body}
::: section-divider

---

:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
Depending on how you might try this out given the current
implementation, you might find the code unable to find an object you
specify or one that's referenced in a `tree`{.markup--code
.markup--p-code} object ...

```{#7972 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ rust-git cat-file -p 25eaa3bf19c719f454216e163cf0a072c6393783
Not a valid object name 25eaa3bf19c719f454216e163cf0a072c6393783
```

And in fact if I look in .git/objects there is no such file

```{#21b2 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="bash"}
$ ls .git/objects/25/eaa3bf19c719f454216e163cf0a072c6393783                                                                                                                                                          2 ↵
".git/objects/25/eaa3bf19c719f454216e163cf0a072c6393783": No such file or directory (os error 2)
```

This particular object was "packed" up into a pack file.

```{#86b3 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git verify-pack -v .git/objects/pack/pack-ba0faee43dc0116b7966fe1beae5c44f29ca0779.idx|grep 25eaa3bf19c719f454216e163cf0a072c6393783                                                                             130 ↵
25eaa3bf19c719f454216e163cf0a072c6393783 blob   38 51 57043 1 0fc92519924a0af1fa2fb5fdbe03cc3904812a8e
```

Also, if you try other Git ways to specify objects like for example with
`HEAD`{.markup--code .markup--p-code} or such human-readable names, my
code doesn't work

```{#ae07 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ rust-git cat-file -p HEAD
Not a valid object name HEAD
```

Why? Well, it's not smart enough yet :). The first issue with using the
object hash has to do with how Git optimizes space with ["pack"
files](https://git-scm.com/book/en/v2/Git-Internals-Packfiles){.markup--anchor
.markup--p-anchor
data-href="<https://git-scm.com/book/en/v2/Git-Internals-Packfiles>"
rel="noopener" target="\_blank"}. The issue with something like
`HEAD`{.markup--code .markup--p-code} has to do with the notion of
references which I mentioned in the [first
post](https://medium.com/gitconnected/learning-git-internals-with-rust-96d05592b902){.markup--anchor
.markup--p-anchor
data-href="<https://medium.com/gitconnected/learning-git-internals-with-rust-96d05592b902>"
target="\_blank"}. If you recall, something like `HEAD`{.markup--code
.markup--p-code} is actually a file
in `.git/refs/heads/<branch-name>`{.markup--code .markup--p-code} which
then contains an object hash:

```{#778c .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ cat .git/refs/heads/more-rust-git
42b31b7976b4a199affdf1f69721bbf86ec70190
```

You can refer to the [`gitrevisions`{.markup--code
.markup--p-code}](https://git-scm.com/docs/gitrevisions){.markup--anchor
.markup--p-anchor data-href="<https://git-scm.com/docs/gitrevisions>"
rel="noopener" target="\_blank"} page to see details on this.

In the next post I will talk about pack files and enhance the
`cat-file`{.markup--code .markup--p-code} command to be able to find
packed objects. I will probably also add the support for the ref names
like `HEAD`{.markup--code .markup--p-code}.
:::
:::
:::

::: {#d51c .section .section .section--body .section--last}
::: section-divider

---

:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
As always if you have any suggestions how to improve my Rust coding
skills, please comment.

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
on [August 25, 2024](https://medium.com/p/de06a154cc7c).

[Canonical
link](https://medium.com/@raysuliteanu/learning-git-internals-with-rust-de06a154cc7c){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
