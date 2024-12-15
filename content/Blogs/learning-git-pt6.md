---
title: Learning Git Internals with Rust - creating tree and commit objects
description: Part 6 - tree and commit objects
created: 2024-10-07
tags:
  - git
  - rust
  - programming
  - blog
draft: false
---

In this blog I continue my journey with Rust and Git, focusing on creating the
last two object types in Git — the `tree` and the commit. As you may recall
from previous post in this series, a `tree` object represents a single level of
a directory tree, with the file’s name, permissions and object hash. A commit
object is what most people are familiar with, and it contains references (via
object hashes) to a `tree` for files in the commit, a reference to the parent
commit if any (e.g. the very first commit in a repo has no parent), the name of
the author and committer (which are allowed to be different) and finally the
commit message. If you sign your commit, this ends up as text in the comment.

For easy reference, here are the previous posts.

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object
- [Part 3](learning-git-pt3) — refactoring
- [Part 4](learning-git-pt4) — git cat-file
- [Part 5](learning-git-pt5) — git ls-tree

In the previous post I showed how to print the `tree` object. Now we will createone, since that is the prerequisite for being able to create the commit object. Let’s get to it.

> I will not be implementing the Git staging area, so there will be “git add” (really git update-index) command required. I will just be creating the `tree` object from the contents of the current directory.

## Creating a `tree` object

The `git write-tree` command for our purposes doesn’t take any command-line options. It traverses the directory tree and for each file creates a new `blob` and if it’s a directory recurses down the directory tree. It does this first, so it’s a depth-first walk … otherwise it wouldn’t know the hash to use for the directories (i.e. trees) at the current level. After creating all the required objects, `write-tree` writes the hash of the `tree` object for the “root” to `stdout`.

Since we are creating a hierarchical tree structure, this implementation will be a recursive one. I created a new module call `write_tree` and following the pattern I’ve established, the `main()` method has a new command to process:

```rust
fn main() -> ExitCode {
env_logger::init();

    let git = Git::parse();

    let result = match git.command {
        Commands::Init(args) => init::init_command(args),
        Commands::CatFile(args) => cat_file::cat_file_command(args),
        Commands::HashObject(args) => hash_object::hash_object_command(args),
        Commands::Config(args) => config::config_command(args),
        Commands::LsTree(args) => ls_tree::ls_tree_command(args),
        Commands::WriteTree => write_tree::write_tree_command(),
```

The way I implemented the recursion, the `write_tree::write_tree_command()` function calls a `write_tree()` function that takes the path of the current directory to process. Every time `write_tree()` sees a directory, it recurses, concatenating the new directory name to the current path. On the other hand, if it’s a regular file, I create a blob for it. In both cases, I keep track of the new entry in a new `struct TreeEntry`.

