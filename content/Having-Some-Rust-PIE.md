---
title: Having Some Rust PIE
description: Many descriptions of Rust call it a functional programming language but there are still object-oriented features that can and should be leveraged.
date: 2025-10-20
tags:
  - blog
  - rust
  - programming
  - object-oriented-programming
draft: true
---

Rust is often differentiated from object-oriented (OO) languages like Java or C++
by people who have a bias against the OO approach. Certainly OO design can create
brittle, hard to maintain/extend programs. But that's true of any language. But
there's nothing inherently wrong or bad about OO languages and programs written
in them. And those programmers with a bias against OO proclaim that functional
programming approaches and languages are the answer.

But guess what ... Rust has OO features, just as you can write functional
programs in Java an C++. In fact, [Chapter 18](https://doc.rust-lang.org/stable/book/ch18-00-oop.html)
of the Rust Book is on "Object-Oriented Programming Features".

## The Three Pillars of Object-Oriented Programming

Perhaps you are able to guess what the three pillars of OO programming are from
the title of this post. The mnemonic PIE has always helped me remember:

- Polymorphism
- Inheritance
- Encapsulation

One key thing I don't explicitly call out is the notion of 'object'. In a sense
I suppose I consider that as axiomatic. But I suppose it is worth calling out
and defining that an object is the combination of state and behavior into a
'unit' also known as an 'object'. In and of itself though, I do not consider this
sufficient to be "object oriented". Without polymorphism, inheritance and
encapsulation all you have is a way of structuring code. Rust is an OO language
if you consider just the ability to have state and behavior combined into named
units. The following Rust code is "object oriented" by this definition:

```rust
pub struct Animal {
    eating: bool,
    sleeping: bool,
    procreating: bool,
}

impl Animal {
    pub fn eat(&mut self) {
        self.eating = true;
        println!("eating");
    }

    pub fn sleep(&mut self) {
        self.sleeping = true;
        println!("sleeping");
    }

    pub fn procreate(&mut self) {
        self.procreating = true;
        println!("procreating");
    }
}
```

The `Animal` "object" has state and behavior. But really is that object-oriented?
That's just "normal" Rust code.

Until you have some PIE, you're not really object-oriented. Also, just having
some and not all of the pillars wouldn't make it OO. For example, the above code
has one of the pillars - Encapsulation. The state of the `Animal` is hidden
because it is not marked `pub` thereby encapsulating it from users of the
`Animal`. The only way to mutate the state of the `Animal` is via its
behavior-changing methods. So `Animal` supports encapsulation (and I understand
I haven't yet formally defined Encapsulation; stand by). This by itself does
not make it OO, but is definitely a beneficial capability of any programming
language.

To be really OO, you need all of the pillars, complimenting the foundational
structural aspect of a unit of state and associated behavior. So let's define
each of the pillars and show how Rust supports them - and where it doesn't,
at least as far as other so-called OO languages.

### Polymorphism

According to Wikipedia, polymorphism [is the provision of one interface to
entities of different data types.](<https://en.wikipedia.org/wiki/Polymorphism_(computer_science)>)
Basically, it's the ability of different types to seem (and act) like a common
type. This seems to me like what a Rust `trait` is. In [Chapter 12, Section 2](https://doc.rust-lang.org/stable/book/ch10-02-traits.html)
of the Rust Book, a trait is defined as

```text
A trait defines the functionality a particular type has and can share with other
types. We can use traits to define shared behavior in an abstract way.
```

Traits are the Rust mechanism to support polymorphism.

Let's tweak the earlier `Animal` example and turn `Animal` into a trait. We'll
just define some behavior, rather than have any associated state.

```rust
pub trait Animal {
    fn eat(&self) {
        println!("eating");
    }

    fn sleep(&self) {
        println!("sleeping");
    }

    fn procreate(&self) {
        println!("procreating");
    }

    fn talk(&self);
}

struct Dog;
struct Cat;

impl Dog {
    pub fn new() -> Self {
        Dog
    }
}

impl Cat {
    pub fn new() -> Self {
        Cat
    }
}

impl Animal for Dog {
    fn talk(&self) {
        println!("Woof!");
    }
}
impl Animal for Cat {
    fn talk(&self) {
        println!("Meow!");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let butch = Dog::new();
        let fluffy = Cat::new();
        act(butch);
        act(fluffy);
    }

    fn act(animal: impl Animal) {
        animal.eat();
        animal.sleep();
        animal.procreate();
        animal.talk();
    }
}
```

In this case, the polymorphism is showcased in the `act()` test method. As
far as the `act()` method is concerned, it doesn't know or care if the `Animal`
passed to it is a `Cat` or a `Dog`. This is obviously a trivial example, but
polymorphism is built-in and fundamental to any non-trivial Rust application.

All Rust developers use polymorphism in their programs, even if they're not
creating their own traits. Traits (and therefore polymorphism) are everywhere.
Do you use `Result<T, E>`? If so, then you use polymorphism because the `E`
generic parameter is some type of `std::error::Error` (if you're using `std`,
there's a `core::error::Error` for no-std) and these `Error` types are traits.

### Inheritance

Inheritance in Wikipedia [is defined as](<https://en.wikipedia.org/wiki/Inheritance_(object-oriented_programming)>)

```text
the mechanism of basing an object or class upon another object
(prototype-based inheritance) or class (class-based inheritance), retaining
similar implementation.
```

and speaking of the `Error` trait, you can see inheritance in Rust at work in
the trait definition:

```rust
pub trait Error: Debug + Display
```

Here, the `Error` trait is inheriting the behavior of the `Debug` and `Display`
traits as indicated by the colon. In other words, if you were to create your
own "object" implementing `Error` you'd also have to implement any required
methods of the `Debug` and `Display` traits. You could say that `Error` extends
`Debug` and `Error`.

### Encapsulation

## Closing

Is Rust an object-oriented programming language? Well, it's not not an OO language.
To me Rust is just a good programming language with various features that make
it generally useful. Rust would certainly be less useful _without_ polymorphism,
inheritance and encapsulation. And Rust is not a "pure" functional language, as
true/pure functions are not allowed to have side effects. But how do you, for
example, print anything to `stdout` without side effects?
