---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Improving your error handling in Rust {#improving-your-error-handling-in-rust .p-name}

</div>

::: {.section .p-summary field="subtitle"}
This is another blog in my fledgling series on Rust as I learn the
language. In this blog I touch on a few cool crates that can improve...
:::

::: {.section .e-content field="body"}
::: {#d741 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Improving your error handling in Rust {#8fdf .graf .graf--h3 .graf--leading .graf--title name="8fdf"}

<figure id="0ff4" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*A_uYBG3sBfuCCceE"
class="graf-image" data-image-id="0*A_uYBG3sBfuCCceE" data-width="6000"
data-height="4000" data-unsplash-photo-id="heNwUmEtZzo"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@davfts?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@davfts?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">David Pupăză</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

This is another blog in my fledgling series on Rust as I learn the
language. In this blog I touch on a few cool crates that can improve
your error handling in Rust. It follows nicely from my prior post on
[logging in
Rust](https://medium.com/@raysuliteanu/logging-in-a-rust-application-36afc34dcc5d){.markup--anchor
.markup--p-anchor
data-href="https://medium.com/@raysuliteanu/logging-in-a-rust-application-36afc34dcc5d"
target="_blank"}. As with that post, this is just an introductory look
at error handling. There is a lot more one can learn about error
handling (in Rust or otherwise) than I will cover here. Here I will just
touch on a few crates that can get you started. Maybe in future posts I
will get into more detail on other topics, but there are also good blogs
out there already (e.g.
[this](https://matklad.github.io/2020/10/15/study-of-std-io-error.html){.markup--anchor
.markup--p-anchor
data-href="https://matklad.github.io/2020/10/15/study-of-std-io-error.html"
rel="noopener" target="_blank"}).

> As a newbie, please feel free in the comments to elaborate on what I
> might be doing wrong, could do better or is not "canonical" Rust.

So let's dive in.

To be specific, in this blog I will cover defining and using error types
specific to your project (application/library). I will also mention a
cool crate to make your panic output look a bit better to facilitate
debugging, and in doing so touch on Rust's 'feature' mechanism and how
you can create and use your own features, in this case to enable/disable
the panic output pretification.

### std::result::Result\<T, E\> {#58fe .graf .graf--h3 .graf-after--p name="58fe"}

Error handling starts with a `Result<T, E>`{.markup--code
.markup--p-code}. I will assume you know the difference between an
`Option`{.markup--code .markup--p-code} and a `Result`{.markup--code
.markup--p-code}, and in your code, for a given situation you have
decided to use a `Result`{.markup--code .markup--p-code} rather than an
`Option`{.markup--code .markup--p-code}. So now you have to decide what
that 'E' should be. I will further assume for the sake of this
discussion that you want an error (or errors) that is domain-specific
i.e. you're not just returning someone else's error (like Rust's
`std::io::Error`{.markup--code .markup--p-code}).

While there are a few different approaches, what I will cover here is
the [`thiserror`{.markup--code
.markup--p-code}](https://crates.io/crates/thiserror){.markup--anchor
.markup--p-anchor data-href="https://crates.io/crates/thiserror"
rel="noopener" target="_blank"}
[crate](https://crates.io/crates/thiserror){.markup--anchor
.markup--p-anchor data-href="https://crates.io/crates/thiserror"
rel="noopener" target="_blank"}. This crate provides macros that you use
in your code with a custom error enum (or enums). It generates custom
errors as if you created your own custom implementations of
std::error::Error. This keeps the crate itself out of your public
API --- you're not 'locked in' to using the crate.

Let's see what this looks like. Let's say I had a custom configuration
file processing implementation and so had some associated error
conditions I wanted. So I create a `ConfigError`{.markup--code
.markup--p-code} enumeration:

<figure id="45bc" class="graf graf--figure graf--iframe graf-after--p">

</figure>

There are some key things to point out. Obviously you have the
annotations from `thiserror`{.markup--code .markup--p-code}. Firstly you
define `derive(thiserror::Error)`{.markup--code .markup--p-code} on the
enum. Then for each enumeration value you use the
`#[error]`{.markup--code .markup--p-code} annotation. A key feature of
this is the message to associate with the error, but even more important
is the ability to reference the values of the enum in the error message.
You could use positional parameters like with the
`ConfigParseError`{.markup--code .markup--p-code} or reference by name
values as in the `UnknownConfigProperty`{.markup--code .markup--p-code}.
And looking at the first enum value `ConfigLoadError`{.markup--code
.markup--p-code} you can see that you can reference another
`Error`{.markup--code .markup--p-code} from which to get the error info.

Let's take a look at that last use case in more detail. What does the
usage and output look like if we have a `ConfigLoadError`{.markup--code
.markup--p-code}? Let's expand on the earlier code and add a function to
load configuration from a file into a custom configuration struct (using
toml for the example, hence the `Deserialize`{.markup--code
.markup--p-code} annotation on the struct.

<figure id="7049" class="graf graf--figure graf--iframe graf-after--p">

</figure>

In this code, note the return type which uses the
`ConfigError`{.markup--code .markup--p-code} we defined earlier, but
also see line 26 which attempts to read the configuration from the
indicated file. `std::fs::read_to_string()`{.markup--code
.markup--p-code} returns a `std::io::error::Error`{.markup--code
.markup--p-code} and obviously not our custom
`ConfigError`{.markup--code .markup--p-code} yet we didn't do any
explicit conversion (as in the next lines). Yet the "right thing"
happens if we run this without a config file:

``` {#56c8 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
2024-04-13T12:54:09.857429824-07:00 [rust_examples] INFO rust_examples:loading config
Error: could not load configuration

Caused by:
    No such file or directory (os error 2)

Location:
    src/main.rs:17:13
```

As you can see we get both our custom error
`could not load configuration`{.markup--code .markup--p-code} as well as
a "caused by" with the underlying I/O error from
`fs::read_to_string()`{.markup--code .markup--p-code}. This is because
`thiserror`{.markup--code .markup--p-code} generates a
`From`{.markup--code .markup--p-code} implementation.

> As a bonus aside, there's a cool cargo tool **cargo-expand** that you
> can install which will dump out the Rust code of a file after all the
> macros have done their thing. It's like running the C/C++ macro
> processor, if you're familiar with that.

``` {#bf5e .graf .graf--pre .graf-after--blockquote .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="bash"}
$ cargo install cargo-expand
$ cargo expand --bin rust-examples --color=always --theme=GitHub --tests config
...
    #[allow(unused_qualifications)]
    impl ::core::convert::From<io::Error> for ConfigError {
        #[allow(deprecated)]
        fn from(source: io::Error) -> Self {
            ConfigError::ConfigLoadError {
                0: source,
            }
        }
    }
```

### Pretty Backtraces (and Features) {#63ae .graf .graf--h3 .graf-after--pre name="63ae"}

So there you have a quick and dirty intro to using
`thiserror`{.markup--code .markup--p-code}. I encourage you to delve
deeper, and to explore alternative crates such as
[`anyhow`{.markup--code
.markup--p-code}](https://crates.io/crates/anyhow){.markup--anchor
.markup--p-anchor data-href="https://crates.io/crates/anyhow"
rel="noopener" target="_blank"}. But as a quick (and brief) finale,
there's a cool create called color-eyre which is simple to use and makes
backtraces pretty (color, etc.). Check out the before and after:

<figure id="3699" class="graf graf--figure graf-after--p">
<img
src="https://cdn-images-1.medium.com/max/800/1*RKD5q4kP5xggtymAiM9K2g.png"
class="graf-image" data-image-id="1*RKD5q4kP5xggtymAiM9K2g.png"
data-width="1679" data-height="702" />
<figcaption>not as pretty</figcaption>
</figure>

<figure id="ade7" class="graf graf--figure graf-after--figure">
<img
src="https://cdn-images-1.medium.com/max/800/1*NxpZpbtyaD8zDiMuCC8OjQ.png"
class="graf-image" data-image-id="1*NxpZpbtyaD8zDiMuCC8OjQ.png"
data-width="1679" data-height="675" />
<figcaption>prettier</figcaption>
</figure>

To enable this, add the `color-eyre`{.markup--code .markup--p-code}
crate and initialize it like so (line 14):

<figure id="218d" class="graf graf--figure graf--iframe graf-after--p">

</figure>

But I'm sure you also noticed line 13! That's how you can dynamically
include or exclude functionality in your code. You also need to declare
the features you have in your `Cargo.toml`{.markup--code
.markup--p-code} file

``` {#81f6 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="ini"}
[features]
pretty-backtrace = []
```

I hope you enjoyed this quick tour of error handling. Please clap and/or
follow and/or [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="https://www.buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"}!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [April 13, 2024](https://medium.com/p/5d348a6d9286).

[Canonical
link](https://medium.com/@raysuliteanu/improving-your-error-handling-in-rust-5d348a6d9286){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
