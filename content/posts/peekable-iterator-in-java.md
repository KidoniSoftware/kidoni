---
title: Peekable Iterators in Java
description: an implementation of an iterator allowing peeking ahead.
date: 2025-06-07
tags:
  - blog
  - java
  - rust
  - programming
draft: false
---

In Java there is your standard [Iterator](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/Iterator.html)
that has been around "forever" (since Java 1.2) and has `hasNext()` and `next()`
methods, to check if the iterator has more elements and to get the next one,
respectively. This is often sufficient, and can work well (though imperatively).
Java 5 added a new [Iterable](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/lang/Iterable.html)
interface along with the "enhanced for" loop, from which you can get an
`Iterator` and a couple other things (primarily a `forEach()` method).

These serve developers well enough, but interestingly Java has no standard
iterator that allows peeking ahead, without actually retrieving values from the
iterator. The [Queue](https://docs.oracle.com/javase/8/docs/api/java/util/Queue.html)
interface does have a `peek()` but there is no general ability to peek for other
things that can be iterated over.

While working on a project recently, I came across the need to be able to peek
ahead, and decided to roll my own. I'm sure there are some open source
libraries that provide a peekable iterator, but I figured it would be "fun" to
do it myself (and not spend any time looking for and adding the 3rd party
dependency).

## A `PeekableIterator<T>` Interface

I decided to keep it simple, and just address my use case, which required peeking
just one element ahead. A more general implementation could allow the user to
specify some (small) number of peek ahead values to keep track of but I only
needed one element. So I defined this new interface as

```java
public interface PeekableIterator<T> extends Iterator<T> {

  /** An iterator with a one-element peek-ahead.
   *
   * Peek one value ahead, if present. If peek() is called multiplle times before
   * a call to next(), the same value is always returned.
   *
   * @returns Optional.of(T) if there is another element, or Optional.empty()
 */
  Optional<T> peek();

}
```

It is a pretty straightforward interface. The Java [`Optional`](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/Optional.html)
type is a good fit here, since it's easy to then determine if there's a
value or not and get the value at the same time if present. Java's `Optional` is
somewhat akin to Rust's `Option` type. You'll see why I mention that in a bit.
The `Optional` type also has some nice "functional"-style methods like `map()`
and `filter()` and such-like.

{{< callout type="note" >}}
One thing I don't like about the `Optional` type is its `ifPresent()` method.
The `ifPresent()` method takes a closure, but returns `void`, so the action you
provide as a parameter can't directly return a value. I think this is a misfire.
I think it would be better to have returned `T`. Oh well. I suppose calling
`map()` could be the alternative, depending on the use case.
{{< /callout >}}


I implemented the interface as:

```java
import java.util.Iterator;
import java.util.Optional;

public class IterablePeekableIterator<T> implements PeekableIterator<T> {

  private final Iterator<T> iterator;
  private Optional<T> peeked = Optional.empty();
  private boolean hasPeeked = false;

  public IterablePeekableIterator(Iterable<T> iterable) {
    this.iterator = iterable.iterator();
  }

  @Override
  public boolean hasNext() {
    return hasPeeked || iterator.hasNext();
  }

  @Override
  public T next() {
    if (hasPeeked) {
      hasPeeked = false;
      return peeked.orElse(null);
    }
    return iterator.next();
  }

  @Override
  public Optional<T> peek() {
    if (!hasPeeked && iterator.hasNext()) {
      peeked = Optional.ofNullable(iterator.next());
      hasPeeked = true;
    }
    return hasPeeked ? peeked : Optional.empty();
  }
}
```

I wanted this implementation to work for anything that was iterable, so the
constructor takes `Iterable`. As I mentioned, I only needed one peek-ahead value,
so I keep track of that with a simple boolean, and save the peeked value (if any)
in an `Optional`. If you call `peek()` multiple times, the same value is always
returned, as the Javadoc described. On a call to `next()` if there is a peek-ahead
value, it is used and the peeked status is reset.

This worked well, and met my requirements. But as I continued with this project,
I realized I had another requirement. What I was doing was something like:

```java
  var t = tokens.peek().get();
  if (t == X || t == Y || t == Z) {
    tokens.next(); // consume token from iterator
    ...
  }
```

Basically, I wanted to consume the next token if it met some criteria. And I need
to do this in many different places. In another place rather than my fictional X,
Y and Z values, I had A, B and C values. What I wanted was something I use in
Rust on iterators, a "next if". Or rather, Rust has this on its built-in
["peekable" iterator](https://doc.rust-lang.org/std/iter/struct.Peekable.html#method.next_if)
that returns an Option. In Rust I can do something like

```rust
if let Some(t) = tokens.next_if(|t| t == foo) {
  // ...
}
```

So what the heck, I decided to implement that as well. It turns out to be quite
easy, and I could do it as a default implementation on the `PeekableIterator`
interface. My new and improved `PeekableIterator` is:

```java
public interface PeekableIterator<T> extends Iterator<T>, Iterable<T> {
  Optional<T> peek();

  default Optional<T> nextIf(Predicate<T> p) {
    if (peek().isPresent() && p.test(peek().get())) {
      return Optional.of(next());
    }

    return Optional.<T>empty();

  }
}
```

Now in my class using the `PeekableIterator` I can do

```java
var t = tokens.nextIf((t) -> t == FOO || t == BAR);
```

The result is an `Optional` so I could do any tests and mappings and what not,
like `map()` and such, as needed.

This worked out really well for me. It's not as good as what Rust provides,
though with the additional pattern matching support now in Java 24, it's getting
closer.

## Conclusion

This ability to peek ahead at iterator values comes up a lot (particularly if
you're building parsers), so I hope this is useful to someone can you can adapt
it to your own uses. If you have any suggestions for improvement, or any other
feedback, please leave them in the comments!

Happy coding.
