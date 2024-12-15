---
title: Learning Git Internals with Rust
description: Part 5 - ls-tree
date: 10-06-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: true
---

In this latest blog on Git internals with Rust, I will focus on the
`ls-tree`{.markup--code .markup--p-code} command in Git. You can find
the earlier posts here:

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object
- [Part 3](learning-git-pt3) — refactoring
- [Part 4](learning-git-pt4) — git cat-file

The `ls-tree`{.markup--code .markup--p-code} command is similar to doing
an `ls`{.markup--code .markup--p-code} in a terminal emulator. It lists
the contents of `tree`{.markup--code .markup--p-code} objects in Git.
The Git object model looks like this (copied from Part 2)

TODO: insert figure

A `commit`{.markup--code .markup--p-code} object contains (among other
things) a "pointer" to a `tree`{.markup--code .markup--p-code} object in
the form of a SHA-1 hash (\`01a2\` in the diagram). The
`tree`{.markup--code .markup--p-code} object contains entries
referencing other Git objects at that level of the hierarchy of objects.
Consider this directory structure

```{#e736 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="shell"}
my_project/
  Cargo.toml
  src/
    main.rs
    commands.rs
    commands/
      ls_tree.rs
```

A `tree`{.markup--code .markup--p-code} object would have
`Cargo.toml`{.markup--code .markup--p-code} and `src`{.markup--code
.markup--p-code} as entries. The `src`{.markup--code .markup--p-code}
entry would have a type `tree`{.markup--code .markup--p-code} which
could then be used to recurse down and list additional tree entries
(e.g. `git ls-tree -r ...`{.markup--code .markup--p-code} similar to
`ls -r`{.markup--code .markup--p-code}).

```{#6935 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git ls-tree c086
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780    Cargo.toml
040000 tree 92bf6c48606cbce7b9c9fcc926b4421afb6ed386    src
```

### Tree Object Format {#4f3e .graf .graf--h3 .graf-after--pre name="4f3e"}

The contents of a `tree`{.markup--code .markup--p-code} object follows
the pattern we saw in Part 3 for other objects like `blob`{.markup--code
.markup--p-code} objects --- a header followed by content, with the
header and content separated by a null byte (0x0), with the header
containing the object type (`tree`{.markup--code .markup--p-code}) and
the length of the content.

For `tree`{.markup--code .markup--p-code} objects the content contains
one or more "entries". Each entry is itself split into two parts
separated by a null byte --- the file permissions (i.e. "mode") as
octal-encoded bits typical for \*nix systems (e.g. 100644 for Cargo.toml
in the example above) and the file name in the first part, and after the
null byte the 20 byte SHA-1 hash. This is the raw bytes, not
ASCII-encoded (otherwise it would be 40 bytes, right). So a
`tree`{.markup--code .markup--p-code} object looks something like

<figure id="97de" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*wQe6nX1bMHbUdVL4AuOcDA.png"
class="graf-image" data-image-id="1*wQe6nX1bMHbUdVL4AuOcDA.png"
data-width="960" data-height="90" />
<figcaption>raw format of a tree object</figcaption>
</figure>

The `ls-tree`{.markup--code .markup--p-code} command also allows
printing the size of the file with the `-l/--long`{.markup--code
.markup--p-code} option e.g.

```{#f6e4 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git ls-tree -l c086
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780     535    Cargo.toml
040000 tree 92bf6c48606cbce7b9c9fcc926b4421afb6ed386       -    src
```

You may have noticed though that neither the object type nor the object
length is actually contained in the description of the
`tree`{.markup--code .markup--p-code} object entries. You are correct.
To retrieve this information we have to take the object hash in each
entry and read the referenced object to retrieve that info.

Luckily we know how to do that already from earlier posts. So let's get
to it.

### Implementing ls-tree {#43c3 .graf .graf--h3 .graf-after--p name="43c3"}

#### Refactoring reading objects {#c239 .graf .graf--h4 .graf-after--h3 name="c239"}

First off we're going to refactor some of the code from earlier posts to
make our lives a little easier. I have extracted the object reading code
into its own module and struct, moving it from the `util`{.markup--code
.markup--p-code} module.

<figure id="9358" class="graf graf--figure graf--iframe graf-after--p">

</figure>

A couple of the utility functions from `util`{.markup--code
.markup--p-code} came along and are now part of the
`GitObject`{.markup--code .markup--p-code} implementation. The
`GitObject`{.markup--code .markup--p-code} `read()`{.markup--code
.markup--p-code} method only decodes the object header, since they are
all the same. The content specific to a specific type of Git object is
stored as bytes in the `body`{.markup--code .markup--p-code} field of
the `GitObject`{.markup--code .markup--p-code} struct. The
`util.rs`{.markup--code .markup--p-code} module now essentially just
contains stuff related to finding Git directories.

The other main refactoring was to move the `tree`{.markup--code
.markup--p-code} object printing that was in `cat-file`{.markup--code
.markup--p-code} for dumping `tree`{.markup--code .markup--p-code}
objects into the new `ls-tree`{.markup--code .markup--p-code} command
handling.

<figure id="eadb" class="graf graf--figure graf--iframe graf-after--p">

</figure>

I was also able to simplify the tree printing function itself, which
I'll show later.

#### ls-tree command {#441d .graf .graf--h4 .graf-after--p name="441d"}

Following the pattern I've established I created a new
`ls-tree`{.markup--code .markup--p-code} module in the
`commands`{.markup--code .markup--p-code} module and a new arguments
structure `LsTreeArgs`{.markup--code .markup--p-code} for the
command-line options handled by `clap`{.markup--code .markup--p-code}.

<figure id="bf4b" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Two things to call out here are the `tree_ish`{.markup--code
.markup--p-code} option and the `path`{.markup--code .markup--p-code}
option. One thing I haven't done yet in this series is handle all the
various ways you can specify specific objects in Git. All I've done is
support partial object hashes (i.e. `git cat-file 942a0`{.markup--code
.markup--p-code} vs
`git cat-file 942a0dd92845b91f0ed99178b782729f233ea780`{.markup--code
.markup--p-code}). But you can specify objects in many different ways
like by `HEAD`{.markup--code .markup--p-code} or relative to it like
`HEAD~3`{.markup--code .markup--p-code} or by tag etc. etc.. With
`ls-tree`{.markup--code .markup--p-code} the "tree-ish" value is some
identifier that resolves to a `tree`{.markup--code .markup--p-code}
object. From the [Git
documentation](https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddeftree-ishatree-ishalsotreeish){.markup--anchor
.markup--p-anchor
data-href="<https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddeftree-ishatree-ishalsotreeish>"
rel="noopener" target="\_blank"}:

```{#6bf6 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="plaintext"}
A tree object or an object that can be recursively dereferenced to a tree
object. Dereferencing a commit object yields the tree object corresponding
to the revision's top directory. The following are all tree-ishes: a
commit-ish, a tree object, a tag object that points to a tree object,
a tag object that points to a tag object that points to a tree object, etc.
```

And a
"[commit-ish](https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddefcommit-ishacommit-ishalsocommittish){.markup--anchor
.markup--p-anchor
data-href="<https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddefcommit-ishacommit-ishalsocommittish>"
rel="noopener" target="\_blank"}" is

```{#cbaa .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="plaintext"}
A commit object or an object that can be recursively dereferenced to a commit
object. The following are all commit-ishes: a commit object, a tag object that
points to a commit object, a tag object that points to a tag object that points
to a commit object, etc.
```

So in my implementation I've tried to add this support for following
these references (at least for following tags, not some things like
`HEAD`{.markup--code .markup--p-code}).

The other command-line option `path`{.markup--code .markup--p-code} is
not really a path to an object but more a (series of) filter on the
output. So for example I could do

```{#d5a3 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ git ls-tree -r HEAD */*.rs
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    src/commands.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    src/main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    src/object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    src/tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    src/util.rs
```

Without the path filter, if I used the `-r`{.markup--code
.markup--p-code} recurse option I'd see

```{#f4f4 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="bash"}
$ git ls-tree -r HEAD
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780    Cargo.toml
100644 blob 89e5d2e19e146ebd87a4da93dc7050347b602549    README.md
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    src/commands.rs
100644 blob 6ec2255e0d5d1eafeb498c22f838a9063dc51a03    src/commands/cat_file.rs
100644 blob cf2573e62ad244f1c8ab2cf4343aea6608def1e5    src/commands/config.rs
100644 blob aff7dd1806bdedc2ae721cfdacf418771331986c    src/commands/hash_object.rs
100644 blob 8a68f0ab4175e5924f9f95a71fcb9719d1217fdc    src/commands/init.rs
100644 blob 6b10925706937c0aab8abc94d640157045f34a09    src/commands/ls_tree.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    src/main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    src/object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    src/tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    src/util.rs
```

Also note that `*/*.rs`{.markup--code .markup--p-code} did not show all
the Rust files, even with the `*/`{.markup--code .markup--p-code}. To
fully match you'd want `**/`{.markup--code .markup--p-code} as the
filter ...

```{#adc6 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="bash"}
$ git ls-tree -r HEAD **/*.rs
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    src/commands.rs
100644 blob 6ec2255e0d5d1eafeb498c22f838a9063dc51a03    src/commands/cat_file.rs
100644 blob cf2573e62ad244f1c8ab2cf4343aea6608def1e5    src/commands/config.rs
100644 blob aff7dd1806bdedc2ae721cfdacf418771331986c    src/commands/hash_object.rs
100644 blob 8a68f0ab4175e5924f9f95a71fcb9719d1217fdc    src/commands/init.rs
100644 blob 6b10925706937c0aab8abc94d640157045f34a09    src/commands/ls_tree.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    src/main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    src/object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    src/tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    src/util.rs
```

The `tree-ish`{.markup--code .markup--p-code} support is in the
`ls_tree()`{.markup--code .markup--p-code} method and handling the
various output options is in the `print_tree_object()`{.markup--code
.markup--p-code} method show later.

<figure id="7dfc" class="graf graf--figure graf--iframe graf-after--p">

</figure>

I split the functions into a public `ls_tree_command()`{.markup--code
.markup--p-code} called by `main()`{.markup--code .markup--p-code} and
an `ls_tree()`{.markup--code .markup--p-code} that can be recursively
called if the object hash is not a `tree`{.markup--code .markup--p-code}
object identifier.

#### Tags {#4db2 .graf .graf--h4 .graf-after--p name="4db2"}

To handle tags, I created a new `tag`{.markup--code .markup--p-code}
module and `Tag`{.markup--code .markup--p-code} struct. Tags technically
are not objects but references ("refs") and live
in `.git/refs/tags`{.markup--code .markup--p-code}
not `.git/objects`{.markup--code .markup--p-code}.

<figure id="6625" class="graf graf--figure graf--iframe graf-after--p">

</figure>

A tag "object" file is just a file with an object hash, so I read that
and save it.

To handle the "tree-ish" properly, "dereferencing" the tag leads to the
commit so reading the commit then gives me the tree and then finally I
can print the tree object.

```{#1e51 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ git tag HEAD wip
$ cat .git/refs/tags/wip
a8011816d88652738af3a5a0470a745c673c8ed2
$ git cat-file -t a8011816d88652738af3a5a0470a745c673c8ed2
commit
$ git cat-file -p a8011816d88652738af3a5a0470a745c673c8ed2
tree c08699ada7f66bf0d7fa61d4c8cbd5d8eb309dc9
<snip>
$ git ls-tree c08699ada7f66bf0d7fa61d4c8cbd5d8eb309dc9
100644 blob 9b270e120d48331e47785a868af6fd940177680a    .gitignore
100644 blob 02e4d202dcf03fcb985fcebe0af2c01b81b65f29    .gitmodules
100644 blob 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64    LICENSE
<snip>
```

The above shows manually what `ls-tree`{.markup--code .markup--p-code}
needs to support directly ...

```{#1afb .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
git ls-tree wip
100644 blob 9b270e120d48331e47785a868af6fd940177680a    .gitignore
100644 blob 02e4d202dcf03fcb985fcebe0af2c01b81b65f29    .gitmodules
100644 blob 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64    LICENSE
<snip>
```

#### Commit Objects {#12b1 .graf .graf--h4 .graf-after--pre name="12b1"}

I created a `Commit`{.markup--code .markup--p-code} object to contain
the details of the commit. You can read the details about commit objects
[here](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects){.markup--anchor
.markup--p-anchor
data-href="<https://git-scm.com/book/en/v2/Git-Internals-Git-Objects>"
rel="noopener" target="\_blank"}. But to save some effort, what it says
regarding the format of a `commit`{.markup--code .markup--p-code} object
is:

```{#b777 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="plaintext"}
The format for a commit object is simple: it specifies the top-level tree for
the snapshot of the project at that point; the parent commits if any; the
author/committerinformation (which uses your user.name and user.email
configuration settings and a timestamp); a blank line, and then the commit
message.
```

This turns out to be one of the simpler formats to read since it's all
just plain text. No fancy separators or segments or anything.

<figure id="db20" class="graf graf--figure graf--iframe graf-after--p">

</figure>

#### Printing tree objects {#5cd8 .graf .graf--h4 .graf-after--figure name="5cd8"}

There are a few interesting aspects to printing the tree object, mostly
around recursion and filtering. I have not implemented the filtering as
of now.

<figure id="d46e" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Recall our diagram from earlier (slightly enhanced).

<figure id="f2af" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*i-3EPL6zultViGNURxlXdw.png"
class="graf-image" data-image-id="1*i-3EPL6zultViGNURxlXdw.png"
data-width="960" data-height="184" />
</figure>

The `print_tree_object()`{.markup--code .markup--p-code} method loops
over the body, advancing a "pointer" (the `body`{.markup--code
.markup--p-code} variable) to the remaining data as we work through the
entries. First we get the file and mode from the entry, by splitting on
0x0. Then we read exactly 20 bytes for the SHA1 hash. We need to do this
regardless of whether we're only printing the name
(`—name-only`{.markup--code .markup--p-code}) to advance the pointer.
It's not really that much "overhead" to worry about conditionally
advancing it ... somehow we need to advance the pointer.

If we are only printing the name, we now get to the challenge of the
`-r`{.markup--code .markup--p-code} recursion option. The
`ls-tree`{.markup--code .markup--p-code} command does a depth first
walk, so what I did is add this
`path_part: Option<String>`{.markup--code .markup--p-code} parameter,
where I build up the path as we recurse, with an initial value of
`None`{.markup--code .markup--p-code}. If it's not just the name we're
printing, we still have the same recursion to do, but then we format the
entry appropriately, optionally adding in the object length if the
`-l/--long`{.markup--code .markup--p-code} option was provided.

One little quirk I noticed when comparing my output to the real
`ls-tree`{.markup--code .markup--p-code} output is that the final space
separating the file name from what precedes it is that it's a tab
`\t`{.markup--code .markup--p-code} character. _C'est la vie_.

### Conclusion {#1d8b .graf .graf--h3 .graf-after--p name="1d8b"}

And there you have it, a mostly complete implementation of
`ls-tree`{.markup--code .markup--p-code} in Rust. As I mentioned one
thing not yet implemented (and perhaps never to be implemented) is the
path filtering. But there's also another interesting case with respect
to the tree output, and that it's relative --- or implicitly filtered if
you will --- by what directory you are in, when listing a commit object
recursively. Taking my simple example from the beginning of the post

```{#824f .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="shell"}
my_project/
  Cargo.toml
  src/
    main.rs
    commands.rs
    commands/
      ls_tree.rs
```

if my current directory is `my_project/src`{.markup--code
.markup--p-code} then even if Cargo.toml is part of the commit that I'm
passing to `ls-tree`{.markup--code .markup--p-code} then only
`main.rs`{.markup--code .markup--p-code}, `commands.rs`{.markup--code
.markup--p-code} and `commands/ls_tree.rs`{.markup--code
.markup--p-code} should be printed. I didn't bother.

```{#0b15 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="bash"}
$  git ls-tree a8011
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780    Cargo.toml
100644 blob 89e5d2e19e146ebd87a4da93dc7050347b602549    README.md
040000 tree 92bf6c48606cbce7b9c9fcc926b4421afb6ed386    src
$ git ls-tree -r a8011
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780    Cargo.toml
100644 blob 89e5d2e19e146ebd87a4da93dc7050347b602549    README.md
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    src/commands.rs
100644 blob 6ec2255e0d5d1eafeb498c22f838a9063dc51a03    src/commands/cat_file.rs
100644 blob cf2573e62ad244f1c8ab2cf4343aea6608def1e5    src/commands/config.rs
100644 blob aff7dd1806bdedc2ae721cfdacf418771331986c    src/commands/hash_object.rs
100644 blob 8a68f0ab4175e5924f9f95a71fcb9719d1217fdc    src/commands/init.rs
100644 blob 6b10925706937c0aab8abc94d640157045f34a09    src/commands/ls_tree.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    src/main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    src/object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    src/tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    src/util.rs
$ cd src
$ git ls-tree -r a8011
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    commands.rs
100644 blob 6ec2255e0d5d1eafeb498c22f838a9063dc51a03    commands/cat_file.rs
100644 blob cf2573e62ad244f1c8ab2cf4343aea6608def1e5    commands/config.rs
100644 blob aff7dd1806bdedc2ae721cfdacf418771331986c    commands/hash_object.rs
100644 blob 8a68f0ab4175e5924f9f95a71fcb9719d1217fdc    commands/init.rs
100644 blob 6b10925706937c0aab8abc94d640157045f34a09    commands/ls_tree.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    util.rs
```

In the next few posts in this series I'll probably be tackling
_creating_ tree objects and commits and cloning a remote Git repo. Stay
tuned!
:::
:::
:::

::: {#529e .section .section .section--body .section--last}
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
on [October 6, 2024](https://medium.com/p/4fbf68936b3a).

[Canonical
link](https://medium.com/@raysuliteanu/learning-git-internals-with-rust-4fbf68936b3a){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