```rust
pub(crate) fn write_tree_command() -> GitCommandResult {
    let sha1 = write_tree(std::env::current_dir()?)?;
    println!("{sha1}");

    Ok(())
}

fn write_tree(path: PathBuf) -> GitResult<String> {
    trace!("write_tree({:?})", path);
    let dir = std::fs::read_dir(&path)?;

    let mut tree = Tree {
        entries: Vec::new(),
    };

    for entry in dir {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();

        trace!("processing dir entry: '{name}'");

        let tree_entry = if entry.metadata()?.is_dir() {
            if name == util::GIT_DIR_NAME {
                continue;
            }

            let sha1 = write_tree(path.join(&name))?;
            make_tree_entry(name, entry, sha1)?
        } else {
            let mut file = std::fs::File::open(path.join(&name))?;
            let sha1 = hash_object::hash_object(&make_hash_object_args("blob"), &mut file)?;
            make_tree_entry(name, entry, sha1)?
        };

        tree.entries.push(tree_entry);
    }

    // git sort algo: https://github.com/git/git/blob/master/tree.c#L101

    tree.entries.sort_by(|x, y| {
        let common_len = std::cmp::min(x.name.len(), y.name.len());
        match x.name[..common_len].cmp(&y.name[..common_len]) {
            Ordering::Equal => {
                let x_name = x.name.clone();
                let x = if x.mode == "40000" {
                    x_name + "/"
                } else {
                    x_name
                };

                let y_name = y.name.clone();
                let y = if y.mode == "40000" {
                    y_name + "/"
                } else {
                    y_name
                };

                x.cmp(&y)
            }
            o => o,
        }
    });

    let mut entries: Vec<u8> = Vec::new();
    let mut size = 0;
    for entry in tree.entries.iter_mut() {
        let mode_and_name = format!("{} {}\0", entry.mode, entry.name);
        size += entries.write(mode_and_name.as_bytes())?;
        size += entries.write(hex_to_bytes(entry.sha1.as_str())?.as_slice())?;
    }

    let mut temp = util::make_temp_file()?;
    let n = temp.write(entries.as_slice())?;
    assert_eq!(n, size);
    temp.flush()?;
    let mut temp = temp.reopen()?;
    let hash = hash_object::hash_object(&make_hash_object_args("tree"), &mut temp)?;

    Ok(hash)
}

#[derive(Debug)]
struct TreeEntry {
    name: String,
    mode: String,
    sha1: String,
}

#[derive(Debug)]
struct Tree {
    entries: Vec<TreeEntry>,
}
```

