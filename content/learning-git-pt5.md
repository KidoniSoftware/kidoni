---
title: Learning Git Internals with Rust - Part 5
description: git ls-tree
date: 10-06-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: false
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

![git object tree](images/git-object-tree.png)

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

![raw tree object](images/raw-tree-object.png)

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

```rust
#[derive(Debug, PartialEq)]
pub(crate) enum GitObjectType {
    Blob,
    Tree,
    Commit,
}

pub(crate) struct GitObject<'a> {
    pub(crate) kind: GitObjectType,
    pub(crate) sha1: &'a str,
    pub(crate) size: usize,
    pub(crate) body: Option<Vec<u8>>,
}

impl GitObject<'_> {
    pub(crate) fn read(obj_id: &str) -> GitResult<GitObject> {
        trace!("read({obj_id})");
        let path = find_object_file(obj_id)?;
        let file = std::fs::File::open(path)?;
        let reader = BufReader::new(file);
        let contents = GitObject::decode_obj_content(reader)?;
        let mut header_and_body = contents.splitn(2, |b| *b == 0);
        let header = header_and_body.next().unwrap();
        let body = header_and_body.next().unwrap();
        let (obj_type, size) = GitObject::get_object_header(header)?;

        Ok(GitObject {
            kind: obj_type.into(),
            sha1: obj_id,
            size,
            body: Some(body.to_vec()),
        })
    }

    fn get_object_header(content: &[u8]) -> GitResult<(String, usize)> {
        let header = &mut content.splitn(2, |x| *x == b' ');
        let obj_type = bytes_to_string(header.next().unwrap());
        let obj_len_bytes = header.next().unwrap();
        match u8_slice_to_usize(obj_len_bytes) {
            None => Err(GitError::ReadObjectError),
            Some(obj_len) => Ok((obj_type, obj_len)),
        }
    }

    fn decode_obj_content(mut reader: impl BufRead) -> GitResult<Vec<u8>> {
        let content: &mut Vec<u8> = &mut Vec::new();
        let _ = reader.read_to_end(content)?;
        let mut decoder = ZlibDecoder::new(&content[..]);
        let mut decoded_content: Vec<u8> = Vec::new();
        decoder.read_to_end(&mut decoded_content)?;

        Ok(decoded_content)
    }
}
```

A couple of the utility functions from `util` came along and are now part of the
`GitObject` implementation. The `GitObject` `read()` method only decodes the
object header, since they are all the same. The content specific to a specific
type of Git object is stored as bytes in the `body` field of the `GitObject`
struct. The `util.rs` module now essentially just contains stuff related to
finding Git directories.

The other main refactoring was to move the `tree` object printing that was in
`cat-file` for dumping `tree` objects into the new `ls-tree` command handling.

```rust
fn handle_cat_file_tree_object(obj: GitObject) -> GitResult<()> {
    let args = LsTreeArgs::default();
    ls_tree::print_tree_object(&args, obj)
}
```

I was also able to simplify the tree printing function itself, which I'll show
later.

### ls-tree command

Following the pattern I've established I created a new `ls-tree` module in the
`commands` module and a new arguments structure `LsTreeArgs` for the command-line
options handled by `clap`.

```rust
#[derive(Debug, Args, Default)]
pub(crate) struct LsTreeArgs {
    /// Show only the named tree entry itself, not its children.
    #[arg(long, default_value = "false")]
    name_only: bool,

    /// Show only the named tree entry itself, not its children.
    #[arg(short, default_value = "false")]
    dir_only: bool,

    /// Recurse into sub-trees.
    #[arg(short, default_value = "false")]
    recurse: bool,

    /// Show tree entries even when going to recurse them. Has no effect if -r was not passed.  -d implies -t.
    #[arg(short = 't', default_value = "false")]
    show_trees: bool,

    /// Show object size of blob (file) entries.
    #[arg(short = 'l', long = "long", default_value = "false")]
    show_size: bool,

    #[arg(name = "tree-ish")]
    tree_ish: String,

    /// When paths are given, show them (note that this isn’t really raw pathnames, but rather a list of
    /// patterns to match). Otherwise implicitly uses the root level of the tree as the sole path argument.
    #[arg(name = "path")]
    path: Option<Vec<String>>,
}
```

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
output options is in the `print_tree_object()` method shown later.

```rust
pub(crate) fn ls_tree_command(args: LsTreeArgs) -> GitCommandResult {
    ls_tree(&args.tree_ish, &args)
}

pub(crate) fn ls_tree(obj_id: &String, args: &LsTreeArgs) -> GitCommandResult {
    trace!("ls_tree({obj_id})");
    match GitObject::read(obj_id) {
        Ok(obj) => match obj.kind {
            GitObjectType::Tree => {
                // format and print tree obj body
                print_tree_object(&args, obj, None)
            }
            GitObjectType::Commit => {
                // get tree object of commit and print that
                let commit = commit::Commit::from(obj);
                ls_tree(&commit.tree, args)
            }
            GitObjectType::Blob => {
                debug!("cannot ls-tree a blob");
                Err(GitError::InvalidObjectId {
                    obj_id: args.tree_ish.to_string(),
                })
            }
            _ => unreachable!("due to other branches")
        },
        Err(_) => {
            debug!("cannot read object file for id '{obj_id}'; trying as a tag ...");
            // could be that the arg_id is not an object (blob/commit/tree)
            // check for tag
            match tag::Tag::get_tag(obj_id) {
                Some(tag) => ls_tree(&tag.obj_id, args),
                None => {
                    debug!("not a tag {obj_id}");
                    // not a tree or a commit or a tag, no good
                    Err(GitError::InvalidObjectId {
                        obj_id: obj_id.to_string(),
                    })
                }
            }
        }
    }
}
```

