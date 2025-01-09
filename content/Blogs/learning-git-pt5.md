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

In this latest blog on Git internals with Rust, I will focus on the `ls-tree`
command in Git. You can find the earlier posts here:

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object
- [Part 3](learning-git-pt3) — refactoring
- [Part 4](learning-git-pt4) — git cat-file

The `ls-tree` command is similar to doing an `ls` in a terminal emulator. It
lists the contents of `tree` objects in Git. The Git object model looks like
this (copied from Part 2)

TODO: insert figure

A `commit` object contains (among other things) a "pointer" to a `tree` object
in the form of a SHA-1 hash (\`01a2\` in the diagram). The `tree` object
contains entries referencing other Git objects at that level of the hierarchy of
objects. Consider this directory structure

```bash
my_project/
  Cargo.toml
  src/
    main.rs
    commands.rs
    commands/
      ls_tree.rs
```

A `tree` object would have `Cargo.toml` and `src` as entries. The `src` entry
would have a type `tree` which could then be used to recurse down and list
additional tree entries (e.g. `git ls-tree -r ...` similar to `ls -r`).

```bash
$ git ls-tree c086
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780    Cargo.toml
040000 tree 92bf6c48606cbce7b9c9fcc926b4421afb6ed386    src
```

### Tree Object Format

The contents of a `tree` object follows the pattern we saw in Part 3 for other
objects like `blob` objects --- a header followed by content, with the header
and content separated by a null byte (0x0), with the header containing the
object type (`tree`) and the length of the content.

For `tree` objects the content contains one or more "entries". Each entry is
itself split into two parts separated by a null byte --- the file permissions
(i.e. "mode") as octal-encoded bits typical for \*nix systems (e.g. 100644 for
Cargo.toml in the example above) and the file name in the first part, and after
the null byte the 20 byte SHA-1 hash. This is the raw bytes, not ASCII-encoded
(otherwise it would be 40 bytes, right). So a `tree` object looks something like

TODO: replace figure/gist

The `ls-tree` command also allows printing the size of the file with the
`-l/--long` option e.g.

```bash
$ git ls-tree -l c086
100644 blob 942a0dd92845b91f0ed99178b782729f233ea780     535    Cargo.toml
040000 tree 92bf6c48606cbce7b9c9fcc926b4421afb6ed386       -    src
```

You may have noticed though that neither the object type nor the object length
is actually contained in the description of the `tree` object entries. You are
correct. To retrieve this information we have to take the object hash in each
entry and read the referenced object to retrieve that info.

Luckily we know how to do that already from earlier posts. So let's get to it.

## Implementing ls-tree

### Refactoring reading objects

First off we're going to refactor some of the code from earlier posts to make
our lives a little easier. I have extracted the object reading code into its own
module and struct, moving it from the `util` module.

TODO: replace figure/gist

A couple of the utility functions from `util` came along and are now part of the
`GitObject` implementation. The `GitObject` `read()` method only decodes the
object header, since they are all the same. The content specific to a specific
type of Git object is stored as bytes in the `body` field of the `GitObject`
struct. The `util.rs` module now essentially just contains stuff related to
finding Git directories.

The other main refactoring was to move the `tree` object printing that was in
`cat-file` for dumping `tree` objects into the new `ls-tree` command handling.

TODO: replace figure/gist

I was also able to simplify the tree printing function itself, which I'll show
later.

### ls-tree command

Following the pattern I've established I created a new `ls-tree` module in the
`commands` module and a new arguments structure `LsTreeArgs` for the command-line
options handled by `clap`.

TODO: replace figure/gist

Two things to call out here are the `tree_ish` option and the `path` option. One
thing I haven't done yet in this series is handle all the various ways you can
specify specific objects in Git. All I've done is support partial object hashes
(i.e. `git cat-file 942a0` vs `git cat-file 942a0dd92845b91f0ed99178b782729f233ea780`).
But you can specify objects in many different ways like by `HEAD` or relative to
it like `HEAD~3` or by tag etc. etc.. With `ls-tree` the "tree-ish" value is some
identifier that resolves to a `tree` object. From the [Git documentation](https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddeftree-ishatree-ishalsotreeish):

```text
A tree object or an object that can be recursively dereferenced to a tree
object. Dereferencing a commit object yields the tree object corresponding
to the revision's top directory. The following are all tree-ishes: a
commit-ish, a tree object, a tag object that points to a tree object,
a tag object that points to a tag object that points to a tree object, etc.
```

And a "[commit-ish](https://git-scm.com/docs/gitglossary#Documentation/gitglossary.txt-aiddefcommit-ishacommit-ishalsocommittish)"
is

```text
A commit object or an object that can be recursively dereferenced to a commit
object. The following are all commit-ishes: a commit object, a tag object that
points to a commit object, a tag object that points to a tag object that points
to a commit object, etc.
```

So in my implementation I've tried to add this support for following these
references (at least for following tags, not some things like `HEAD`).

The other command-line option `path` is not really a path to an object but more
a (series of) filter on the output. So for example I could do

```bash
$ git ls-tree -r HEAD */*.rs
100644 blob b1782add9b7656ceb6c95756a7c9a43cd221d877    src/commands.rs
100644 blob 24406bb5d3df8ba3e667d6ee10d065075b174bc2    src/main.rs
100644 blob 5634f30e1edd28dd589d9dc805d792b1dda1adb5    src/object.rs
100644 blob ac364c6a99bc887e6358d73b2054f358eecc4612    src/tag.rs
100644 blob d03dfe603c78389df1575d8ca2dc3088204cfc76    src/util.rs
```

Without the path filter, if I used the `-r` recurse option I'd see

```bash
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

Also note that `*/*.rs` did not show all the Rust files, even with the `*/`. To
fully match you'd want `**/` as the filter ...

```bash
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

The `tree-ish` support is in the `ls_tree()` method and handling the various
output options is in the `print_tree_object()` method show later.

TODO: replace figure/gist

I split the functions into a public `ls_tree_command()` called by `main()` and
an `ls_tree()` that can be recursively called if the object hash is not a `tree`
object identifier.

### Tags

To handle tags, I created a new `tag` module and `Tag` struct. Tags technically
are not objects but references ("refs") and live in `.git/refs/tags` not
`.git/objects`.

TODO: replace figure/gist

A tag "object" file is just a file with an object hash, so I read that and save
it.

To handle the "tree-ish" properly, "dereferencing" the tag leads to the commit
so reading the commit then gives me the tree and then finally I can print the
tree object.

```bash
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

The above shows manually what `ls-tree` needs to support directly ...

```bash
git ls-tree wip
100644 blob 9b270e120d48331e47785a868af6fd940177680a    .gitignore
100644 blob 02e4d202dcf03fcb985fcebe0af2c01b81b65f29    .gitmodules
100644 blob 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64    LICENSE
<snip>
```

### Commit Objects

I created a `Commit` object to contain the details of the commit. You can read
the details about commit objects [here](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects).
But to save some effort, what it says regarding the format of a `commit` object
is:

```text
The format for a commit object is simple: it specifies the top-level tree for
the snapshot of the project at that point; the parent commits if any; the
author/committerinformation (which uses your user.name and user.email
configuration settings and a timestamp); a blank line, and then the commit
message.
```

This turns out to be one of the simpler formats to read since it's all just
plain text. No fancy separators or segments or anything.

TODO: replace figure/gist

### Printing tree objects

There are a few interesting aspects to printing the tree object, mostly around
recursion and filtering. I have not implemented the filtering as of now.

TODO: replace figure/gist

Recall our diagram from earlier (slightly enhanced).

TODO: replace figure/gist

The `print_tree_object()` method loops over the body, advancing a "pointer" (the
`body` variable) to the remaining data as we work through the entries. First we
get the file and mode from the entry, by splitting on 0x0. Then we read exactly
20 bytes for the SHA1 hash. We need to do this regardless of whether we're only
printing the name (`—name-only`) to advance the pointer. It's not really that
much "overhead" to worry about conditionally advancing it ... somehow we need to
advance the pointer.

If we are only printing the name, we now get to the challenge of the `-r`
recursion option. The `ls-tree` command does a depth first walk, so what I did
is add this `path_part: Option<String>` parameter, where I build up the path as
we recurse, with an initial value of `None`. If it's not just the name we're
printing, we still have the same recursion to do, but then we format the entry
appropriately, optionally adding in the object length if the `-l/--long` option
was provided.

One little quirk I noticed when comparing my output to the real `ls-tree` output
is that the final space separating the file name from what precedes it is that
it's a tab `\t` character. _C'est la vie_.

## Conclusion

And there you have it, a mostly complete implementation of `ls-tree` in Rust. As
I mentioned one thing not yet implemented (and perhaps never to be implemented)
is the path filtering. But there's also another interesting case with respect to
the tree output, and that it's relative --- or implicitly filtered if you will
--- by what directory you are in, when listing a commit object recursively.
Taking my simple example from the beginning of the post

```bash
my_project/
  Cargo.toml
  src/
    main.rs
    commands.rs
    commands/
      ls_tree.rs
```

if my current directory is `my_project/src` then even if Cargo.toml is part of
the commit that I'm passing to `ls-tree` then only `main.rs`, `commands.rs` and
`commands/ls_tree.rs` should be printed. I didn't bother.

```bash
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

In the next few posts in this series I'll probably be tackling _creating_ tree
objects and commits and cloning a remote Git repo. Stay tuned!

---

As always, please comment if you notice anything I could do better with
my Rust coding as I'm doing this to learn Rust better. If there are
idiomatic things that I could do that I'm not, let me know! And any
other comments on the content or possible future content, let me know!
