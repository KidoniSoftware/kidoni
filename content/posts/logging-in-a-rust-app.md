---
title: Logging in a Rust Application
description: how to use logging in a Rust application
date: 2024-04-07
tags:
  - blog
  - rust
  - logging
  - programming
  - observability
draft: false
---

This blog post is part of a series I'm developing documenting my
evolution as a Rust developer. Currently I'm a newbie, but I'm making
progress.

{{% callout type="note" %}}
As a newbie, please feel free in the comments to elaborate on what I
might be doing wrong, could do better or is not "canonical" Rust.
{{% /callout %}}


Logging is obviously a key aspect of a production-ready application.
While one could use `println!` or `dbg!` or similar Rust macros to achieve
something similar, they are not really a replacement for a real logging
framework. In fact, particularly for (long running) "services" as
opposed to CLIs, many architecture/coding standards prohibit use of the
equivalent to `println!` in whatever language you're using. I myself have set
such standards on projects I've lead.

So as I've been teaching myself Rust, I was naturally interested in what
the Rust ecosystem has in terms of logging capabilities.

The first crate to mention is the [log](https://crates.io/crates/log)
crate. This library provides a standard logging facade API that is then
combined with an actual logging implementation provided by a separate
crate that you as the developer can select per your requirements. This
is similar to `commons-logging` or `SLF4J` in the Java world. To use
`log` in Rust,

```shell
cargo add log
```

or add it manually, but in either case your `Cargo.toml` will end up with

```toml
[dependencies]
log = "0.4.21"
```

To add logging to your application, you then use one of the macros to
log at

- `trace!`
- `debug!`
- `info!`
- `warn!`
- `error!`

There is also a generic `log!` macro which takes the log level as a parameter.
To use these macros just include them in your code, e.g.

```rust
use log::info;

fn main() {
    info!("Hello, world!");
}
```

If you run this now, this is what you'd see:

```shell
$ cargo run
    Finished dev [unoptimized + debuginfo] target(s) in 0.00s
     Running `target/debug/rust-examples`
```

Hey, where's my log message? Well, as I mentioned, the `log` crate just provide
the API. To actually do something you need a log implementation. (Returning to
the Java example, this is the same as needing to include, e.g.
[Logback](https://logback.qos.ch/) as an implementation when using `SLF4J` as
the API.)

Looking at the `log` create documentation you'll see a lot of different possible
logging implementations that you can select from. Choose one based on your
requirements. For this blog I am going to pick a sophisticated implementation
that's inspired by [Logback](https://logback.qos.ch/) and provides a lot of
configuration options. It is called [log4rs](https://docs.rs/log4rs/latest/log4rs/).

```shell
$ cargo add log4rs
    Updating crates.io index
      Adding log4rs v1.3.0 to dependencies.
             Features:
             ...
```

_(I am truncating the output, which lists all the features that are
available.)_

```shell
[dependencies]
log = "0.4.21"
log4rs = "1.3.0"
```

This is not all that is required though. If you were to run the
application now, you'd still not see any output. This is because
`log4rs` requires configuration. This can be done either via a YAML
configuration file, or programmatically. You can read the `log4rs` documentation
for the details, but to briefly summarize, `log4rs` (like `Logback`) has the
notion of loggers, appenders and encoders. An appender is something that
writes (appends) to a log. Encoders define how the log messages are
formatted when written. Examples of appenders include a `console` appender (to
`stdout`) and a `file` appender. Encoders could be a regex `pattern` encoder or
a `json` encoder. Here is a very basic `log4rs` configuration file.

```yaml
appenders:
  console:
    kind: console
    encoder:
      pattern: "{d(%+)(local)} [{t}] {h({l})} {M}:{m}{n}"

root:
  appenders:
    - console
```

You then need to load this configuration and initialize `log4rs`, like so:

```rust
use log::info;

fn main() {
    log4rs::init_file("log_config.yaml", Default::default()).unwrap();
    info!("Hello, world!");
}
```

Finally you will now see a log message, formatted according to the
pattern specified in the configuration file.

```shell
$ cargo run
    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running `target/debug/rust-examples`
2024-04-07T14:37:36.838882622-07:00 [rust_examples] INFO rust_examples:Hello, world!

```

If you change the configuration file to use the JSON encoder like so

```yaml
appenders:
  console:
    kind: console
    encoder:
      kind: json

root:
  appenders:
    - console
```

Now you'll see a JSON formatted equivalent (I've run the output through
`jq` to make it more readable):

```shell
$ cargo run | jq
    Finished dev [unoptimized + debuginfo] target(s) in 0.05s
     Running `target/debug/rust-examples`
{
  "time": "2024-04-07T14:45:09.715994247-07:00",
  "level": "INFO",
  "message": "Hello, world!",
  "module_path": "rust_examples",
  "file": "src/main.rs",
  "line": 5,
  "target": "rust_examples",
  "thread": "main",
  "thread_id": 140185055148352,
  "mdc": {}
}
```

There is a lot more I could show here, such as using a file (or rolling
file) appender, different possibilities with the encoders, having
multiple loggers e.g. maybe a rolling file appender for everything but a
console appender that filters to allow only error level messages; or
maybe different file appenders for different modules. This is also only
one of many available implementations that work with the
`log` facade crate.

Stay tuned for more blogs as I continue my Rust journey. Thanks for
reading!
