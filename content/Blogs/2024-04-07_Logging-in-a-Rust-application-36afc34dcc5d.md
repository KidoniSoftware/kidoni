---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Logging in a Rust application {#logging-in-a-rust-application .p-name}

</div>

::: {.section .p-summary field="subtitle"}
This blog post is part of a series I'm developing documenting my
evolution as a Rust developer. Let's start with how to use logging.
:::

::: {.section .e-content field="body"}
::: {#85dc .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Logging in a Rust application {#ac10 .graf .graf--h3 .graf--leading .graf--title name="ac10"}

<figure id="1d2d" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*UUvEj3fbmjAijx-u"
class="graf-image" data-image-id="0*UUvEj3fbmjAijx-u" data-width="4016"
data-height="6016" data-unsplash-photo-id="39gUADZGi9E"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@charlottelharrison?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@charlottelharrison?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Charlotte Harrison</a>
on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

This blog post is part of a series I'm developing documenting my
evolution as a Rust developer. Currently I'm a newbie, but I'm making
progress.

> As a newbie, please feel free in the comments to elaborate on what I
> might be doing wrong, could do better or is not "canonical" Rust.

Logging is obviously a key aspect of a production-ready application.
While one could use `println!`{.markup--code .markup--p-code} or
`dbg!`{.markup--code .markup--p-code} or similar Rust macros to achieve
something similar, they are not really a replacement for a real logging
framework. In fact, particularly for (long running) "services" as
opposed to CLIs, many architecture/coding standards prohibit use of the
equivalent to `println!`{.markup--code .markup--p-code} in whatever
language you're using. I myself have set such standards on projects I've
lead.

So as I've been teaching myself Rust, I was naturally interested in what
the Rust ecosystem has in terms of logging capabilities.

The first thing to mention is
[log](https://crates.io/crates/log){.markup--anchor .markup--p-anchor
data-href="https://crates.io/crates/log" rel="noopener" target="_blank"}
crate. This library provides a standard logging facade API that is then
combined with an actual logging implementation provided by a separate
crate that you as the developer can select per your requirements. This
is similar to `commons-logging`{.markup--code .markup--p-code} or
`SLF4J`{.markup--code .markup--p-code} in the Java world. To use
`log`{.markup--code .markup--p-code} in Rust,

``` {#8180 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ cargo add log
```

or add it manually, but in either case your `Cargo.toml`{.markup--code
.markup--p-code} will end up with

``` {#eb26 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="ini"}
[dependencies]
log = "0.4.21"
```

To add logging to your application, you then use one of the macros to
log at

-   [`trace!`{.markup--code .markup--li-code}]{#2e76}
-   [`debug!`{.markup--code .markup--li-code}]{#64a9}
-   [`info!`{.markup--code .markup--li-code}]{#cc5c}
-   [`warn!`{.markup--code .markup--li-code}]{#6aee}
-   [`error!`{.markup--code .markup--li-code}]{#c91b}

There is also a generic `log!`{.markup--code .markup--p-code} macro
which takes the log level as a parameter. To use these macros just
include them in your code, e.g.

<figure id="cf0b" class="graf graf--figure graf--iframe graf-after--p">

<figcaption>logging with info! macro</figcaption>
</figure>

If you run this now, this is what you'd see:

``` {#48c3 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ cargo run
    Finished dev [unoptimized + debuginfo] target(s) in 0.00s
     Running `target/debug/rust-examples`
```

Hey, where's my log message? Well, as I mentioned, the
`log`{.markup--code .markup--p-code} crate just provide the API. To
actually do something you need a log implementation. (Returning to the
Java example, this is the same as needing to include, e.g.
[Logback](https://logback.qos.ch/){.markup--anchor .markup--p-anchor
data-href="https://logback.qos.ch/" rel="noopener" target="_blank"} as
an implementation when using `SLF4J`{.markup--code .markup--p-code} as
the API.)

Looking at the `log`{.markup--code .markup--p-code} create documentation
you'll see a lot of different possible logging implementations that you
can select from. Choose one based on your requirements. For this blog I
am going to pick a sophisticated implementation that's inspired by
[Logback](https://logback.qos.ch/){.markup--anchor .markup--p-anchor
data-href="https://logback.qos.ch/" rel="noopener" target="_blank"} and
provides a lot of configuration options. It is called
[log4rs](https://docs.rs/log4rs/latest/log4rs/){.markup--anchor
.markup--p-anchor data-href="https://docs.rs/log4rs/latest/log4rs/"
rel="noopener" target="_blank"}.

``` {#c6af .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ cargo add log4rs
    Updating crates.io index
      Adding log4rs v1.3.0 to dependencies.
             Features:
             ...
```

*(I am truncating the output, which lists all the features that are
available.)*

``` {#eae2 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="ini"}
[dependencies]
log = "0.4.21"
log4rs = "1.3.0"
```

This is not all that is required though. If you were to run the
application now, you'd still not see any output. This is because
`log4rs`{.markup--code .markup--p-code} requires configuration. This can
be done either via a YAML configuration file, or programmatically. You
can read the `log4rs`{.markup--code .markup--p-code} documentation for
the details, but to briefly summarize, `log4rs`{.markup--code
.markup--p-code} (like `Logback`{.markup--code .markup--p-code}) has the
notion of loggers, appenders and encoders. An appender is something that
writes (appends) to a log. Encoders define how the log messages are
formatted when written. Examples of appenders include a
`console`{.markup--code .markup--p-code} appender (to
`stdout`{.markup--code .markup--p-code}) and a `file`{.markup--code
.markup--p-code} appender. Encoders could be a regex
`pattern`{.markup--code .markup--p-code} encoder or a
`json`{.markup--code .markup--p-code} encoder. Here is a very basic
`log4rs`{.markup--code .markup--p-code} configuration file.

<figure id="fae7" class="graf graf--figure graf--iframe graf-after--p">

</figure>

You then need to load this configuration and initialize
`log4rs`{.markup--code .markup--p-code}, like so:

<figure id="5cd5" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Finally you will now see a log message, formatted according to the
pattern specified in the configuration file.

``` {#754a .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ cargo run
    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running `target/debug/rust-examples`
2024-04-07T14:37:36.838882622-07:00 [rust_examples] INFO rust_examples:Hello, world!

```

If you change the configuration file to use the JSON encoder like so

``` {#7e0a .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="yaml"}
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
`jq`{.markup--code .markup--p-code} to make it more readable):

``` {#1cb9 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
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
`log`{.markup--code .markup--p-code} facade crate.

Stay tuned for more blogs as I continue my Rust journey. Thanks for
reading! Clap if you enjoyed this, follow if you want more and feel free
to [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="https://www.buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"}. :)
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [April 7, 2024](https://medium.com/p/36afc34dcc5d).

[Canonical
link](https://medium.com/@raysuliteanu/logging-in-a-rust-application-36afc34dcc5d){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
