---
title: Learning Git Internals with Rust
description: Part 2 - Objects
date: 07-30-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: true
---

This post continues from where I left off in the first post that covered
creating a new empty repository. You can read it
[here](learning-git-pt1).
To briefly summarize the goal of this
series of posts, I am on a journey to learn Rust and for me the best way
is doing "real" stuff. In this case I'm looking at the internals of Git,
by implementing some of the many commands available.

After the first post I am able to create a new repository. Let's start
to look at what Git stores and how it does so. As we saw in the first
post, after `git init`{.markup--code .markup--p-code} we have a
directory `.git/objects`{.markup--code .markup--p-code}. Content is
stored in files under that base objects directory by using a SHA-1 hash
of the contents being stored. Git provides a command
`git hash-object`{.markup--code .markup--p-code} which allows generating
the hash based on content, and _optionally_ writing that file
to `.git/objects`{.markup--code .markup--p-code}. However, that doesn't
mean that `git hash-object`{.markup--code .markup--p-code} is just a
fancy wrapper around `sha1sum`{.markup--code .markup--p-code} or similar
tools.

```{#17a4 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ echo "hello world" | sha1sum
22596363b3de40b06f981fb85d82312e8c0ed511  -
$ echo "hello world" | git hash-object --stdin
3b18e512dba79e4c8300dd08aeb37f8e728b8dad
```

That's because each object stored by Git has a header in addition to the
file content, identifying the type of object. The object types in Git
are

