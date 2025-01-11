---
title: Learning Git Internals with Rust - Part 3
description: Rust refactoring
date: 08-20-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: false
---

In this post we continue our journey with Rust and Git. If you haven't read the
previous posts, you can find them here

- [Part 1](learning-git-pt1) — git init
- [Part 2](learning-git-pt2) — git hash-object

> [!info]
> At the end of Part 2 I said the next blog would be on `cat-file`. Sorry for
> the bait and switch, but I wanted to do this refactoring, so I snuck this in.
> We'll definitely get to `cat-file` next time.

While this post is mostly standalone, there are aspects of the prior posts that
will probably help to understand this post better.

This series is about Rust as much as Git, since my purpose is to learn Rust,
more so than to learn Git. So in this post, what I'm going to do is take my
single `main.rs` file and refactor it into several files. I will create a
`commands` module, and move each implemented command into a separate module
within `commands`. I will also separate out utility functions into a `util`
module.

![code refactor](images/learning-git-code-refactor.png)

The directory structure becomes

![refactored code directory tree](images/learning-git-pt3-dir-tree.png)

The `main()` method becomes extremely
basic (`use` statements elided).

```rust
mod commands;
mod util;

fn main() -> io::Result<()> {
    env_logger::init();

    let git = Git::parse();

    match git.command {
        Commands::Init(args) => init_command(args),
        Commands::CatFile(args) => cat_file_command(args),
        Commands::HashObject(args) => hash_object_command(args),
        Commands::Config(args) => config_command(args),
    }
}
```

You could argue --- based on my module diagram above --- that the `mod util`
belongs in `commands/mod.rs` which is probably valid. I left it as it is for
now, to see what other utility methods I might have later. Depending how I
embellish this as I work on these blogs, I might move it.

The `util.rs` file now has the common functions --- functions that are not
specific to any one command. Most of the functions are exposed as `pub(crate)`
but a few are private to the `util` module. Rather than embedding the file here,
you can [view it on GitHub](https://github.com/raysuliteanu/blog-examples/blob/f29760510562a12d9590601e6ba415e3b9ae82a8/rust-git/src/util.rs).

The `commands` module defined in `commands/mod.rs` is also relatively simple at
this point. Other than defining the other command modules, it has the `struct
Git` and `enum Commands` types.

```rust
pub(crate) mod cat_file;
pub(crate) mod config;
pub(crate) mod hash_object;
pub(crate) mod init;

#[derive(Debug, Parser)]
pub(crate) struct Git {
    #[command(subcommand)]
    pub(crate) command: Commands,
}

#[derive(Debug, Subcommand)]
pub(crate) enum Commands {
    Init(InitArgs),
    CatFile(CatFileArgs),
    HashObject(HashObjectArgs),
    Config(ConfigArgs),
}
```

Then as shown above, we have a file for each command module. Each module has
the implementation details for the specific command, moved from the old
`main.rs`. I will not replicate the code here, but you can [view it on GitHub](https://github.com/raysuliteanu/blog-examples/tree/main/rust-git/src/commands).

Each file/module follows the same pattern --- basically the struct for the
command's arguments and a `pub(crate)` function called by `main()` with any
additional private functions needed by that handler function, if any, since
most are in the `util` module. There are some functions in some of the command
modules which could be moved to `util` since they are completely generic and
not specific to Git, but if they're only used (currently) by one command I've
left them in that command module.

The `hash_object` command is one example. The `generate_hash()` and
`encode_obj_content()` methods are completely generic, but I've left them where
they are for now.

```rust
fn generate_hash(content: &[u8]) -> String {
    let mut hasher = Sha1::new();
    hasher.update(content);
    let sha1_hash = hasher.finalize();
    hex::encode(sha1_hash)
}

fn encode_obj_content(content: &[u8]) -> io::Result<Vec<u8>> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(content)?;
    let result = encoder.finish()?;
    Ok(result)
}
```

That about covers the refactoring. Now we'll get back to Git ... next blog will
cover the `cat-file` command as I had indicated in Part 2.

---

As always, please comment if you notice anything I could do better with
my Rust coding as I'm doing this to learn Rust better. If there are
idiomatic things that I could do that I'm not, let me know! And any
other comments on the content or possible future content, let me know!

If you enjoyed this content, and you'd like to support me, consider
[buying me a coffee](https://www.buymeacoffee.com/raysuliteanu)
