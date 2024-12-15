---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Text parsing in Rust with Nom {#text-parsing-in-rust-with-nom .p-name}

</div>

::: {.section .p-summary field="subtitle"}
As soon as you want to do anything non-trivial with respect to parsing
text using Rust (or any language) you should use some kind of parser...
:::

::: {.section .e-content field="body"}
::: {#9966 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Text parsing in Rust with Nom {#a1b4 .graf .graf--h3 .graf--leading .graf--title name="a1b4"}

<figure id="a5ce" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*N4WMJqO8GI_ZZzr6"
class="graf-image" data-image-id="0*N4WMJqO8GI_ZZzr6" data-width="3966"
data-height="5582" data-unsplash-photo-id="8GnB_yOShaU"
data-is-featured="true" alt="munch as in nom" />
<figcaption>Photo by <a
href="https://unsplash.com/@artchicago?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@artchicago?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Art Institute of
Chicago</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

As soon as you want to do anything non-trivial with respect to parsing
text using Rust (or any language) you should use some kind of parser
implementation. Writing a working parser for anything but the most
trivial content is non-trivial. Unless you want to learn parsers
(perhaps you're taking a compiler course), better to use an existing
tool/framework.

One approach is to use a parser generator, such as lex/flex or
yacc/bison. In this approach you write a grammar for what you want to
parse using the format those tools take, and they generate code that you
can then use to parse whatever it is you're parsing.

Another approach is to programmatically define your parser, and that's
where the [`nom`{.markup--code
.markup--p-code}](https://github.com/rust-bakery/nom){.markup--anchor
.markup--p-anchor data-href="https://github.com/rust-bakery/nom"
rel="noopener" target="_blank"} Rust crate comes in. In a sense you can
think of `nom`{.markup--code .markup--p-code} as a
[DSL](https://en.wikipedia.org/wiki/Domain-specific_language){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Domain-specific_language"
rel="noopener" target="_blank"} for writing parsers. The crate contains
a bunch of functions that do very simple, specific things and you
combine and compose them to parse your text. You construct your parser
"bottom up" looking at the lowest level constructs and combining them to
build more complex items. Perhaps you need to match an encoded secret in
a configuration file, and these encoded passwords are of the form
`some_secret: {bcrypt}A87ADB6ADF`{.markup--code .markup--p-code} in
which case you could use the `tag`{.markup--code .markup--p-code}
function in `nom`{.markup--code .markup--p-code}:

``` {#dfb9 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="rust"}
fn secret_parser(i: &str) -> IResult<&str, &str> {
  tag("{bcrypt}")(i)
}
```

which will strip off the `{bcrypt}`{.markup--code .markup--p-code}
prefix and return the rest of the input. Maybe your secret parser needs
to support two alternatives, `bcrypt`{.markup--code .markup--p-code} and
`custom`{.markup--code .markup--p-code} in which case you could modify
the above example to use the `alt`{.markup--code .markup--p-code}
function like so, to have two `alt`{.markup--code
.markup--p-code}ernatives to match.

``` {#291c .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="rust"}
fn secret_parser(i: &str) -> IResult<&str, &str> {
    alt((tag("{bcrypt}"), tag("{custom}")))
}
```

Generally speaking, the `nom`{.markup--code .markup--p-code} functions
all have the same basic signature:

``` {#4b0a .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="1" spellcheck="false" code-block-lang="rust"}
pub fn some_parser<T, Input, Error: ParseError<Input>>(
  tag: T,
) -> impl Fn(Input) -> IResult<Input, Input, Error>
```

They are essentially function generators, with the idea that you compose
them together to create more complex parsers ...

``` {#5087 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="2" spellcheck="false" code-block-lang="rust"}
fn my_parser(input: &str) -> IResult<&str, MyType> {
    foo(bar(baz1, baz2))(input)?
}
```

### A Realistic Example {#f801 .graf .graf--h3 .graf-after--pre name="f801"}

Rather than just showing some standalone snippets, let's create
something somewhat useful. Let's see how we could use
`nom`{.markup--code .markup--p-code} for parsing HTTP protocol messages,
or part of them anyway ... the request line and the headers. I'll leave
parsing the request body to you if you like.

> Of course there are crates out there to do this, so I wouldn't go down
> this route if I was trying to parse HTTP messages myself. Use
> something like the [`hyper`{.markup--code
> .markup--blockquote-code}](https://docs.rs/hyper/latest/hyper/index.html){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://docs.rs/hyper/latest/hyper/index.html"
> rel="noopener" target="_blank"} crate instead.

### HTTP Request Line {#1f66 .graf .graf--h3 .graf-after--blockquote name="1f66"}

Let's start with the HTTP protocol's request line. Starting with the
HTTP [RFC 2616](https://www.rfc-editor.org/rfc/rfc2616){.markup--anchor
.markup--p-anchor data-href="https://www.rfc-editor.org/rfc/rfc2616"
rel="noopener" target="_blank"} you can find what constitutes valid
messages including the
[ABNF](https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form"
rel="noopener" target="_blank"} grammar, which stands for Augmented
[Backus-Naur
Form](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form"
rel="noopener" target="_blank"}. If you've taken a compiler and/or
theoretical computer science course you probably came across BNF. RFC
2616 specifies the ABNF for the HTTP protocol, such as [basic
rules](https://www.rfc-editor.org/rfc/rfc2616#section-2.2){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-2.2"
rel="noopener" target="_blank"} for what are valid characters and
tokens, what is a [valid HTTP
version](https://www.rfc-editor.org/rfc/rfc2616#section-3.1){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-3.1"
rel="noopener" target="_blank"} and of course what is a valid protocol
[request
line](https://www.rfc-editor.org/rfc/rfc2616#section-5.1){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-5.1"
rel="noopener" target="_blank"}.

In ABNF, a request line is defined as:

``` {#ac5b .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="0" spellcheck="false"}
Request-Line = Method SP Request-URI SP HTTP-Version CRLF
```

Each of the items to the right of the `=`{.markup--code .markup--p-code}
is required and is defined somewhere in the RFC. The `SP`{.markup--code
.markup--p-code} and `CRLF`{.markup--code .markup--p-code} are defined
in the basic rules link I provided above, and are basically what you'd
guess. Then there's the `Method`{.markup--code .markup--p-code},
`Request-URI`{.markup--code .markup--p-code} and
`HTTP-Version`{.markup--code .markup--p-code} which are specified in
their own subsections. These may further break down into ABNF
expressions. If you look at [`Request-URI`{.markup--code
.markup--p-code}](https://www.rfc-editor.org/rfc/rfc2616#section-5.1.2){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-5.1.2"
rel="noopener" target="_blank"} you'll see it defined as

``` {#84e5 .graf .graf--pre .graf-after--p .graf--preV2 code-block-mode="0" spellcheck="false"}
Request-URI = "*" | absoluteURI | abs_path | authority
```

The pipe `|`{.markup--code .markup--p-code} symbol in ABNF signifies
logical "or" --- in other words the request URI has one of those parts.

Given this, what would the `nom`{.markup--code .markup--p-code}-based
parser look like? As with any code, there are several ways you could go
about writing this. The request line has three things we want to
extract, the HTTP method, the URI and the version. We don't care about
the separating white space or line terminator. And for the HTTP version,
we just want the version number itself. We know that it's HTTP after
all! I therefore organized my code into basically three parsers and I
return the parsed data as a tuple of
`(method, path, version)`{.markup--code .markup--p-code}. Also, since
there's more to parse after the request line, and given the way the
`nom`{.markup--code .markup--p-code} parser functions work, there's also
a "the rest of the input" return value that contains what has not been
parsed yet. So a function to parse the request line is:

<figure id="b03a" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Breaking this down, lines 2--5 define my `nom`{.markup--code
.markup--p-code}-based parser functions. I construct my domain-specific
parsers building on the low level `nom`{.markup--code .markup--p-code}
constructs. In this case, looking at the `method_parser`{.markup--code
.markup--p-code} function defined at line 2, I use four different
`nom`{.markup--code .markup--p-code} parsers:

-   [`terminated`{.markup--code .markup--li-code} --- this parser takes
    two parsers; the first one defines how to match the content I want
    to keep, and the second parser defines how to match what I want to
    discard.]{#6ca8}
-   [`take_while1`{.markup--code .markup--li-code} --- what I want to
    keep is defined by this parser. This parser takes a function
    defining what is valid to keep until some condition. In this case I
    want to keep alphabetic characters. This parser also shows a common
    pattern in the `nom`{.markup--code .markup--li-code} API which is
    the `1`{.markup--code .markup--li-code} at the end of the function.
    There are many functions that have a `1`{.markup--code
    .markup--li-code} or a `0`{.markup--code .markup--li-code} at the
    end, signifying there should be "one or more" or "zero or more" of
    the specific thing, similar to the `?`{.markup--code
    .markup--li-code} and `*`{.markup--code .markup--li-code} regular
    expression characters.]{#dba2}
-   [`is_alphabetic`{.markup--code .markup--li-code} --- this parser
    does exactly what it says: returns true while the input is an
    aphabetic character.]{#3603}
-   [`multispace1`{.markup--code .markup--li-code} --- this parser
    defines what the terminated parser should discard. In this case it
    should consume and discard one or more spaces. This takes care of
    the space after the method.]{#09a5}

Putting that all together I have a variable
`method_parser`{.markup--code .markup--p-code} that's a
`Fn`{.markup--code .markup--p-code} that takes a `&[u8]`{.markup--code
.markup--p-code} and returns an `IResult<&[u8], &[u8]>`{.markup--code
.markup--p-code} where the first value in the tuple is the "rest" of the
input that wasn't consumed, and the second value is the matched HTTP
method bytes. If there was an error, the result has an
`Err(ParseError)`{.markup--code .markup--p-code} from
`nom`{.markup--code .markup--p-code}.

> One thing I'm going to skip over in this post for brevity is the
> different APIs `nom`{.markup--code .markup--blockquote-code} has for
> "complete" or "streaming" inputs. For example, the
> `take_while1`{.markup--code .markup--blockquote-code} function is
> `nom::bytes::complete::take_while1`{.markup--code
> .markup--blockquote-code} but there is also a
> `nom::bytes::streaming::take_while1`{.markup--code
> .markup--blockquote-code} and the difference manifests in the errors
> generated if the input "runs out" while parsing. You can read the docs
> for details.

Assuming a valid request line then, the result of calling
`method_parser(b"GET /foo HTTP/1.1")`{.markup--code .markup--p-code} is
`(b"GET", b"/foo HTTP/1.1")`{.markup--code .markup--p-code}.

The next parser, that `path_parser`{.markup--code .markup--p-code}
simply looks for anything that isn't a space, to define what is valid,
and then uses the `multispace1`{.markup--code .markup--p-code} function
again to define the terminator. Finally the
`http_version_parser`{.markup--code .markup--p-code} looks for the
`tag`{.markup--code .markup--p-code} of `HTTP/`{.markup--code
.markup--p-code} and drops it, while keeping the content that is matched
by `version_parser`{.markup--code .markup--p-code}. This uses the
`nom`{.markup--code .markup--p-code} function `preceeded`{.markup--code
.markup--p-code} which as you can probably tell is the opposite of the
`terminated`{.markup--code .markup--p-code} function we've already seen.
The `terminated`{.markup--code .markup--p-code} parser keeps the content
of the first parser argument and drops the content of the second while
the `preceeded`{.markup--code .markup--p-code} parser drops the content
matched by the first parser and keeps the content matched by the second
parser. (There's also a `match_eol`{.markup--code .markup--p-code}
parser function which is something that I wrote; it's not from
`nom`{.markup--code .markup--p-code}. It just looks for
`tag("\r\n")`{.markup--code .markup--p-code} in the input. I broke it
out so I can re-use it elsewhere.)

Putting it all together I chain these parsers together using the
`tuple `{.markup--code .markup--p-code}parser from `nom`{.markup--code
.markup--p-code} and finally converting the matched method, path and
version to `&str`{.markup--code .markup--p-code} values from the
`&[u8]`{.markup--code .markup--p-code} slices.

### HTTP Headers {#7389 .graf .graf--h3 .graf-after--p name="7389"}

After consuming the HTTP request line, the "rest" of the input should be
the HTTP headers. There are two types, request and response headers
(really three types since there are ["entity"
headers](https://www.rfc-editor.org/rfc/rfc2616#section-7){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-7"
rel="noopener" target="_blank"}). As we're parsing the request, I'm only
going to cover the request headers, which are defined [here in the
RFC](https://www.rfc-editor.org/rfc/rfc2616#section-5.3){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-5.3"
rel="noopener" target="_blank"}.

All headers ABNF syntax are defined [here in the
RFC](https://www.rfc-editor.org/rfc/rfc2616#section-4.2){.markup--anchor
.markup--p-anchor
data-href="https://www.rfc-editor.org/rfc/rfc2616#section-4.2"
rel="noopener" target="_blank"}, but to summarize are name/value pairs
separated by a `:`{.markup--code .markup--p-code}. Here is the function
I wrote using `nom`{.markup--code .markup--p-code} to parse a single
header:

<figure id="23fd" class="graf graf--figure graf--iframe graf-after--p">

</figure>

You should be able to grok what's going on here given the earlier
example. What's new here is the `nom`{.markup--code .markup--p-code}
method `separated_pair`{.markup--code .markup--p-code} which takes three
parsers, the first and third defining the pair of things to keep, and
the middle one what to match to discard. In this case we're skipping
the `:`{.markup--code .markup--p-code} separator. The
`match_header`{.markup--code .markup--p-code} parser then will match one
header line. To match all the headers, just call this in a loop. The
HTTP headers section itself, when there are no more headers to read, is
indicated by double CRLF, that is `"\r\n\r\n"`{.markup--code
.markup--p-code}. Following that is the request body, but as I said at
the start I'm not going to get into that. Reading the body isn't really
about parsing, since it's opaque bytes, and all we know is what's
provided in the headers we just parsed.

### Conclusion {#93e1 .graf .graf--h3 .graf-after--p name="93e1"}

Hopefully this has given you a taste for what parsing with
`nom`{.markup--code .markup--p-code} is like. There is obviously a lot
more ... I didn't cover all the various parsers the crate provides. If
this intro whetted your appetite, go check out their docs. And as I also
mentioned at the start, there are multiple ways to write this example.
Please let me know if you've got a "better" or just different way. I'm a
beginner with `nom`{.markup--code .markup--p-code} just as I am with
Rust overall. I'm doing this to learn, and so if you have something to
share to help me learn, please share it!

And if you liked this content please clap or follow me for more. If you
really liked it, feel free to [buy me a
coffee](https://www.buymeacoffee.com/raysuliteanu){.markup--anchor
.markup--p-anchor data-href="https://www.buymeacoffee.com/raysuliteanu"
rel="noopener" target="_blank"}!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [July 11, 2024](https://medium.com/p/ca5f7355fb47).

[Canonical
link](https://medium.com/@raysuliteanu/text-parsing-in-rust-with-nom-ca5f7355fb47){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
