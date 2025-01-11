---
title: Learning Git Internals with Rust - Part 4
description: git cat-file
date: 08-25-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: false
---

In this post we'll cover the Git `cat-file` command. Previous posts in this
series are

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object
- [Part 3](learning-git-pt3) — refactoring

The Git [`cat-file`](https://git-scm.com/docs/git-cat-file) command let's you
dump the contents of a Git object. You cannot view Git object files directly
since they are compressed as well as having headers, as we saw in the second
post on `hash-object`. The `cat-file` command is essentially the inverse of the
`hash-object` command.

With `cat-file` you have four primary options with respect to viewing the file:

- pretty-print the content --- the `-p` command-line option
- print the type of the object --- the `-t` command-line option
- print the size of the object --- the `-s` command-line option
- check for the existence of the object --- the `-e` command-line option

Each option is exclusive of the others --- you can only specify one. I
will show how this is achieved using `clap` (well, one way). There are other
things you can do, such as batch (i.e. bulk) operations, but I will not cover
that in this post. You can learn more
[here](https://git-scm.com/docs/git-cat-file#_batch_output).

## Handling the command-line options

### Preparatory Work

As mentioned, the `-e` option just tests for the existence of the object and
the process return code should be 0 if found, 1 if there's a problem ---
standard Unix. At the same time I wanted to keep the details local to the
command, and have the `main()` method be ignorant. There was also some code
duplication creeping in with respect to the error handling, so what I have done
is included the [`thiserror`](https://docs.rs/thiserror/latest/thiserror/)
crate, and defined my own error enum:

```rust
pub type GitResult<T> = Result<T, GitError>;
pub type GitCommandResult = GitResult<()>;

#[derive(Error, Debug)]
pub(crate) enum GitError {
    #[error("Not a valid object name {obj_id}")]
    InvalidObjectId { obj_id: String },
    #[error("I/O error")]
    Io {
        #[from]
        source: io::Error,
    },
}
```

So far the commands I have implemented have only had two errors --- either an
underlying I/O error (e.g. couldn't open a file) or something wrong with the
provided object id from the user. The `thiserror` crate makes it easy to define
custom error types. I
[wrote a blog](https://medium.com/dev-genius/improving-your-error-handling-in-rust-5d348a6d9286)
on it, so I won't go into details here. Check it out if you like.

For convenience I also created some type aliases for custom `Result` types,
rather than using the `std::io::Result` everywhere as I had been doing.

The `main()` method changed to have the return type be `std::process::ExitCode`
and I return the exit code explicitly based on the result.

```rust
    let result = match git.command {
        Commands::Init(args) => init::init_command(args),
        Commands::CatFile(args) => cat_file::cat_file_command(args),
        Commands::HashObject(args) => hash_object::hash_object_command(args),
        Commands::Config(args) => config::config_command(args),
    };

    if result.is_ok() {
        ExitCode::from(0)
    } else {
        eprintln!("{}", result.err().unwrap());
        ExitCode::from(1)
    }
```

I then changed all the return signatures from the various command handlers to
return `GitCommandResult` e.g.

```rust
pub(crate) fn cat_file_command(args: CatFileArgs) -> GitCommandResult {
...
```

> [!info]
> At some point I will probably refactor these command entry points such that
> there is a trait for a command, to make it explicit that each handler should
> take `args` and return a `GitCommandResult` but it's not worth it at this
> point.

I also went through and pretty much everywhere replaced `io::Result` with
`GitResult`.

## Clap Changes

With that work out of the way, I updated the `CatFileArgs` struct so that the
`-e/-p/-s/-t` options were mutually exclusive. To do this in `clap` you can use
groups. One way to do that is to add a `group` option to the `#[arg]`
definition as so:

```rust
#[derive(Debug, Args)]
pub(crate) struct CatFileArgs {
    /// pretty-print object's content
    #[arg(short, default_value = "false", group = "operation")]
    pretty: bool,
    /// show object type
    #[arg(short = 't', default_value = "false", group = "operation")]
    obj_type: bool,
    /// allow -s and -t to work with broken/corrupt objects
    #[arg(long, default_value = "false")]
    allow_unknown_type: bool,
    /// show object size
    #[arg(short, default_value = "false", group = "operation")]
    show_size: bool,
    /// exit with zero when there's no error
    #[arg(short, default_value = "false", group = "operation")]
    exists: bool,
    #[arg(name = "object")]
    object: String,
}
```

Here I added `group = "operation"` to group these mutually exclusive options
together. You can read more about the `clap` group support
[here](https://docs.rs/clap/latest/clap/_derive/_tutorial/chapter_3/index.html#argument-relations).
As you may have noticed if you read the earlier blogs, I also added doc comments
for each struct field. This is one way to tell `clap` what to use to print the
help text. Here I just copied the text from the Git `cat-file` help text.

## Pretty-Print Option

All of the options require the same up front work ... finding the object based
on the object id and reading it. At that point, the options for existence, type
and size are trivial. For existence, we don't even need to read the file --- we
just need to see if we can find it. So I short circuit that in the
`cat_file_command()`

```rust
pub(crate) fn cat_file_command(args: CatFileArgs) -> GitCommandResult {
    let result = util::find_object_file(&args.object);

    let path = match result {
        // if -e option (test for object existence) return Ok now, don't continue
        Ok(_) if args.exists => return Ok(()),
        Ok(p) => p,
        // if error already, return now, no point continuing regardless of -e option or not
        Err(e) => return Err(GitError::from(e)),
    };
```

If it's not the `-e` option, then I read the file. At that point, the only
interesting thing is printing the content. For the size and type options, I just
print those values.

```rust
    if args.pretty {
        match GitObjectType::from(obj_type) {
            GitObjectType::Blob | GitObjectType::Commit => {
                print!("{}", util::bytes_to_string(content));
            }
            GitObjectType::Tree => {
                handle_cat_file_tree_object(obj_len, content)?;
            }
        }
    } else if args.obj_type {
        println!("{obj_type}");
    } else if args.show_size {
        println!("{obj_len}");
    }
```

So let's focus on the pretty-printing. Here, the `blob` and `commit` types are
the same and trivial --- the content is just printed out. Where it gets more
involved is handling the `tree` object. This is because each entry in the tree
object is variable length and so the overall object size is variable length.

Each entry of the tree object contains the file permissions (standard Unix `mode`
octal format) and a filename. The filename makes the row and resulting full Git
object variable length. The file name is terminated by a null-byte and then there's
the 20-byte object hash:

```bash
[filemode][SP][filename]\0[hash-bytes]<repeat>
```

The pretty-printed output of a tree object looks like

```bash
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

```rust
fn handle_cat_file_tree_object(content: &[u8]) -> GitResult<()> {
    let mut consumed = 0usize;
    let len = content.len();
    while consumed < len {
        let index = util::find_null_byte_index(&content[consumed..]);
        let end = consumed + index;
        assert!(end < content.len());

        let mode_and_file = &mut content[consumed..end].split(|x| *x == b' ');
        let mode = util::bytes_to_string(mode_and_file.next().unwrap());
        let file = util::bytes_to_string(mode_and_file.next().unwrap());
        consumed += index + 1; // +1 for null byte

        let hash = hex::encode(&content[consumed..consumed + 20]);
        consumed += 20; // sizeof SHA-1 hash

        let obj_contents = &mut util::get_object(hash.as_str())?;
        let index = util::find_null_byte_index(obj_contents);
        let (obj_type, _) = util::get_object_header(obj_contents, index);

        println!("{:0>6} {} {}    {}", mode, obj_type, hash, file);
    }

    Ok(())
}
```

The code iterates through the `content` buffer, maintaining an index `consumed`
as data gets parsed. First the file mode and name is found by first finding
the null byte to find the end of the file name and then splitting that on the
`b' '` separator. Next (line 14) the object id gets parsed. Given the object id,
the code looks up the object to get the object type. The extracted tree info is
printed to `stdout`. Repeat while there is still content.

This is a pretty straightforward, brute-force approach. Could it be optimized?
Perhaps. In particular, extracting the object type currently requires reading
the entire referenced object (line 17) so it can parse the header; the rest of
the object content is discarded.

That said, this implementation of the `cat-file` command works for `blob`,
`commit` and `tree` objects and the `-e`, `-s`, `-t` and `-p` options.

---

Depending on how you might try this out given the current implementation, you
might find the code unable to find an object you specify or one that's
referenced in a `tree` object ...

```bash
$ rust-git cat-file -p 25eaa3bf19c719f454216e163cf0a072c6393783
Not a valid object name 25eaa3bf19c719f454216e163cf0a072c6393783
```

And in fact if I look in .git/objects there is no such file

```bash
$ ls .git/objects/25/eaa3bf19c719f454216e163cf0a072c6393783                                                                                                                                                          2 ↵
".git/objects/25/eaa3bf19c719f454216e163cf0a072c6393783": No such file or directory (os error 2)
```

This particular object was "packed" up into a pack file.

```bash
$ git verify-pack -v .git/objects/pack/pack-ba0faee43dc0116b7966fe1beae5c44f29ca0779.idx | grep 25eaa3bf19c719f454216e163cf0a072c6393783                                                                             130 ↵
25eaa3bf19c719f454216e163cf0a072c6393783 blob   38 51 57043 1 0fc92519924a0af1fa2fb5fdbe03cc3904812a8e
```

Also, if you try other Git ways to specify objects like for example with `HEAD`
or such human-readable names, my code doesn't work

```bash
$ rust-git cat-file -p HEAD
Not a valid object name HEAD
```

Why? Well, it's not smart enough yet :). The first issue with using the object
hash has to do with how Git optimizes space with ["pack" files](https://git-scm.com/book/en/v2/Git-Internals-Packfiles).
The issue with something like `HEAD` has to do with the notion of references
which I mentioned in the [first post](https://medium.com/gitconnected/learning-git-internals-with-rust-96d05592b902).
If you recall, something like `HEAD` is actually a file in
`.git/refs/heads/<branch-name>` which then contains an object hash:

```bash
$ cat .git/refs/heads/more-rust-git
42b31b7976b4a199affdf1f69721bbf86ec70190
```

You can refer to the [`gitrevisions`](https://git-scm.com/docs/gitrevisions)
page to see details on this.

In the next post I will talk about pack files and enhance the `cat-file` command
to be able to find packed objects. I will probably also add the support for
the ref names like `HEAD`.

---

As always if you have any suggestions how to improve my Rust coding skills,
please comment.

If you enjoyed this content, and you'd like to support me, consider
[buying me a coffee](https://www.buymeacoffee.com/raysuliteanu)
