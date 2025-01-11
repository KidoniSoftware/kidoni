---
title: Learning Git Internals with Rust - Part 2
description: Git Objects
date: 07-30-2024
tags:
  - git
  - rust
  - programming
  - blog
draft: false
---

This post continues from where I left off in the first post that covered
creating a new empty repository. You can read it [here](learning-git-pt1). To
briefly summarize the goal of this series of posts, I am on a journey to learn
Rust and for me the best way is doing "real" stuff. In this case I'm looking at
the internals of Git, by implementing some of the many commands available.

After the first post I am able to create a new repository. Let's start to look
at what Git stores and how it does so. As we saw in the first post, after
`git init` we have a directory `.git/objects`. Content is stored in files under
that base objects directory by using a SHA-1 hash of the contents being stored.
Git provides a command `git hash-object` which allows generating the hash based
on content, and _optionally_ writing that file to `.git/objects`. However, that
doesn't mean that `git hash-object` is just a fancy wrapper around `sha1sum` or
similar tools.

```bash
$ echo "hello world" | sha1sum
22596363b3de40b06f981fb85d82312e8c0ed511  -
$ echo "hello world" | git hash-object --stdin
3b18e512dba79e4c8300dd08aeb37f8e728b8dad
```

That's because each object stored by Git has a header in addition to the file
content, identifying the type of object. The object types in Git are

- **blob** --- the actual data the user is adding to Git; if you're committing
  `main.rs` to Git, the content of `main.rs` is stored as a blob object.
- **tree** --- a tree object stores a mapping from object hashes to the
  human-readable file/directory names; it also stores the file permissions (mode).
- **commit** --- this is what most people would think of being stored in a VCS;
  in Git it's basically an aggregate --- it references tree objects, stores the
  comment message, metadata like the commit author, possibly the commit signature,
  and such like.

As an example, let's say our initial commit of a new Rust project had a
`Cargo.toml` file and `src/main.rs` and `src/lib.rs` files. You might end up
with an object graph like

![git object tree](images/git-object-tree.png)

Note that in and of themselves, blob objects don't know anything about
themselves --- a complete lack of self-awareness as it were. The fact that blob
`2a3b` holds content for a file we know as `main.rs` that has `0644` file
permission is only captured in the tree object. We will get more into the
details of each as we go along.

One last thing to mention is that all the object contents are encoded/compressed
with ZLib.

### Blobs

Let's start our Rust code looking at blob objects. We are going to implement
some of the `git hash-object` command. First let's look at the command arguments
to be parsed by [`clap`](https://docs.rs/clap/latest/clap/)

```rust
#[derive(Debug, Args)]
struct HashObjectArgs {
    #[arg(short = 't', default_value = "blob")]
    obj_type: String,
    #[arg(short = 'w', default_value = "false")]
    write_to_db: bool,
    #[arg(long, default_value = "false")]
    stdin: bool,
    #[arg(long, default_value = "false")]
    literally: bool,
    #[arg(last = true)]
    file: Option<Vec<OsString>>,
}

```

> [!note]
> I'm not showing all the command arguments available to `git hash-object`.

Everything in `struct HashObjectArgs` should be familiar from my first post,
except for the `file` field at the end, lines 11--12. Many Git commands have a
syntax where a `--` indicates the end of the command line arguments and the
beginning of "raw" arguments, typically file paths. Tell `clap` using
`#[arg(last = true)]`. Combine that with the type `Option<Vec<OsString>>` and we
can now optionally take a list of files e.g.

```bash
git hash-object -- file1 file2 file3
```

Given the `clap` setup and an update to the `match` in `main()` as shown in the
previous post, I wrote a new function `hash_object_command(args)` which
currently only supports the `--stdin` option. I also support the `-w` option
which will create a file in `.git/objects`.

```rust
        let mut stdin = stdin();
        let mut input = Vec::new();
        let read = stdin.read_to_end(&mut input)?;

        let obj_header = format!("{} {read}\0", args.obj_type);
        let obj_header = obj_header.as_bytes();
        let mut buf = Vec::with_capacity(obj_header.len() + input.len());
        buf.append(&mut obj_header.to_vec());
        buf.append(&mut input);

        let hash = generate_hash(&buf);
        let encoded = encode_obj_content(&buf)?;

        if args.write_to_db {
            write_object(&encoded, &hash)?;
        }

        println!("{}", hash);
```

I read all the content into a buffer `input` and then construct the object
header. The object header is of the form `type len\0` --- the object type, in
this case `blob` then a space and the length of the content that follows the
null byte. Then I build a buffer combining the header and the object contents
read from `stdin`. Following that I have three helper functions, to generate
the hash string, encode/compress the file contents with ZLib and write out the
file. Finally the object hash is printed to `stdout`.

```rust
fn generate_hash(buf: &[u8]) -> String {
    let mut hasher = Sha1::new();
    hasher.update(buf);
    let sha1_hash = hasher.finalize();
    hex::encode(sha1_hash)
}

fn encode_obj_content(content: &[u8]) -> io::Result<Vec<u8>> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(content)?;
    let result = encoder.finish()?;
    Ok(result)
}

fn write_object(encoded: &[u8], hash: &str) -> io::Result<()> {
    let (dir, name) = hash.split_at(2);
    let git_object_dir = get_git_object_dir();
    let full_dir = git_object_dir.join(dir);
    let file_path = full_dir.join(name);
    fs::create_dir_all(full_dir)?;

    debug!("writing to {}", file_path.display());

    let mut file = File::create(file_path)?;
    file.write_all(encoded)?;

    Ok(())
}
```

To do the SHA-1 hash, I use the `sha1` crate. Most hash/digest and compression
libraries follow a common pattern

- input all the data to process
- call an "I'm done" function

The `Sha1` type follows this pattern (lines 2--4) and then using the `hex`
crate I take the bytes to produce the 40 character usable string
representation.

To do the ZLib encoding, I use the `flate2` crate, which follows the same
pattern --- lines 9--11.

Finally, if the user provided the `-w` option the `write_object()` method is
called at line 15. First I take the 40 character hash string and split it into
the first 2 characters and the remaining 38, to construct the directory name and
file name respectively. I then construct the `PathBuf` representing
`.git/objects/xx` where `xx` are those first 2 characters. If this directory
needs to be created, I do so. Finally, after constructing the `PathBuf` for the
full path including the filename, I write out the ZLib encoded contents.

Starting from a fresh repository, running this you'll see something like

```bash
$ ls .git/objects/
branches  hooks  info  pack
$ echo "hello world" | rust-git hash-object --stdin -w
3b18e512dba79e4c8300dd08aeb37f8e728b8dad
$ ls .git/objects/
3b  branches  hooks  info  pack
$ ls .git/objects/3b
18e512dba79e4c8300dd08aeb37f8e728b8dad
```

You can use the `git cat-file` command (which we'll get to next post) and verify
that my Rust version "did the right thing" as well as a few other commands you
could run including the "reverse" operation showing the raw contents using
[`pigz`](https://github.com/madler/pigz) (or some other utility that can
decompress ZLib data).

```bash
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

### Next Time

The next blog will go on to implement the `git cat-file` command so we can look
at the contents of objects. It is effectively the reverse of the
`git hash-object` command.

As always, please comment if you notice anything I could do better with my Rust
coding as I'm doing this to learn Rust better. If there are idiomatic things
that I could do that I'm not, let me know! And any other comments on the
content or possible future content, let me know!

If you enjoyed this content, and you'd like to support me, consider
[buying me a coffee](https://www.buymeacoffee.com/raysuliteanu)
