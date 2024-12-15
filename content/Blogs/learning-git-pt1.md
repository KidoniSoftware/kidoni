---
title: Learning Git Internals with Rust
description: the first in a series on Git internals as a project to learn Rust
created: 2024-07-26
tags:
  - git
  - rust
  - programming
  - blog
draft: false
---

Have you ever wondered how Git does what it does? What happens when you
do a commit? You can read about some of this in the [Git
Book](https://git-scm.com/book/en/v2) free online, like in [Chapter 10 on Git
Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain).
But it doesn't give you all the
details, as I discovered. And I wanted another interesting "project" to
help me on my continuing journey learning Rust. So why not poke around
under the Git hood?

If all I wanted to do was use Git from Rust, there's already a decent
crate out there,
[git2](https://docs.rs/git2/latest/git2/index.html), that wraps the C
libgit2. And in fact this blog post
(or series probably) was inspired by me trying to figure out
git2/libgit2, since I kept having to try and figure out what was going
on under the hood. I'd also briefly looked at the [CodeCrafters Git
course](https://app.codecrafters.io/courses/git), and started working through the
exercises using Rust.

However, for this blog I'm starting from scratch. The intent here is not
to rewrite the Git client in its entirety, nor will I cover every aspect
of the few commands I do cover. This is still about learning Rust, but
with learning some Git internals at the same time. I am also going to
assume some familiarity with Git and source code version control in
general ... I am not going to explain why using version control systems
(VCSs) is a "good thing" nor go into the history of Git or VCS. If you
do want some of the Git history, I recently read an interesting blog
[here](https://graphite.dev/blog/bitkeeper-linux-story-of-git-creation) on the
[Graphite](https://graphite.dev/) blog.
Speaking of Graphite I am also not going to talk about different
approaches to doing development with Git (like the 'stacking' approach
Graphite supports with their product).

So what **_will_** I cover?

- creating a new empty repository (`git init`)
- creating a Git object (`git hash-object`)
- writing a Git object to `stdout` (`git cat-file`)
- looking at Git config (`git config`)
- looking at Git tree objects (`git ls-tree`)
- looking at Git packs (e.g. `git pack-objects`, `git index-pack`,
  `git unpack-objects` and the like)
- maybe look at `git clone` / `git pull` / `git push`

Who knows, maybe more (or maybe less). And to re-iterate, then intent is
not to replicate the above commands in their entirety, but rather just
enough to understand what Git is doing.

Let's get started.

## Initializing a New Repository

If you've got nothing to start from you create a new Git repository with
`git init`. Without any other options,
this will create the `.git` directory in
the current directory, and it will create a few additional directories
and files.

```bash
$ ls -a
$ git init
Initialized empty Git repository in /tmp/foo/.git/
$ ls -al .git
drwxr-xr-x  - ray 25 Jul 16:03 -I branches
.rw-r--r-- 92 ray 25 Jul 16:03 -I config
.rw-r--r-- 73 ray 25 Jul 16:03 -I description
.rw-r--r-- 22 ray 25 Jul 16:03 -I HEAD
drwxr-xr-x  - ray 25 Jul 16:03 -I hooks
drwxr-xr-x  - ray 25 Jul 16:03 -I info
drwxr-xr-x  - ray 25 Jul 16:03 -I objects
drwxr-xr-x  - ray 25 Jul 16:03 -I refs
```

Before we continue it would probably help to explain a few key concepts
in Git's implementation. A lot more detail is in the [Git
Book](https://git-scm.com/book/en/v2) and other sources. You can think
of Git as a persistent
(hash) map also known as a key-value store. More specifically Git is
typically described as a "content-addressable store" but really that's
just a hash map. In the case of Git, the hash is a SHA-1 hash generated
from the content being stored. These are "objects" and stored
in `.git/objects`. SHA-1 hashes are 20
bytes which in hex ends up as 40 characters. The first 2 are used to
create subdirectories in the `.git/objects` directory, and the remaining
38 are the filename. So given as hash of
`0b7c8fd4fd2231304c72b781f7a791c39e31d963` you'd have a file path
`.git/objects/0b/7c8fd4fd2231304c72b781f7a791c39e31d963`

The main object types in Git are `blob`,
`tree` and `commit`. More on this in a subsequent blog. So the
directory `.git/objects` is created
during `git init` to store these objects.

Because the hashes are not that easy for humans to remember, Git
supports a way to "refer" to objects with more human-friendly names. The
use of `HEAD` is one example. This is just a "reference" to the current branch.
The `HEAD` file created by `git init` contains a single line referring to the
default branch created by `git init`.

```bash
$ cat .git/HEAD
ref: refs/heads/trunk
```

The name of this default branch depends on a few things.
`git init` supports a command-line option
`--initial-branch` or `-b` to specify the branch name. The
`~/.gitconfig` file can also have your
preferred default branch:

```bash
$ cat /.gitconfig
[init]
    defaultBranch = trunk
```

This is how `git init` populates `.git/HEAD`. The value in the file is the path to
a file in `.git/refs/heads` which contains the hash of the latest commit. But since
this is an empty repository that was just created, there is no
file `.git/refs/heads/trunk` yet.

Finally the `.git/config` file is created
during repository initialization. This is referred to as the "local"
repository configuration, containing repository-specific configuration
overrides to the global (i.e. per-user) and system config. If you use
the command `git config --list --local`
it lists just the content from `.git/config`. At initialization there isn't a
lot of info. It contains a version number, and a few other things, some based on
what options are specified to `git init`. For example the `core.bare` property
is set based on `git init --bare` command line option.

```bash
$ cat .git/config
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
```

The last thing I'm going to touch on for `git init` is the ability to specify a "separate"
Git repository directory that should contain the actual repository and that is then
"referenced" by the directory where `git init` would otherwise create the repository.
That may sound a little confusing, so let's show an example of the different options.
Starting from `/tmp/foo`

```bash
#1
$ git init
Initialized empty Git repository in /tmp/foo/.git/
#2
$ git init bar
Initialized empty Git repository in /tmp/foo/bar/.git/
#3
$ git init --separate-git-dir bar baz
Initialized empty Git repository in /tmp/foo/bar/
$ ls -a baz
.git
$ cat baz/.git
gitdir: /tmp/foo/bar
```

The most common cases are #1 and #2 --- create the repo in the current
directory (#1) or in the specified directory (#2). But look at #3 --- it
says to create the repo in `bar` but
refer to it from `baz`. In
`baz` there's a `.git` _file_ rather than a directory and it contains
configuration that points to the actual repository. You can do
everything in `baz` that you would do if
it were a "normal" Git repo.

## Implementing Init in Rust

### The Command Line

So let's get to some code. One thing that everyone knows about Git is
that it's made up of a bunch of subcommands which take a lot of
different options. I used the [`clap`](https://docs.rs/clap/latest/clap/index.html)
crate to define the commands and options. The
`clap` crate is pretty much standard for
working with command line options. While it provides a builder-style API
I use the derive approach.

First you define your "main" command, in this case that's
`git` of course, so I define a
`struct Git`. Clap infers the command
name from the struct, but if you wanted it different you can customize
it with e.g. `#[command(name = “git”)]`.
The `Parser` derive directive tells Clap
this is the place to start parsing the command line options. Within the
struct I have an for the subcommands and tell Clap using
`#[command(subcommand)]`. One thing I've
omitted at this point are the options to the `git` command itself, which
would be in the `struct Git`. In the `enum Commands` I start defining the
various subcommands which I've started to implement. I tell Clap that
this enum contains the subcommands using
`#[derive(Subcommand)]`.

What we're concerned about right now is the `init` subcommand, and to make
the enum easier to read when
there are a lot of options for the subcommand, I split them out to their
own `struct InitArgs`. These structs are
declared to Clap as holding the subcommand arguments using
`#[derive(Args)]`.

Now we get into the interesting bit, how to define all the various
possible arguments to the command. I've only scratched the surface, and
haven't implemented all the validation and grouping you could and need
to do with the Git commands, but to call out some things you see in the
code.

- Clap infers the argument name from the field name, but you can
  explicitly set the value, in particular if you want a field name
  that's more obvious while not matching the Git command arg name. A
  good example is the `initial_branch`
  field, where I specify the short argument name to be
  `-b` since otherwise Clap would make
  it `-i` since the field starts with
  an 'i'. The long name is still `--initial-branch` as Clap infers.

```bash
#[arg(short = 'b', long)]
initial_branch: Option<String>,
```

- To make an argument optional you can make the field type an
  `Option` or you can set a default
  value. You can see this in the `object_format` option, which makes the
  `object_format` field both optional
  and with a default value.

```bash
#[arg(long, default_value = "sha1")]
object_format: String,
```

- Finally for now with Clap, look at the `directory` field which has no annotation.
  This is still an
  argument but with no short or long indicator, and it is also
  optional. This is how I get the behavior with
  `git init` of optionally specifying
  the directory to create:

```bash
git init
git init foo
```

Moving on to the main method, to have Clap parse the command line you call the
`parse()` method on the struct
that was annotated with `Parse`. If there are any issues parsing
or validating the config, `parse()` will exit and print help text.

> A `help` command is automatically created by Clap.

Otherwise you get back the struct Clap parsed. Then it's simple enough
to just match on the enum commands.

### **Creating the Repository**

The first thing to do is create all the required directories and files,
as described in the first section. This is complicated by the ability to
have a separate Git repo with the `--separate-git-dir` option I mentioned.
There are 3 possibilities for the actual repo directory

- the current directory
- the directory passed to `git init` as the last parameter
- the directory provided to the `--separate-git-dir` option.

On top of that, if there is a separate repo directory provided, we need
to determine where to create the link file --- the current directory or
the directory passed to `git init`.

The first thing I do is look at the `args.directory` and `args.separate_git_dir`
arguments that were provided on the command line. I separated this into a
function `get_git_dirs()` which returns a tuple. The first item in the tuple is
either the value provided on the command line or the current directory
if not specified. The second value of the tuple is the separate
directory that was provided, if there was one, so it returns an
`Option` so `None` can indicate no separate directory. The first tuple
value is always a valid directory since there's always a current
directory to use if no argument was provided on the command line.

The returned values are also converted to `PathBuf` with absolute paths.

Back in the `init_command()` method, if
there was a separate directory provided, then I create the link file at
the location returned as the first argument in the tuple, writing the
path to the separate directory.

At this point we know where to create the actual repository directory
and contents, so at line 20 in `init_command()` I go and create that
directory. Then as shown next I create the required subdirectories:

I have defined constants for the various directory names e.g. `.git/objects/pack`
or `.git/refs/heads` and what not. Next I create the `.git/HEAD` file

If the user passed in the `-b` or
`--initial-branch` option I use that
value, otherwise I use the value specified in
`~/.gitconfig`. If there are neither,
then the current Git default `master` is
used.

### A Note on Git Config

You'll have noticed I have a static called `GIT_CONFIG` which is a map. I use
the `lazy-static` crate to define it and a few other things:

I will touch on the `git config` command in a subsequent blog post, but for
now I am just reading `~/.gitconfig` which is considered "global" config and
what you'd see with `git config --list --global`.

## Coming Up Next

In this blog I hope you gained some insight into both how Git builds and
structures its repository, as well as some increased understanding of
the `clap` crate. As we get into some of the other Git commands, I'll
continue to touch on `clap` when there's something new or interesting.

Stay tuned for subsequent blogs coming soon. I will get into the
`git hash-object` command which helps
understand the on-disk format of objects. This will then lead nicely
into the `git cat-file` command to
"reverse" the process ... going from the on-disk object format back to
human readable content.
As always, please comment if you notice anything I could do better with
my Rust coding as I'm doing this to learn Rust better. If there are
idiomatic things that I could do that I'm not, let me know! And any
other comments on the content or possible future content, let me know!

Please clap (pun intended) and/or follow and/or [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu) if you liked this blog. Thanks!

## Correction

Ooops! I found a bug in the way I was handling the `git init --separate-git-dir`
option. The problem stems from the fact that the directory specified
with `git init` like `git init foo` is the **_parent_** of the repository to create
i.e. that will create `foo/.git`. However, the directory given to
`--separate-git-dir` is the actual place to create the repo files, not the parent
of a `.git` directory. Here is the updated code. (I also changed the constants
I have to remove ".git/" as a prefix, but I don't include those minor changes here.)
