---
title: Pattern Matching in Java and Rust
description: comparing Java's new pattern matchingb support with how Rust pattern matching works.
date: 2025-05-25
tags:
  - blog
  - java
  - rust
  - programming
draft: true
---

In this blog post, we'll take a look at the support for pattern matching in Java
that has enabled some language ergonomics that has existed in other languages for
a while. Pattern matching in this case refers to the capability in a language to
compare some data at runtime to various "patterns" describing how that data may
look, and based on that comparison, take different actions. In addition, as part
of the pattern matching, values of the data can be associated with/bound to
variables which can then be used in the actions.

Let's take a concrete example using Rust, which like many functional (or functional-like)
languages support as core capabilities. In a somewhat simple use case, consider
some code that is tokenizing input characters to parse input representing some
programming language. You might have

```rust
let chars = source.chars();
loop {
  if let Some(c) = chars.next() {
    // do something based on value of 'c'
  } else {
    break;
  }
}
```

In this example, we see pattern matching by checking if the iterator `chars.next()`
returns a `Some` value vs a `None` value, which is Rust's `Optional` type. In this
example, if the return value matches the pattern `Some` then the value returned from
the iterator is bound to `c` and the code can then use `c`. If the pattern matches
`None` this indicates the iterator is complete, and there is no more data in the
iterator, so we end the loop. This code as is isn't very idiomatic since a better
approach would be to use a `for` loop such as `for c in chars { ... }` but the
pattern matching isn't as obvious with the `for` loop, but it de-sugars to essentially
the same thing. Another way to write the above example is

```rust
let chars = source.chars();
loop {
  match chars.next() {
    Some(c) => { ... }
    None => break,
  }
}
```

Pattern matching in Rust is pervasive as it is in many functionally-oriented
languages. Destructuring data into values is a powerful feature of these languages.
So far these examples have shown a trivial example using a single `char` value.
But imagine a more complex data type. Another powerful feature of Rust is its
support for Algebraic Data Types. Continuing with the example of a language
parser, let's say we have a type called a `Token` and let's say there are different
types of tokens to represent the various language constructs ...

```rust
struct Token {
  token_type: TokenType,
}

enum TokenType {
  Number(f64),
  StringLiteral(String),
  Identifier(String),
  // ...
}
```

With pattern matching in Rust, you can write code like

```rust
if let Some(token) = tokens.next() {
  match token.token_type {
    Number(val) => // use val and span
    Identifier(val) => // use val and span
    // ...
  }
}
```

One thing to note is how enumeration discriminants in Rust can have data of
different types. In the above example it's relatively trivial, with just a single
value but it can be arbitrary data. Let's say we wanted to represent errors ...

```rust
enum ParseError {
  UnexpectedToken {
    actual: Token,
    expected: Token,
  },
  InvalidToken(Token),
  UnexpectedEof,
}
```

You can have a `struct` as data to a particular enum value, with named values;
you can have unnamed tuple values (accessed by position if not via pattern
matching), or just the discriminant itself. Now, using pattern matching, we can
easily take different actions based on the different possible errors:

```rust
match tokens.next() {
  Some(result) => match result {
    Ok(token) => {}
    Err(e) => match e {
      UnexpectedToken(act, exp) => {}
      InvalidToken(t) => {}
      UnexpectedEof => {}
    }
  }
  None => {}
}
```

## How About Java?

So, given these capabilities in Rust (and other languages), what can Java do?
Well, up until the last few releases, nothing nearly as elegant. But as of Java 24
just recently released, Java can support a lot of what I've shown so far.

### Java

The Java folks started adding support for pattern matching in about Java 17.
Prior to that, some things were verbose, some things had to be hand-rolled and
sometimes both (if at all). This of course is because of Java's parentage. But
even as of Java 24, one thing that Java doesn't support is Algebraic Data Types.
