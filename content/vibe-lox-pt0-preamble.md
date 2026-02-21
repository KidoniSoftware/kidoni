---
title: "Vibe Coding a Lox Compiler, Part 0: Background"
description: Using Claude Code to build a compiler and blog about it"
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - compilers
  - llvm
draft: false
---

I have been working with Claude Code for maybe a year, in various ways. Often, I
would use it to understand compiler error messages, since I've been teaching
myself Rust for that time and more, and as you might know, the Rust borrow
checker can give one fits. I would also purposefully limit my use of Claude when
programming Rust because I want to learn Rust, and you learn by doing; reading
code doesn't have the same impact. In some cases I worked on projects where I
would write the backend (whether Java or Rust) and have Claude build me the
frontend, since I am barely literate with frontend stuff and whatever literacy I
did have with JavaScript, Typescript, React, Angular or whatever I have been
quickly dumping from core memory.

During the last 18 months or so as I've been learning Rust, one of the projects
I worked on was a compiler for the Lox programming language from the book
[Crafting Interpreters](https://www.amazon.com/Crafting-Interpreters-Robert-Nystrom/dp/0990582930/),
working through it via the [CodeCrafters](https://app.codecrafters.io/courses/interpreter/overview)
site. Compilers have interested me since I took an undergraduate course on them,
way back in the day, and in general I enjoy the lower-level, under the hood kind
of thing ... think operating systems, embedded systems, virtual machines and the
like. So the interpreter project on CodeCrafters was a fun one for me. That said,
I never finished the project. I got about as far as implementing closures. Also,
since I was learning Rust, as I learned more Rust, I started over on my Lox
interpreter a few times, to try slightly different approaches, maybe try with
some Rust macros, whatever.

I also have a bit of ADD when it comes to hobby projects, since I often come
across new ideas or technologies I find interesting, and then I switch from what
I was working on and start on the latest shiny thing. Depending on what the
shiny thing was, I might use more Claude for help (like those frontend aspects I
mentioned). Using Claude to generate full projects, sometimes backend as well as
the frontend, I could see the models getting better at writing code. But I never
used Claude 100% for a full project - maybe 100% on the frontend, and 50-80%
backend at most. Then recently I got the idea - honestly I can't remember now
why, what prompted (pun semi-intended) it - why not see how Claude does creating
an implementation of the Lox interpreter/compiler and in doing so, compare to
what I had written by hand, combined with learning the parts beyond where I'd
gone myself, like the virtual machine implementation.

And so I did. And I also went beyond the book, with native code generation, as
you'll see. When Claude was done, it also occurred to me, why not also have
Claude author a series of blog posts about the project, to see how Claude does
in that aspect as well. Obviously people (including myself) have been using
Claude to do documentation, so I was sure it would be fine, but I thought it
would be an interesting complement to the code, having Claude write about what
it did.

So this blog series, in seven parts, was **100% written by Claude**. I did not
change a thing. The only thing I told it, beyond the general parameters of what
I wanted in the blogs, was to put a notice in each blog back to this introduction
to make sure everyone reading it knows clearly that I did not write this blog
series, for full disclosure.

All of the code is on GitHub at <https://github.com/raysuliteanu/vibe-lox/tree/blog-version>
on the `blog-version` branch (since I will probably continue to iterate on the
code with Claude for additional features based on my own interests, which of
course you're free to look at as well, but it may just not match the code
referenced in the blog series).

The blogs are best written in order, particularly if you're new to compilers,
but feel free to jump around based on your interests.

- [Part 1 - Introduction](vibe-lox-pt1-introduction)
- [Part 2 - Tokenization](vibe-lox-pt2-tokenization)
- [Part 3 - Parsing](vibe-lox-pt3-parsing)
- [Part 4 - Interpreter](vibe-lox-pt4-interpreter)
- [Part 5 - VM](vibe-lox-pt5-vm)
- [Part 6 - LLVM](vibe-lox-pt6-llvm)
- [Part 7 - REPL](vibe-lox-pt7-repl)

I am very interested to hear any comments or feedback on how you think Claude
did, both in the code and in the blog posts.

If you gain anything from these blogs and feel like supporting me in some way,
[consider buying me a coffee](https://www.buymeacoffee.com/raysuliteanu).
