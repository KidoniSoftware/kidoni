---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Using Protocol Buffers to serialize to off-heap memory {#using-protocol-buffers-to-serialize-to-off-heap-memory .p-name}

</div>

::: {.section .p-summary field="subtitle"}
In my previous post about using off-heap memory in Java I showed how to
set up a memory-mapped file. Now that we have a memory-mapped file...
:::

::: {.section .e-content field="body"}
::: {#1e38 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Using Protocol Buffers to serialize to off-heap memory {#ccfb .graf .graf--h3 .graf--leading .graf--title name="ccfb"}

<figure id="df0b" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*ukj7Qp9xAf1mgOu9"
class="graf-image" data-image-id="0*ukj7Qp9xAf1mgOu9" data-width="6000"
data-height="4000" data-unsplash-photo-id="40XgDxBfYXM"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@jordanharrison?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@jordanharrison?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Jordan Harrison</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

In my previous post about [using off-heap memory in
Java](https://medium.com/everyday-programmer/using-off-heap-memory-in-java-programs-de4fb3e7683f){.markup--anchor
.markup--p-anchor
data-href="https://medium.com/everyday-programmer/using-off-heap-memory-in-java-programs-de4fb3e7683f"
target="_blank"} I showed how to set up a memory-mapped file. Now that
we have a memory-mapped file, let's write something to the file. There
are different approaches to how to serialize Java objects obviously
including the built-in Java serialization. But in this post I'm going to
use [Protocol
Buffers](https://developers.google.com/protocol-buffers){.markup--anchor
.markup--p-anchor
data-href="https://developers.google.com/protocol-buffers"
rel="noopener" target="_blank"} (AKA protobuf) for serialization,
because why not? It will also give an opportunity to show how to
automate the use of protobuf in your automated build using
[Gradle](https://gradle.org/){.markup--anchor .markup--p-anchor
data-href="https://gradle.org/" rel="noopener" target="_blank"}.

Protocol Buffers are a recent incarnation of a technique that's been
around for a long time --- a mechanism for describing data in a
language- and platform-neutral form which can be used to generate code
for (de)serialization. Take XDR for example.

::: {#1622 .graf .graf--mixtapeEmbed .graf-after--p}
[**What Is XDR? - ONC+ Developer\'s Guide**\
*This book describes the ONC+ distributed services that were developed
at Sun Microsystems. ONC+ technologies consist
of...*docs.oracle.com](https://docs.oracle.com/cd/E18752_01/html/816-1435/xdrnts-1.html "https://docs.oracle.com/cd/E18752_01/html/816-1435/xdrnts-1.html"){.markup--anchor
.markup--mixtapeEmbed-anchor
data-href="https://docs.oracle.com/cd/E18752_01/html/816-1435/xdrnts-1.html"}[](https://docs.oracle.com/cd/E18752_01/html/816-1435/xdrnts-1.html){.js-mixtapeImage
.mixtapeImage .mixtapeImage--empty .u-ignoreBlock
media-id="bfd2f2861d0fea54fcbd111ecf4b515f"}
:::

This is very similar to protobuf and was used in the RPC implementation
originating with Sun in SunOS/Solaris (ah the good old days). Just as
you can use protobuf for (de)serialization even if you aren't using
Google's gRPC, you could use XDR for (de)serialization without Sun RPC.

There was also the CORBA (Common Object Request Broker Architecture) and
its IDL ([Interface Description
Language](https://en.wikipedia.org/wiki/Interface_description_language){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Interface_description_language"
rel="noopener" target="_blank"}). There are a lot of "IDLs" as the
preceding link shows. And as for CORBA, there was actually support in
Java for CORBA as CORBA's heyday coincided with Java's rise.

The main point is that what protofbuf is doing is nothing new. What goes
around comes around.

With protobuf you create a `.proto`{.markup--code .markup--p-code} file
where you define "message" formats. For this example we'll define a
`Person`{.markup--code .markup--p-code} with some attributes including
an `Address`{.markup--code .markup--p-code}.

<figure id="693f" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Some things to note in this definition are

-   [`syntax`{.markup--code .markup--li-code} specifies the protobuf
    version]{#9744}
-   [there is both a `package`{.markup--code .markup--li-code}
    definition as well as an `option java_package`{.markup--code
    .markup--li-code} definition; protobuf is language-agnostic and the
    `package`{.markup--code .markup--li-code} definition is for its own
    namespacing, while the Java package specification is for the mapping
    to Java. I set them the same but that isn't required.]{#f066}
-   [the `option java_outer_classname`{.markup--code .markup--li-code}
    specifies what the code generator should use as the class containing
    the code it will generate for the subsequent `message`{.markup--code
    .markup--li-code} definitions.]{#bf86}
-   [each type you want to define is a `message`{.markup--code
    .markup--li-code} with various fields, and each field must have a
    unique integer ordinal; the types of fields are language neutral and
    map to specific language types per a defined spec]{#a322}
-   [you can have repeated elements, as shown with the
    `repeated Address`{.markup--code .markup--li-code} field]{#9385}
-   [you can have nested definitions like with the
    `Address`{.markup--code .markup--li-code} message definition within
    the `Person`{.markup--code .markup--li-code} message; alternatively
    I could have specified `Address`{.markup--code .markup--li-code} in
    its own `.proto`{.markup--code .markup--li-code} file and used an
    `import`{.markup--code .markup--li-code} statement e.g. if I was
    going to use `Address`{.markup--code .markup--li-code} in multiple
    message definitions.]{#421d}

Given a `.proto`{.markup--code .markup--p-code} file as above a compiler
is used to generate source code which is then used in your own code. The
protobuf compiler is called `protoc`{.markup--code .markup--p-code} and
you invoke it like any compiler, providing the `.proto`{.markup--code
.markup--p-code} source file(s). But obviously you want to have this
automated in your build. With Gradle, there is a [protobuf
plugin](https://github.com/google/protobuf-gradle-plugin){.markup--anchor
.markup--p-anchor
data-href="https://github.com/google/protobuf-gradle-plugin"
rel="noopener" target="_blank"}. It is pretty straightforward to use in
your Gradle build. A very nice convenient feature of the plugin is that
it can (optionally) download the `protoc`{.markup--code .markup--p-code}
compiler for you automatically, so you don't have to ensure it's
installed wherever your build is executing.

First, add the plugin:

<figure id="d577" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Then add the protobuf library dependency:

<figure id="c897" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Finally, configure the plugin to download `protoc`{.markup--code
.markup--p-code} if you want that:

<figure id="9b04" class="graf graf--figure graf--iframe graf-after--p">

</figure>

By default the plugin expects your `.proto`{.markup--code
.markup--p-code} files to be in `src/main/proto`{.markup--code
.markup--p-code} but you can configure that as well as several other
things (e.g. the location for the generated sources). See the plugin
documentation in the link provided.

Now how do you use the generated code? Protobuf uses a "builder" pattern
for constructing instances.

<figure id="ba47" class="graf graf--figure graf--iframe graf-after--p">

</figure>

There are a few different methods that can then be used to serialize the
`Person`{.markup--code .markup--p-code} instance e.g.

``` {#0823 .graf .graf--pre .graf-after--p}
public byte[] toByteArray();
public void writeTo(final OutputStream output);
```

and a few others. As I integrated this with my `LogDbFile`{.markup--code
.markup--p-code} example, I used the
`writeTo(OutputStream)`{.markup--code .markup--p-code} method, after
enhancing my `LogDbFile`{.markup--code .markup--p-code} class to expose
an `OutputStream`{.markup--code .markup--p-code} (and an
`InputStream`{.markup--code .markup--p-code}).

<figure id="8c40" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Since the idea with this `LogDb`{.markup--code .markup--p-code} is to
simulate an append-only file, you can either write (to the end) or read,
so in this example I create a new file --- implicitly for writing as I
have it right now --- and I serialize to the
`OutputStream`{.markup--code .markup--p-code}. Then I open the same file
for reading, allocating a buffer to store the data read from the file,
then deserialize using the generated
`Person.parseFrom(byte[])`{.markup--code .markup--p-code} method.

As you can see, it's pretty straightforward to use protobuf as a
serialization mechanism. One benefit of this over, say, Java native
serialization is that the serialized content is language-neutral. I
could write a C/C++ program or a Go program with the
same `.proto`{.markup--code .markup--p-code} file and read the data I
wrote using my `LogDbFile`{.markup--code .markup--p-code} example.
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [January 2, 2021](https://medium.com/p/a1a7d2d08cd7).

[Canonical
link](https://medium.com/@raysuliteanu/using-protocol-buffers-to-serialize-to-off-heap-memory-a1a7d2d08cd7){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
