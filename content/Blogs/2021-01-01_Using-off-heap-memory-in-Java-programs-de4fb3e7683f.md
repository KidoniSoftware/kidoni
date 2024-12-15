---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Using off-heap memory in Java programs {#using-off-heap-memory-in-java-programs .p-name}

</div>

::: {.section .p-summary field="subtitle"}
One of the nice things about modern programming languages is Garbage
Collection. As a developer you don't have to worry much about...
:::

::: {.section .e-content field="body"}
::: {#3d10 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Using off-heap memory in Java {#071f .graf .graf--h3 .graf--leading .graf--title name="071f"}

<figure id="330d" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*sb-LVRHgi8YhllpD"
class="graf-image" data-image-id="0*sb-LVRHgi8YhllpD" data-width="6000"
data-height="4000" data-unsplash-photo-id="X_JsI_9Hl7o"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@zanilic?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@zanilic?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Zan</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

One of the nice things about modern programming languages is Garbage
Collection. As a developer you don't have to worry much about allocating
and freeing memory for your objects. With Java you just 'new' your class
and voila a new instance of the class. And when the instance is no
longer referenced, Java will take care of freeing the memory. When you
create objects this way, the JVM allocates memory from 'heap'
memory --- memory it manages for you.

So why would you want to do anything else?

In Java, the JVM allocates only so much heap space, when the JVM is
launched. How much heap is allocated can be controlled by command line
arguments:

``` {#9aca .graf .graf--pre .graf-after--p}
-Xms<size>        set initial Java heap size
-Xmx<size>        set maximum Java heap size
```

If you run out of heap, kaboom.

Also, depending on your use case, there could be performance reasons to
avoid the heap.

So how do you avoid the heap i.e. use "off-heap" memory? Java has
provided the java.nio package for quite a while now, and part of the
java.nio package is a Buffer interface and a Channel interface, with
various implementations like ByteBuffer and MappedByteBuffer and a
FileChannel and SocketChannel. I won't get into all the various things
you can do with the java.nio package here, but rather focus on the use
of off-heap memory.

To examine the use of off-heap memory, I will use an example of a "log
database", that is, an append-only immutable file-based "database". This
is how Kafka Topics are implemented, for example. I will use this
example to show using one approach to off-heap memory --- memory-mapped
files. The idea/capability of memory-mapped files has existed in
operating systems for a long time ... in \*nix systems, the
[`mmap`{.markup--code
.markup--p-code}](https://man7.org/linux/man-pages/man2/mmap.2.html){.markup--anchor
.markup--p-anchor
data-href="https://man7.org/linux/man-pages/man2/mmap.2.html"
rel="noopener" target="_blank"} [system
call](https://man7.org/linux/man-pages/man2/mmap.2.html){.markup--anchor
.markup--p-anchor
data-href="https://man7.org/linux/man-pages/man2/mmap.2.html"
rel="noopener" target="_blank"} has existed for decades.

In Java, when you use memory-mapped files, you are directly accessing
the OS memory, bypassing the Java heap. This allows you to have possibly
very large amounts of memory accessible to you, limited only by the
amount of memory available to the OS.

To create a memory-mapped file in Java, you create a
`FileChannel`{.markup--code .markup--p-code} and invoke the
`FileChannel.map()`{.markup--code .markup--p-code} method.

<figure id="438f" class="graf graf--figure graf--iframe graf-after--p">

</figure>

To create the channel you call `FileChannel.open()`{.markup--code
.markup--p-code} as shown, providing the location of the file as a
`java.nio.file.Path`{.markup--code .markup--p-code} and the options for
opening the file as a list of `StandardOpenOption`{.markup--code
.markup--p-code} enumeration values. Then calling
`FileChannel.map()`{.markup--code .markup--p-code} where you specify the
byte range of the file you want to map into memory. In this case I'm
mapping the entire file. The `FileChannel`{.markup--code
.markup--p-code} is not required after mapping into memory, so I use the
try-with-resource pattern to ensure the channel gets closed.

Now you can read and write to this file via the
`MappedByteBuffer`{.markup--code .markup--p-code} handle. Let's write a
header record to the file.

<figure id="6b00" class="graf graf--figure graf--iframe graf-after--p">

</figure>

I have a `FileHeader`{.markup--code .markup--p-code} record (been
experimenting with the new Java `record`{.markup--code .markup--p-code}
support) that contains a type and version. I convert this to a
`byte[]`{.markup--code .markup--p-code} and call the
`MappedByteBuffer.put()`{.markup--code .markup--p-code} method. This
will write the bytes to position 0 in the mapped file, since as we saw
in the `FileChannel.map()`{.markup--code .markup--p-code} method I
specified '0' as the starting position. The
`MappedByteBuffer`{.markup--code .markup--p-code} keeps track of the
last written position, so I can just keep writing to the buffer and the
offset is increased. You can manipulate the position e.g. if I wanted to
now read back the header I just wrote, I could call
`MappedByteBuffer.position(0)`{.markup--code .markup--p-code} and then
call `get()`{.markup--code .markup--p-code}.

<figure id="1afd" class="graf graf--figure graf--iframe graf-after--p">

</figure>

I hope this has given you a jump start in the use of off-heap memory in
Java.
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [January 1, 2021](https://medium.com/p/de4fb3e7683f).

[Canonical
link](https://medium.com/@raysuliteanu/using-off-heap-memory-in-java-programs-de4fb3e7683f){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
