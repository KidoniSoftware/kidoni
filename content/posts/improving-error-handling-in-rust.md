---
title: Improving your error handling in Rust
description: tips for better error handling in Rust
date: 2024-04-13
tags:
  - blog
  - rust
  - programming
draft: false
---

This is another blog in my fledgling series on Rust as I learn the
language. In this blog I touch on a few cool crates that can improve
your error handling in Rust. It follows nicely from my prior post on
[logging in Rust](/posts/logging-in-a-rust-app/).
As with that post, this is just an introductory look at error handling. There is
a lot more one can learn about error handling (in Rust or otherwise) than I will
cover here. Here I will just touch on a few crates that can get you started.
Maybe in future posts I will get into more detail on other topics, but there are
also good blogs out there already (e.g.
[this](https://matklad.github.io/2020/10/15/study-of-std-io-error.html)).

{{< callout type="info" >}}
As a newbie, please feel free in the comments to elaborate on what I
might be doing wrong, could do better or is not "canonical" Rust.
{{< /callout >}}


So let's dive in.

## Overview

To be specific, in this blog I will cover defining and using error types
specific to your project (application/library). I will also mention a
cool crate to make your panic output look a bit better to facilitate
debugging, and in doing so touch on Rust's 'feature' mechanism and how
you can create and use your own features, in this case to enable/disable
the panic output pretification.

## std::result::Result<T, E>

Error handling starts with a `Result<T, E>`. I will assume you know the
difference between an `Option` and a `Result`, and in your code, for a given
situation you have decided to use a `Result` rather than an `Option`. So now you
have to decide what that 'E' should be. I will further assume for the sake of
this discussion that you want an error (or errors) that is domain-specific i.e.
you're not just returning someone else's error (like Rust's `std::io::Error`).

While there are a few different approaches, what I will cover here is
the [`thiserror`](https://crates.io/crates/thiserror) crate. This crate provides
macros that you use in your code with a custom error enum (or enums). It
generates custom errors as if you created your own custom implementations of
`std::error::Error`. This keeps the crate itself out of your public API ---
you're not 'locked in' to using the crate.

Let's see what this looks like. Let's say I had a custom configuration
file processing implementation and so had some associated error
conditions I wanted. So I create a `ConfigError` enumeration:

```rust
use std::io;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("could not load configuration")]
    ConfigLoadError(#[from] io::Error),

    #[error("invalid config file format: {0}")]
    ConfigParseError(String),

    #[error("unknown config property '{key}:{value}'")]
    UnknownConfigProperty {
        key: String,
        value: String,
    },
}
```

There are some key things to point out. Obviously you have the annotations from
`thiserror`. Firstly you define `derive(thiserror::Error)` on the enum. Then for
each enumeration value you use the `#[error]` annotation. A key feature of this
is the message to associate with the error, but even more important is the
ability to reference the values of the enum in the error message. You could use
positional parameters like with the `ConfigParseError` or reference by name
values as in the `UnknownConfigProperty`. And looking at the first enum value
`ConfigLoadError` you can see that you can reference another `Error` from which
to get the error info.

Let's take a look at that last use case in more detail. What does the usage and
output look like if we have a `ConfigLoadError`? Let's expand on the earlier
code and add a function to load configuration from a file into a custom
configuration struct (using toml for the example, hence the `Deserialize`
annotation on the struct.

```rust
use std::io;
use serde::Deserialize;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("could not load configuration")]
    ConfigLoadError(#[from] io::Error),

    #[error("invalid config file format: {0}")]
    ConfigParseError(String),

    #[error("unknown config property '{key}:{value}'")]
    UnknownConfigProperty {
        key: String,
        value: String,
    },
}

#[derive(Deserialize)]
pub struct MyConfig {
    value: String,
}

pub fn load_config(file_name: &str) -> Result<MyConfig, ConfigError> {
    let config_str = std::fs::read_to_string(file_name)?;
    let config: MyConfig = toml::from_str(&config_str)
        .map_err(|e| ConfigError::ConfigParseError(e.to_string()))?;
    Ok(config)
}
```

In this code, note the return type which uses the `ConfigError` we defined
earlier, but also see line 26 which attempts to read the configuration from the
indicated file. `std::fs::read_to_string()` returns a `std::io::error::Error`
and obviously not our custom `ConfigError` yet we didn't do any explicit
conversion (as in the next lines). Yet the "right thing" happens if we run this
without a config file:

```text
2024-04-13T12:54:09.857429824-07:00 [rust_examples] INFO rust_examples:loading config
Error: could not load configuration

Caused by:
    No such file or directory (os error 2)

Location:
    src/main.rs:17:13
```

As you can see we get both our custom error `could not load configuration` as
well as a "caused by" with the underlying I/O error from `fs::read_to_string()`.
This is because `thiserror` generates a `From` implementation.

{{< callout type="note" >}}
As a bonus aside, there's a cool cargo tool **cargo-expand** that you
can install which will dump out the Rust code of a file after all the
macros have done their thing. It's like running the C/C++ macro
processor, if you're familiar with that.
{{< /callout >}}


```text
$ cargo install cargo-expand
$ cargo expand --bin rust-examples --color=always --theme=GitHub --tests config
...
    #[allow(unused_qualifications)]
    impl ::core::convert::From<io::Error> for ConfigError
        }
    }
```

## Pretty Backtraces (and Features)

So there you have a quick and dirty intro to using
`thiserror`. I encourage you to delve
deeper, and to explore alternative crates such as
[`anyhow`](https://crates.io/crates/anyhow). But as a quick (and brief) finale,
there's a cool create called color-eyre which is simple to use and makes
backtraces pretty (color, etc.). Check out the before and after:

![not pretty](/images/not-pretty.webp)

![pretty](/images/pretty.webp)

To enable this, add the `color-eyre`
crate and initialize it like so (line 14):

```rust
use std::io;

use color_eyre::eyre::Result;
use log::info;
use serde::Deserialize;

use crate::config::ConfigError;

mod config;

fn main() -> Result<()> {
    log4rs::init_file("log_config.yaml", Default::default()).unwrap();
    #[cfg(feature = "pretty-backtrace")]
    color_eyre::install()?;

    info!("loading config");
    let _ = config::load_config("config.yaml")?;

    panic!("oh crap!");
}
```

But I'm sure you also noticed line 13! That's how you can dynamically
include or exclude functionality in your code. You also need to declare
the features you have in your `Cargo.toml` file

```toml
[features]
pretty-backtrace = []
```

## Next steps

There is obviously a lot more we could discuss around error handling and how to
improve it in your code, things like when to use `panic!`, use of `unwrap()`
and `expect()` or not, (over)use of `?` to short-circuit returning errors, etc.
But this is a good start. I hope you found this useful.
