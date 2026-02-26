---
title: Using thread locals in Rust
description: one approach to thread-local data in Rust
date: 2024-06-14
tags:
  - blog
  - rust
  - programming
  - multithreading
draft: false
---

As I continue my journey learning Rust, I thought I'd share some
learning related to multithreading and thread locals.

I came across an interesting new site called [CodeCrafters](https://codecrafters.io).
The site is another learning site supporting multiple programming languages, but
they focus on specific "challenges" with specific tasks to accomplish for each
challenge. I've worked through a few of them, and I used threads and thread
locals on the HTTP server challenge.

{{% callout type="note" %}}
I am not affiliated with CodeCrafters in any way. I just found it interesting
and since I developed the code I use in this example from working on one of
their challenges, I thought I'd give some acknowledgement. I don't get any
kind of "kickback" for mentioning them.
{{% /callout %}}


As the task was to build a basic HTTP server, I decided to use the `tokio` crate.
One use case of the CodeCrafter's HTTP server challenge was supporting
downloading of files. The HTTP server would be provided a command line option
specifying a base directory from which files would be downloaded. Then the HTTP
server would expose an endpoint a client could invoke to download some file. So
given:

```sh
my_server --directory /tmp
```

and a client invocation like

```sh
curl localhost:8080/files/foo.txt
```

the server should return a file `/tmp/foo.txt` if it exists.

The main processing loop using `tokio` looks something like this:

```rust
use std::io;
use tokio::net::{TcpListener, TcpStream};

#[tokio::main(flavor = "multi_thread")]
async fn main() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    loop {
        let (mut stream, addr) = listener.accept().await?;
        println!("Connection from {addr}");

        tokio::spawn(async move { process_request(&mut stream).await });
    }
}

async fn process_request(stream: &mut TcpStream) {
    todo!()
}
```

In my approach, the `process_request()` function will handle all the HTTP
protocol details like parsing the initial protocol line to extract what the
client is asking for, and any headers. So assuming the client executes the `curl`
command shown above, the HTTP server should get

`GET /files/foo.txt HTTP/1.1`

That means of course it needs to look for `foo.txt` in some place that was
provided to the server at startup via `--directory`. I decided to use the `clap`
crate for this, with the `derive`feature.

```rust
#[derive(Parser)]
struct Cli {
    #[arg(long)]
    directory: Option<String>,
    #[arg(short, long)]
    port: Option<u16>,
}
```

(I also added a `--port` option but I'm not doing to discuss that here.)

By using `#[derive(Parser)]` on your struct containing the command line options,
you can now simply call `Cli::parse()` to return an instance of your struct
populated as defined. This post isn't about `clap` so I'll let you
[look that useful crate up on your own](https://docs.rs/clap/latest/clap/).

So now comes the point where you have to decided how to provide the given
directory to the threads executing `process_request()`. I could have just
passed in the directory as a parameter like `process_request(dir)` but that's no
fun :) and also looking ahead there could be other things I'll need to
provide, as well as the fact that the directory is only required for the
one use case of downloading files. So I decided to try and figure out how to use
thread locals.

The `tokio` crate has support for a `task_local!` macro. It's called "task local"
because technically what you spawn using `tokio::spawn` does not necessarily get
run on a new thread. If you want to use threads you actually have to tell the
Tokio runtime about it, which you can do with the `flavor = "multi_thread"`
argument to the `tokio::main` macro ...

```rust
#[tokio::main(flavor = "multi_thread")]
async fn main() -> io::Result<()> {
```

{{% callout type="note" %}}
You need to have the macros, rt and rt-multi-thread features enabled, at a
minimum, for tokio::main, task_local! and flavor = "multi_thread" to work.
Some other features are required as well to get the net and io stuff e.g.

`tokio = { version = “1.38.0”, features = [“macros”, “rt-multi-thread”, “rt”, “net”, “io-util”, “fs”] }`
{{% /callout %}}


To contain the current and future "context" I wanted to provide to
spawned threads, I created a struct and then set it as my "task" local
context.

```rust
#[derive(Clone, Copy, Debug)]
struct ThreadLocalContext {
    directory: Option<&'static str>,
}

impl ThreadLocalContext {
    fn new(file_directory: Option<&'static str>) -> Self {
        ThreadLocalContext {
            directory: file_directory,
        }
    }
}

task_local! {
    static CONTEXT : ThreadLocalContext;
}
```

Then all I needed to do was "wrap" my invocation of the
`process_request()` method thusly

```rust
    let listener = TcpListener::bind(host_and_port).await?;
    loop {
        let (mut stream, addr) = listener.accept().await?;
        println!("Connection from {addr}");

        tokio::spawn(
            CONTEXT.scope(context, async move {
                process_request(&mut stream).await
            })
        );
    }
```

To then get access to the context during execution of the task, you call
the `get()` method:

```rust
async fn read_file(filename: &str) -> io::Result<Vec<u8>> {
    if let Some(directory) = CONTEXT.get().directory {
        let dir_file = PathBuf::from(directory).join(filename);
```

That's "all" there is to it. There are caveats, like trait bounds e.g. Clone.
And I'm sure there are other subtleties that I haven't yet encountered since my
usage so far is pretty basic. But it does work! And depending on your situation
you don't need to use `tokio`. There are other implementations of thread locals
including [`std::thread_local!`](https://doc.rust-lang.org/std/macro.thread_local.html#).
