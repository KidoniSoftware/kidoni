---
title: Using Java's New Gatherer Interface
description: Create new collectors using Java's Gatherer interface, using some Rust methods as examples.
date: 2025-03-01
tags:
  - blog
  - java
  - rust
  - programming
draft: false
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
Stream API ... things like `map` or `filter`. But Rust's standard library
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

I define two static methods creating instances of `Gatherer` for our two split
methods. At this stage they are almost identical except for the method names and
the extra `n` argument. I've elided the details for now, to show the overall
structure of the implementation. As I mentioned earlier, the supplier is called
once at the start of the stream processing, the integrator is called for each
element in the stream, and the finalizer is called when processing is complete.
The instance of state returned by the supplier is passed to the integrator and
finalizer. `downstream` is the next part of the stream.

To use the returned `Gatherer` instance, you create a stream like:

```java
var split = Stream.of(10, 40, 30, 20, 60, 50)
    .gather(Gatherers.splitn(2, (el) -> el % 3 == 0))
    .iterator();
```

In this example, the predicate will split the input into two results, based on
the first element that is divisible by 3 ... so if we iterated over the output
it will be:

```plain
10, 40
20, 60, 50
```

On the other hand, if we used `split` instead of `splitn`, the output would be:

```plain
10, 40
20
50
```

### Implementing split

Let's fill in the details of the `split` method.

```java
public static <T> Gatherer<T, ?, List<T>> split(Predicate<? super T> predicate) {
    class SplitState {
        final List<T> list = new ArrayList<>();
        boolean did_push;
    }    u

    return Gatherer.ofSequential(
            SplitState::new,
            (state, element, downstream) -> {
                if (predicate.test(element)) {
                    List<T> copy = List.copyOf(state.list);
                    state.list.clear();
                    downstream.push(copy);
                    state.did_push = true;
                }
                else {
                    state.list.add(element);
                    state.did_push = false;
                }

                return true;
            },
            (state, downstream) -> {
                if (state.did_push || !state.list.isEmpty()) {
                    downstream.push(List.copyOf(state.list));
                }
            });
}
```

I create an inner class to hold the state of the splitter. There is a list of
elements to accumulate values until the predicate matches. Then to match the
semantics of the Rust equivalent, I keep a boolean flag to know at finalization
whether the last thing I did was a push downstream. Simply checking whether the
state list is empty is not enough. This is because it's set in the predicate
match section as we'll see next. That means the method was called with a matching
value. So the state will be empty, but if the stream is now finalized, the Rust
semantics requires an empty set returned. I initialize the state calling
`SplitState::new`.

The integrator is obviously more complex, though not terribly so. If the predicate
matches, I make a (immutable) copy of the state list and it's the copy that is
sent downstream. I clear the state list so it starts fresh and set the flag that
I just did the push for the reason mentioned in the previous paragraph. Note that
the current i.e. matching element is discarded. Rust has a version of split
`split_inclusive` that includes the matching element in the output. Implementing
that is a simple tweak. If the predicate does not match, I add the element to the
list state and clear the push flag. In both cases I return `true` to indicate
stream processing can continue. Java's Stream API allows short-circuiting, in
which case you'd return false from the integrator.

Lastly, the finalize is straightforward, sending whatever is left in the state
list even if it's an empty list.

### Implementing splitn

The `splitn` method is almost identical to the `split` method. The main difference
is in the state, to keep track of how many splits have been done, and to check
that to decide if we should stop.

```java
public static <T> Gatherer<T, ?, List<T>> splitn(int n, Predicate<? super T> predicate) {
    class SplitState {
        final List<T> list = new ArrayList<>();
        boolean did_push;
        int splits = 1;
    }
    if (n < 1) {
      throw new IllegalArgumentException("n must be greater than 0");
    }

    return Gatherer.ofSequential(
            SplitState::new,
            (state, element, downstream) -> {
                if (state.splits < n && predicate.test(element)) {
                    List<T> copy = List.copyOf(state.list);
                    state.list.clear();
                    downstream.push(copy);
                    state.did_push = true;
                    state.splits++;
                }
```

The rest of the implementation is the same so I omit it here. I start the number
of splits at 1 because there is always at least one split. If `n` is 1 then it
doesn't matter what the predicate is, you just get all the elements of the stream
in the result.

## Building with Gradle

Until JDK 24 is released, you will need to pass the `--enable-preview` flag to
use the `Gatherer` interfaced as I mentioned. To do this with Gradle, you can do
the following:

```groovy
java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(23)
    }
}

compileJava {
    options.compilerArgs += ["--enable-preview"]
}

compileTestJava {
    options.compilerArgs += ["--enable-preview"]
}

tasks.named('test') {
    // Use JUnit Platform for unit tests.
    useJUnitPlatform()
    jvmArgs '--enable-preview'
}
```

## Conclusion

This overview just touches the surface of what you can do with the new `Gatherer`
interface. I didn't cover parallel gatherers, or how to compose gatherers. I
also didn't show anything about using the combiner function. But I feel this is
enough to get a sense of what you can do with the new interface. The code and
some unit tests for this blog is available on my
[GitHub](https://github.com/raysuliteanu/blog-examples/tree/main/java-gatherers).
