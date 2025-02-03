---
title: My Three Must Read Books for the Working Software Developer
description: some book recommendations for developers
date: 2020-12-23
tags:
  - books
  - recommendation
  - programming
  - blog
draft: false
---

I've read a lot of books over my almost thirty year career as a software
developer. A lot of books have helped me understand various topics
related to building software, everything from books on learning new
programming languages to understanding particular architectures to how
to manage teams. But if you asked me to pick just three out of all the
books I've read, the three books I discuss here have had the most
profound positive impact on me as a developer.

That said, I reserve the right to amend the list at a future point, not
because new books will come out that I think should be in the top three,
but because I've probably forgotten some books that should make the
list. It's a variation of "what have you done for me lately" ... books
from 20 or 30 years ago may have slipped my mind. My core memory is not
what it used to be.

The three books are in no particular order. I recommend reading them
all. I would also like to hear from you (assuming someone reads this)
about what your top three books would be, and what you think of my top
three.

## Clean Code: A Handbook of Agile Software Craftsmanship by Robert C. Martin

First published in 2008, this book has shaped how I've written software
ever since I read it back when it came out. I had read other books by
Robert "Uncle Bob" Martin (see my next pick in fact), so I was
pre-disposed to look favorably on this new publication. Clean Code is a
very practical book. It deals with the every day aspects of writing
good, clean code. Some readers might feel like it's almost too basic at
points, and be tempted to skip sections. I discourage that. While you
might skim quickly in parts, I highly recommend reading every single
page.

One of the key takeaways from this book is that you are writing code not
for yourself, but for the developers that come after you. How you name
your classes, your variables, your methods, how you organize those
methods within a source file, these all matter, not so much for you
(though if you come back to your code months or years later it will help
you as well) but for those who have to maintain and enhance the software
when you've moved on.

One related aspect of this is that the software is the documentation.
Anyone who has written software and been involved in building production
code over time knows that any software documentation --- whether
internal design documents or public user-facing documentation --- is
never going to be 100% accurate about how the software really works as
that software evolves over time. The only real 100% accurate source of
truth about how the software actually works is the software code itself.

And the easier it is to read the code, the easier it is to understand
what it's doing. A corollary to that, described in the book, is that
comments in the code imply the code itself is not readable. Comments
generally should not be required if you've named and organized your code
properly. And comments are like any other non-code documentation ... it
can get out of sync with the actual code just like design documents and
user manuals.

Bottom line --- if you write software, read this book.

## Agile Software Development, Principles, Patterns, and Practices by Robert C. Martin

My next recommendation is also by "Uncle Bob".

> Pretty much read anything by Robert C. Martin and you can't go wrong.

This book covers a lot of territory. Under one cover you have a well
stated discussion of agile development combined with software design
patterns and best practices. It's a great one stop shop. You could read
other books on agile methods but you won't get anything about design
patterns. Or you could read books about design patterns and principles
but not get anything on agile. Sometimes when you get a book that covers
a broad set of topics, it's sort of a "jack of all trades, master of
none" issue. Not in this case.

## Design Patterns: Elements of Reusable Object-Oriented Software by Gamma et al

I actually considered having all three of my selections be "Uncle Bob"
books. But I think _Design Patterns_, a _bona fide_ classic that should
be read and understood by everyone and anyone writing software. You
don't have to memorize it, but you have to read an understand it.
Developers are often using the patterns described in this classic
without even realizing it, which is a shame.

The patterns described in this book --- factory, adapter, observer,
strategy, and the list goes on --- these are the fundamental building
blocks of software construction. Pretty much everything else is built on
this foundation. Without a solid foundation, you're building your
software on sand.

## Conclusion

So there you have it, my top three picks. As always when someone makes a
list like this, there are going to be a lot of differing opinions. There
are many more books I recommend. Several quickly jump to
mind ... _Refactoring: Improving the Design of Existing Code_ by Martin
Fowler, _Extreme Programming Explained: Embrace Change_ by Kent Beck,
and if you're a Unix geek like me, both _The Magic Garden Explained: The
Internals of Unix System V Release 4 : An Open Systems Design_ by James
Cox and Berny Goodheart and _Design and Implementation of the 4.4 BSD
Operating System_ by Marshall Kirk McKusick et al. (or 4.2 BSD or 4.3
BSD, depending on your era)

> A not-so-amusing aside, someone stole my copy of the 4.2 BSD book off
> my desk at work at my first job at Amdahl Corp; is nothing sacred?

Fundamentally though, if you could only buy three books to help you be a
better software programmer every single day, I think these three will
get you quite far.
