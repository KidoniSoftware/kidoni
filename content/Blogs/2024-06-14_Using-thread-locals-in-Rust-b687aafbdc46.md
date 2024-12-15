---
title: 
description: 
date: 
tags:
  - blog
draft: true
---

<div>

# Using thread locals in Rust {#using-thread-locals-in-rust .p-name}

</div>

::: {.section .p-summary field="subtitle"}
As I continue my journey learning Rust, I thought I'd share some
learning related to multithreading and thread locals.
:::

::: {.section .e-content field="body"}
::: {#4f76 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Using thread locals in Rust {#44b3 .graf .graf--h3 .graf--leading .graf--title name="44b3"}

<figure id="ace9" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*dtrWxlnQv4MuMq0y"
class="graf-image" data-image-id="0*dtrWxlnQv4MuMq0y" data-width="5360"
data-height="3572" data-unsplash-photo-id="hTeYcjviZ-s"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@amir_v_ali?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@amir_v_ali?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">amirali mirhashemian</a>
on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

As I continue my journey learning Rust, I thought I'd share some
learning related to multithreading and thread locals.

I came across an interesting new site called
[CodeCrafters](https://codecrafters.io){.markup--anchor
.markup--p-anchor data-href="https://codecrafters.io" rel="noopener"
target="_blank"}. The site is another learning site supporting multiple
programming languages, but they focus on specific "challenges" with
specific tasks to accomplish for each challenge. I've worked through a
few of them, and I used threads and thread locals on the HTTP server
challenge.

> I am not affiliated with CodeCrafters in any way. I just found it
> interesting and since I developed the code I use in this example from
> working on one of their challenges, I thought I'd give some
> acknowledgement. I don't get any kind of "kickback" for mentioning
> them.

As the task was to build a basic HTTP server, I decided to use the
`tokio`{.markup--code .markup--p-code} crate. One use case of the
CodeCrafter's HTTP server challenge was supporting downloading of files.
The HTTP server would be provided a command line option specifying a
base directory from which files would be downloaded. Then the HTTP
server would expose an endpoint a client could invoke to download some
file. So given

``` {#45ec .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ my_server --directory /tmp
```

and a client invocation like

``` {#056d .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="shell"}
$ curl localhost:8080/files/foo.txt
```

the server should return a file `/tmp/foo.txt`{.markup--code
.markup--p-code} if it exists.

The main processing loop using `tokio`{.markup--code .markup--p-code}
looks something like this:

<figure id="3f2f" class="graf graf--figure graf--iframe graf-after--p">

</figure>

In my approach, the `process_request()`{.markup--code .markup--p-code}
function will handle all the HTTP protocol details like parsing the
initial protocol line to extract what the client is asking for, and any
headers. So assuming the client executes the `curl`{.markup--code
.markup--p-code} command shown above, the HTTP server should get

`GET /files/foo.txt HTTP/1.1`{.markup--code .markup--p-code}

That means of course it needs to look for `foo.txt`{.markup--code
.markup--p-code} in some place that was provided to the server at
startup via `--directory`{.markup--code .markup--p-code}. I decided to
use the `clap`{.markup--code .markup--p-code} crate for this, with the
`derive `{.markup--code .markup--p-code}feature.

<figure id="e87a" class="graf graf--figure graf--iframe graf-after--p">

</figure>

(I also added a `--port`{.markup--code .markup--p-code} option but I'm
not doing to discuss that here.)

By using `#[derive(Parser)]`{.markup--code .markup--p-code} on your
struct containing the command line options, you can now simply call
`Cli::parse()`{.markup--code .markup--p-code} to return an instance of
your struct populated as defined. This post isn't about
`clap`{.markup--code .markup--p-code} so I'll let you [look that useful
crate up on your
own.](https://docs.rs/clap/latest/clap/){.markup--anchor
.markup--p-anchor data-href="https://docs.rs/clap/latest/clap/"
rel="noopener" target="_blank"}

So now comes the point where you have to decided how to provide the
given directory to the threads executing
`process_request()`{.markup--code .markup--p-code}. I could have just
passed in the directory as a parameter like
`process_request(dir)`{.markup--code .markup--p-code} but that's no
fun :) and also looking ahead there could be other things I'll need to
provide, as well as the fact that the directory is only required for the
one use case of downloading files. So I decided to try and figure out
how to use thread locals.

The `tokio`{.markup--code .markup--p-code} crate has support for a
`task_local!`{.markup--code .markup--p-code} macro. It's called "task
local" because technically what you spawn using
`tokio::spawn`{.markup--code .markup--p-code} does not necessarily get
run on a new thread. If you want to use threads you actually have to
tell the Tokio runtime about it, which you can do with the
`flavor = "multi_thread"`{.markup--code .markup--p-code} argument to the
`tokio::main`{.markup--code .markup--p-code} macro ...

``` {#9b50 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="rust"}
#[tokio::main(flavor = "multi_thread")]
async fn main() -> io::Result<()> { 
```

> NOTE: you need to have the `macros`{.markup--code
> .markup--blockquote-code}, `rt`{.markup--code
> .markup--blockquote-code} and `rt-multi-thread`{.markup--code
> .markup--blockquote-code} features enabled, at a minimum, for
> `tokio::main`{.markup--code .markup--blockquote-code},
> `task_local!`{.markup--code .markup--blockquote-code} and
> `flavor = "multi_thread"`{.markup--code .markup--blockquote-code} to
> work. Some other features are required as well to get the net and io
> stuff.\
> `tokio = { version = “1.38.0”, features = [“macros”, “rt-multi-thread”, “rt”, “net”, “io-util”, “fs”] }`{.markup--code
> .markup--blockquote-code}

To contain the current and future "context" I wanted to provide to
spawned threads, I created a struct and then set it as my "task" local
context.

<figure id="7845" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Then all I needed to do was "wrap" my invocation of the
`process_request()`{.markup--code .markup--p-code} method thusly

<figure id="7577" class="graf graf--figure graf--iframe graf-after--p">

</figure>

To then get access to the context during execution of the task, you call
the `get()`{.markup--code .markup--p-code} method:

<figure id="21b1" class="graf graf--figure graf--iframe graf-after--p">

</figure>

That's "all" there is to it. There are caveats, like trait bounds e.g.
Clone. And I'm sure there are other subtleties that I haven't yet
encountered since my usage so far is pretty basic. But it does work! And
depending on your situation you don't need to use `tokio`{.markup--code
.markup--p-code}. There are other implementations of thread locals
including [`std::thread_local!`{.markup--code
.markup--p-code}](https://doc.rust-lang.org/std/macro.thread_local.html#){.markup--anchor
.markup--p-anchor
data-href="https://doc.rust-lang.org/std/macro.thread_local.html#"
rel="noopener" target="_blank"}.

As always, since I'm still learning, if you spot anything egregious or
have any suggestions or recommendations, please comment. Regardless, if
you liked this please clap and/or [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="https://www.buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"}!. Thanks and stay tuned for more!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [June 14, 2024](https://medium.com/p/b687aafbdc46).

[Canonical
link](https://medium.com/@raysuliteanu/using-thread-locals-in-rust-b687aafbdc46){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