- [**blob** --- the actual data the user is adding to Git; if you're
  committing `main.rs`{.markup--code .markup--li-code} to Git, the
  content of `main.rs`{.markup--code .markup--li-code} is stored as a
  blob object.]{#256d}
- [**tree** --- a tree object stores a mapping from object hashes to
  the human-readable file/directory names; it also stores the file
  permissions (mode).]{#2447}
- [**commit** --- this is what most people would think of being stored
  in a VCS; in Git it's basically an aggregate --- it references tree
  objects, stores the comment message, metadata like the commit
  author, possibly the commit signature, and such like.]{#dab0}

As an example, let's say our initial commit of a new Rust project had a
`Cargo.toml`{.markup--code .markup--p-code} file and
`src/main.rs`{.markup--code .markup--p-code} and
`src/lib.rs`{.markup--code .markup--p-code} files. You might end up with
an object graph like

<figure id="8da8" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*YrPrMjgLeXs3FEOB_-5nRw.png"
class="graf-image" data-image-id="1*YrPrMjgLeXs3FEOB_-5nRw.png"
data-width="956" data-height="777" />
<figcaption>simple Git object graph example © the author</figcaption>
</figure>

Note that in and of themselves, blob objects don't know anything about
themselves --- a complete lack of self-awareness as it were. The fact
that blob `2a3b`{.markup--code .markup--p-code} holds content for a file
we know as `main.rs`{.markup--code .markup--p-code} that has
`0644`{.markup--code .markup--p-code} file permission is only captured
in the tree object. We will get more into the details of each as we go
along.

One last thing to mention is that all the object contents are
encoded/compressed with ZLib.

### Blobs {#9c1e .graf .graf--h3 .graf-after--p name="9c1e"}

Let's start our Rust code looking at blob objects. We are going to
implement some of the `git hash-object`{.markup--code .markup--p-code}
command. First let's look at the command arguments to be parsed by
[`clap`{.markup--code
.markup--p-code}](https://docs.rs/clap/latest/clap/){.markup--anchor
.markup--p-anchor data-href="<https://docs.rs/clap/latest/clap/>"
rel="noopener" target="\_blank"}

<figure id="5655" class="graf graf--figure graf--iframe graf-after--p">

</figure>

> Note: I'm not showing all the command arguments available to
> `git hash-object`{.markup--code .markup--blockquote-code}.

Everything in `struct HashObjectArgs`{.markup--code .markup--p-code}
should be familiar from my first post, except for the
`file`{.markup--code .markup--p-code} field at the end, lines 11--12.
Many Git commands have a syntax where a `--`{.markup--code
.markup--p-code} indicates the end of the command line arguments and the
beginning of "raw" arguments, typically file paths. Tell
`clap`{.markup--code .markup--p-code} using
`#[arg(last = true)]`{.markup--code .markup--p-code}. Combine that with
the type `Option<Vec<OsString>>`{.markup--code .markup--p-code} and we
can now optionally take a list of files e.g.

```{#fe70 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
git hash-object -- file1 file2 file3
```

Given the `clap`{.markup--code .markup--p-code} setup and an update to
the `match`{.markup--code .markup--p-code} in `main()`{.markup--code
.markup--p-code} as shown in the previous post, I wrote a new function
`hash_object_command(args)`{.markup--code .markup--p-code} which
currently only supports the `--stdin`{.markup--code .markup--p-code}
option. I also support the `-w`{.markup--code .markup--p-code} option
which will create a file in `.git/objects`{.markup--code
.markup--p-code}.

<figure id="9d25" class="graf graf--figure graf--iframe graf-after--p">

</figure>

I read all the content into a buffer `input`{.markup--code
.markup--p-code} and then construct the object header. The object header
is of the form `type len\0`{.markup--code .markup--p-code} --- the
object type, in this case `blob`{.markup--code .markup--p-code} then a
space and the length of the content that follows the null byte. Then I
build a buffer combining the header and the object contents read from
`stdin`{.markup--code .markup--p-code}. Following that I have three
helper functions, to generate the hash string, encode/compress the file
contents with ZLib and write out the file. Finally the object hash is
printed to `stdout`{.markup--code .markup--p-code}.

<figure id="2ea6" class="graf graf--figure graf--iframe graf-after--p">

</figure>

To do the SHA-1 hash, I use the `sha1`{.markup--code .markup--p-code}
crate. Most hash/digest and compression libraries follow a common
pattern

- [input all the data to process]{#d710}
- [call an "I'm done" function]{#e3b4}

The `Sha1`{.markup--code .markup--p-code} type follows this pattern
(lines 2--4) and then using the `hex`{.markup--code .markup--p-code}
crate I take the bytes to produce the 40 character usable string
representation.

To do the ZLib encoding, I use the `flate2`{.markup--code
.markup--p-code} crate, which follows the same pattern --- lines 9--11.

Finally, if the user provided the `-w`{.markup--code .markup--p-code}
option the `write_object()`{.markup--code .markup--p-code} method is
called at line 15. First I take the 40 character hash string and split
it into the first 2 characters and the remaining 38, to construct the
directory name and file name respectively. I then construct the
`PathBuf`{.markup--code .markup--p-code}
representing `.git/objects/xx`{.markup--code .markup--p-code} where
`xx`{.markup--code .markup--p-code} are those first 2 characters. If
this directory needs to be created, I do so. Finally, after constructing
the `PathBuf`{.markup--code .markup--p-code} for the full path including
the filename, I write out the ZLib encoded contents.

Starting from a fresh repository, running this you'll see something like

```{#ab4b .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ ls .git/objects/
branches  hooks  info  pack
$ echo "hello world" | rust-git hash-object --stdin -w
3b18e512dba79e4c8300dd08aeb37f8e728b8dad
$ ls .git/objects/
3b  branches  hooks  info  pack
$ ls .git/objects/3b
18e512dba79e4c8300dd08aeb37f8e728b8dad
```

You can use the `git cat-file`{.markup--code .markup--p-code} command
(which we'll get to next post) and verify that my Rust version "did the
right thing" as well as a few other commands you could run including the
"reverse" operation showing the raw contents using [`pigz`{.markup--code
.markup--p-code}](https://github.com/madler/pigz){.markup--anchor
.markup--p-anchor data-href="<https://github.com/madler/pigz>"
rel="noopener" target="\_blank"} (or some other utility that can
decompress ZLib data).

```{#d86b .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git cat-file -p 3b18
hello world
$ file .git/objects/3b/18e512dba79e4c8300dd08aeb37f8e728b8dad
.git/objects/3b/18e512dba79e4c8300dd08aeb37f8e728b8dad: zlib compressed data
$ xxd .git/objects/3b/18e512dba79e4c8300dd08aeb37f8e728b8dad
00000000: 789c 4bca c94f 5230 3462 c848 cdc9 c957  x.K..OR04b.H...W
00000010: 28cf 2fca 49e1 0200 4411 0689            (./.I...D...
$ cat .git/objects/3b/18e512dba79e4c8300dd08aeb37f8e728b8dad |pigz -d -
blob 12hello world
```

### Next Time {#ab1e .graf .graf--h3 .graf-after--pre name="ab1e"}

The next blog will go on to implement the `git cat-file`{.markup--code
.markup--p-code} command so we can look at the contents of objects. It
is effectively the reverse of the `git hash-object`{.markup--code
.markup--p-code} command.
:::
:::
:::

::: {#3a34 .section .section .section--body .section--last}
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
on [July 30, 2024](https://medium.com/p/8589777a21da).

[Canonical
link](https://medium.com/@raysuliteanu/learning-git-internals-with-rust-8589777a21da){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