I split the functions into a public `ls_tree_command()` called by `main()` and
an `ls_tree()` that can be recursively called if the object hash is not a `tree`
object identifier.

### Tags

To handle tags, I created a new `tag` module and `Tag` struct. Tags technically
are not objects but references ("refs") and live in `.git/refs/tags` not
`.git/objects`.

```rust
pub(crate) struct Tag {
    pub name: String,
    pub path: PathBuf,
    pub obj_id: String,
}

impl Tag {
    pub(crate) fn get_tag(name: &str) -> Option<Tag> {
        let path = get_git_tags_dir().join(name);
        match File::open(path) {
            Ok(mut file) => {
                let mut obj_id = String::new();
                match file.read_to_string(&mut obj_id) {
                    Ok(_) => Some(Tag {
                        name: name.to_string(),
                        path: get_git_tags_dir().join(name),
                        obj_id,
                    }),
                    Err(_) => None,
                }
            }
            Err(_) => None,
        }
    }
}
```

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

```rust
pub(crate) struct Commit {
    sha1: String,
    pub(crate) tree: String,
    parent: String,
    author: String,
    committer: String,
    comment: String,
}

impl From<GitObject<'_>> for Commit {
    fn from(object: GitObject) -> Self {
        let body = object.body.unwrap();
        let mut reader = body.reader();

        let tree = get_entry(&mut reader, "tree");
        let parent = get_entry(&mut reader, "parent");
        let author = get_entry(&mut reader, "author");
        let committer = get_entry(&mut reader, "committer");

        let mut comment = String::new();
        let _ = reader.read_to_string(&mut comment);

        Self {
            sha1: object.sha1.to_string(),
            tree,
            parent,
            author,
            committer,
            comment,
        }
    }
}

fn get_entry(reader: &mut impl BufRead, name: &str) -> String {
    let mut entry = String::new();
    let _ = reader.read_line(&mut entry);
    let mut n = entry.splitn(2, ' ');
    assert_eq!(n.next(), Some(name));
    n.next().unwrap().trim().to_string()
}
```

### Printing tree objects

There are a few interesting aspects to printing the tree object, mostly around
recursion and filtering. I have not implemented the filtering as of now.

```rust
pub fn print_tree_object(
    args: &LsTreeArgs,
    obj: GitObject,
    path_part: Option<String>,
) -> GitResult<()> {
    // each entry is 'mode name\0[hash:20]
    let mut body = obj.body.unwrap();

    loop {
        if body.is_empty() {
            break;
        }

        // 1. split into two buffers, `[mode_and_name]0[rest]` with the 0 discarded
        let mut split = body.splitn(2, |b| *b == 0);
        let mode_and_file = split.next().unwrap();
        let mut rest = split.next().unwrap();

        // 2. spit the mode_and_name buffer into the mode and the name, which are separated by ' '
        let mut split = mode_and_file.split(|b| *b == b' ');
        let mode = util::bytes_to_string(split.next().unwrap());
        let filename = util::bytes_to_string(split.next().unwrap());

        // 3. read the next 20 bytes from `rest` which is the object hash
        let mut hash_buf = [0u8; 20];
        rest.read_exact(&mut hash_buf)?;

        // 4. point body at the remaining bytes for the loop
        body = rest.to_vec();

        // 5. using the hash, look up the referenced object to get its type
        let hash = hex::encode(hash_buf);
        let entry_obj = GitObject::read(hash.as_str())?;
        let kind = &entry_obj.kind;

        let path = create_file_name(&path_part, filename);

        // 6. if name_only then only print the name :)
        if args.name_only {
            if *kind == GitObjectType::Tree && args.recurse {
                print_tree_object(args, entry_obj, Some(path))?;
            } else {
                println!("{}", path);
            }

            continue;
        }

        if *kind == GitObjectType::Tree && args.recurse {
            print_tree_object(args, entry_obj, Some(path))?;
        } else {
            print!("{:0>6} {} {}", mode, kind, hash);

            if args.show_size {
                let len = entry_obj.size;
                if entry_obj.kind == GitObjectType::Tree {
                    print!("{: >8}", "-");
                } else {
                    print!("{: >8}", len);
                }
            }

            println!("\t{}", path);
        }
    }

    Ok(())
}

fn create_file_name(path: &Option<String>, filename: String) -> String {
    match path {
        Some(p) => p.to_owned() + "/" + filename.as_str(),
        None => filename,
    }
}
```

Recall our diagram from earlier (slightly enhanced).

![enhanced raw tree object](images/enhanced-raw-tree-obj.png)

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

If you enjoyed this content, and you'd like to support me, consider
[buying me a coffee](https://www.buymeacoffee.com/raysuliteanu)
