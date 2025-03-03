---
title: Using Java's New Gatherer Interface
description: Create new collectors using Java's Gatherer interface, using
some Rust methods as examples.
date: 2025-03-01
tags:
  - blog
  - java
  - rust
  - programming
draft: true
---

As a preview in JDK 23 and about to be final in the upcoming JDK 24, Java has
added a capability to its Stream API to create new collectors using a new
interface called [Gatherer](https://docs.oracle.com/en/java/javase/23/docs/api/java.base/java/util/stream/Gatherer.html).
Java has had a [Collector](https://docs.oracle.com/en/java/javase/23/docs/api/java.base/java/util/stream/Collector.html)
API for a while now, but the Gatherer interface addresses some limitations,
including the issue that there was no way to tell a Collector that processing
was complete. If there were still some data the Collector was processing, this
data was lost. You will see an example of this later.

Gatherers can be stateful or stateless. They can be serial or parallel. The JDK
will provide some built-in implementations, just as it provided for Collectors.
Gatherers are also meant to be composable, so you can link them up into a chain
providing higher level capabilities.

## Rust

In Rust, there are a lot of operations similar to what's available in Java's
Stream API ... things like `map` or `fileter`. But Rust's standard library
provides many more varied operations than are available for Streams in Java. As
examples of the `Gatherer` interface, I will implement two of Rust's methods
available on Rust slices: [split](https://doc.rust-lang.org/std/primitive.slice.html#method.split)
and [splitn](https://doc.rust-lang.org/std/primitive.slice.html#method.splitn).
These methods take a predicate function, and break up the input into slices
containing the elements up to the value matching the predicate. The difference
between the two methods is that `splitn` will return at most `n` slices. For
example, given

```rust
let s = [ 1, 2, 0, 3, 4, 0, 5, 6];
```

then if you had

```rust
let res = s.split(|n| *n == 0);
```

you would end up with 3 slices:

```rust
[1, 2],
[3, 4],
[5, 6]
```

however if you had

```rust
let res = s.splitn(2, |n| *n == 0);
```

you would end up with 2 slices:

```rust
[1, 2],
[3, 4, 0, 5, 6]
```

There are some interesting "edge" cases as well in the Rust split methods. For
example, if the predicate matches more than once "in a row" an empty slice is
emitted. Using a slightly tweaked example from above, if we have

```rust
let s = [ 1, 2, 0, 0, 5, 6];
let res = s.split(|n| *n == 0);
```

you'd have

```rust
[1, 2]
[]
[5, 6]
```

## Java

So let's see how we would do that in Java.

> [!note]
> As I mentioned, the `Gatherer` interface is still preview in JDK 23. To use it
> you will need to pass `--enable-preview` to the JVM when you run these
> examples. Or pass the flag via your build tool, like Gradle or Maven. I will
> show how to do it with Gradle.

### Constructing a Gatherer

The [Gatherer](https://docs.oracle.com/en/java/javase/23/docs/api/java.base/java/util/stream/Gatherer.html).
interface takes two static "of" methods, one for sequential gatherers and one
for parallel gatherers, each with a few variations depending on what your use
case is. I will let you read the documentation for the details. A `Gatherer`
can take up to four parameters: a supplier, an integrator, a combiner and a
finalizer.

- supplier: if you have a stateful gatherer, this is a function to initialize
  the state
- integrator: a function that does the main work of your gatherer
- combiner: a merging function taking two states and producing a combined state
- finalizer: called when downstream processing is complete, allowing your
  gatherer to deal with any pending work

For our `split` and `splitn` functions, we will have a sequential, stateful
gatherer. The state is the intermediate "slices" while we wait for the predicate
to match. I collect these gatherers into a single static utility class I've
ingeniously named `Gatherers`.

> [!note]
> For decades now I've adopted a pattern I first saw in `Spring Framework` code,
> to have static utility classes be `public abstract` classes. This avoids some
> "boilerplate" where you would otherwise need to create a private constructor
> so that class can't be instantiated.

In the `Gatherers` class I have static methods to create our splitters.

```java
public abstract class Gatherers {
    public static <T> Gatherer<T, ?, List<T>> split(Predicate<? super T> predicate) {
        return Gatherer.ofSequential(
                (), // TODO: supplier
                (state, element, downstream) -> { }, // TODO: integrator
                (state, downstream) -> { }); // TODO: finalizer
    }

    public static <T> Gatherer<T, ?, List<T>> splitn(int n, Predicate<? super T> predicate) {
        return Gatherer.ofSequential(
                (), // TODO: supplier
                (state, element, downstream) -> { }, // TODO: integrator
                (state, downstream) -> { }); // TODO: finalizer
    }
}
```