One thing that turned out to be complicated and a real pain in the arse is figuring out and implementing the way Git sorts files in a tree object. I had to look it up in the [Git source](https://github.com/git/git/blob/master/tree.c#L101) and rewrite it in Rust. Could I have done it better? Perhaps. But it works 😃. Basically it sorts files before directories if the names match.

Take this example directory structure:

```text
.
└── src
    ├── command
    │   └── hello.rs
    ├── command.rs
    └── goodbye.rs
```

If you commit this and look at the tree object for `src` you’ll see something like:

```sh
$ git cat-file -p 38089d625d022e1cc25de9fe2c0b34335427e195
100644 blob aa56d324fe1b80ae8ff3021d8f9bace41dd8c4f5    command.rs
040000 tree aaa96ced2d9a1c8e72c56b253a0e2fe78393feb7    command
100644 blob dd7e1c6f0fefe118f0b63d9f10908c460aa317a6    goodbye.rs
```

Note that `command.rs` is before `command`.

## Refactoring writing objects

To support re-using the blob object writing I implemented way back in Part 2, I refactored to allow passing the type of the object being written. The `HashObjectArgs` structure already had a field or the type of object, and whether the -w option was passed to git hash-object. So I make use of that here by creating and passing an instance of it to `hash_object::hash_object()` along with a temp file containing the contents of the `blob` or `tree` object. The main refactoring was to have `hash_object()` pass the `HashObjectArgs` on to `hash_object::encode_content()` to use the object type when creating the header. Before it had been hard-coded to “blob”. Note that this refactoring will of course come in handy for supporting `git commit-tree`.

```rust
fn encode_content(args: &HashObjectArgs, input: &mut File, output: &NamedTempFile) -> GitResult<String> {
    let writer = BufWriter::new(output);
    let mut hasher = HashObjectWriter::new(writer);

    let len = input.metadata()?.len();
    let header = format!("{} {}\0", args.obj_type, len);
    debug!("encode_content: file header '{}'", header);
    write!(hasher, "{}", &header)?;
```

And that’s really it for writing tree objects!

## Creating a commit object

Compared to some of the other things I’ve had to implement, creating a commit object was relatively straightforward. It was really about hooking together bits I’ve already implemented. There is no fancy formatting beyond the standard header/content split and as I just mentioned, we already have a way to create those objects via `hash_object::hash_object()`.

> One refactoring I will probably do is move this object-writing stuff from
> hash_object module to object module, since that’s where I have the object
> reading stuff. But I haven’t done that yet.

One thing I did to simplify this implementation for now is to only support three command line options.

- `-p` for the parent
- `-m` for the commit message
- hash to specify the tree we’re committing

Also, with `commit-tree` you can have multiple parents (or none) so you could have multiple `-p` (think merges). I am only supporting one parent. You can also have multiple `-m` for multiple commit messages, one paragraph per `-m`. I am also not handling that currently.

To view the commit format you can do

```sh
$ git cat-file -p HEAD
tree d23239051b1703985c17f12f23fb35b39dec41ac
author Ray Suliteanu <raysuliteanu@gmail.com> 1728327330 -0700
committer Ray Suliteanu <raysuliteanu@gmail.com> 1728327330 -0700

test
```

There is always an extra newline (0xA) after the committer. The timestamps you see are the standard Unix epoch value in seconds with the UTC offset. The author and committer names come from the Git config, if set, with a fallback to `user.email` and `user.name`.

```rust
pub(crate) fn commit_tree_command(args: CommitTreeArgs) -> GitCommandResult {
    // make sure tree exists
    let tree = object::GitObject::read(args.tree.as_str())?;
    assert!(tree.sha1.starts_with(args.tree.as_str()));
    let tree_hash = tree.sha1;

    let email_default = || GIT_CONFIG.get("user.email").expect("valid user.email");
    let user_default = || GIT_CONFIG.get("user.name").expect("valid user.name");

    let author_email = GIT_CONFIG.get("author.email").unwrap_or_else(email_default);
    let author_name = GIT_CONFIG.get("author.name").unwrap_or_else(user_default);

    let committer_email = GIT_CONFIG
        .get("committer.email")
        .unwrap_or_else(email_default);
    let committer_name = GIT_CONFIG
        .get("committer.name")
        .unwrap_or_else(user_default);

    let mut commit: Vec<u8> = Vec::new();
    let mut size = commit.write(format!("tree {}\n", tree_hash).as_bytes())?;

    if let Some(parent_arg) = args.parent {
        let parent = object::GitObject::read(&parent_arg)?;
        size += commit.write(format!("parent {}\n", parent.sha1).as_bytes())?;
    }

    let epoch = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("valid epoch time")
        .as_secs();

    let tz = get_tz();

    size += commit.write(
        format!(
            "author {} <{}> {} {}\n",
            author_name, author_email, epoch, tz
        )
        .as_bytes(),
    )?;
    size += commit.write(
        format!(
            "committer {} <{}> {} {}\n",
            committer_name, committer_email, epoch, tz
        )
        .as_bytes(),
    )?;

    size += commit.write("\n".as_bytes())?;

    if let Some(message) = args.message {
        size += commit.write(format!("{}\n", message).as_bytes())?;
    }

    let mut temp = util::make_temp_file()?;
    let n = temp.write(&commit)?;
    assert_eq!(n, size);
    temp.flush()?;
    let mut temp = temp.reopen()?;
    let hash = hash_object::hash_object(&make_hash_object_args("commit"), &mut temp)?;

    println!("{hash}");

    Ok(())
}
```

I covered a bit on the Git config support in [Part 1](https://medium.com/gitconnected/learning-git-internals-with-rust-96d05592b902). Take a look at that if you want to see where the `GIT_CONFIG` is implemented.

Above, when I call `GitObject::read()` I do this to validate that the values
provided by the user on the command line are valid hashes. If they are not `read()` returns an `Err`.

To get the timezone value I used the `chrono` crate, partly just to learn a little
about it vs. the standard library. The timestamp is just using the `std::time`
module. To get the timezone I wrote this:

```rust
fn get_tz() -> String {
    let local_time = Local::now();
    let offset = local_time.offset();
    let local_offset = offset.local_minus_utc();
    format!("{:+}{:02}", local_offset / 3600, (local_offset % 3600) / 60)
}
```

And there you have `git commit-tree`.
