---
title: A Look At Pin in Rust
description: Self-referencing types are a challenge, no matter the language.
date: 2026-01-15
tags:
  - blog
  - rust
draft: true
---

In Rust, generally speaking, it's unusual to have self-referencing types i.e.
a field in a `struct` that "points" at another field of the same `struct`.

```c
#include <stdio.h>
typedef struct {
  char buf[1024];
  char *buf_ptr;
} foo_t;

int main(int argc, char **argv) {
  foo_t x;

  x.buf_ptr = &x.buf[512];
  printf("x: %p x.buf: %p x.buf_ptr: %p\n", &x, x.buf, x.buf_ptr);

  // copy 'x' into 'y'
  foo_t y = x;
  printf("y: %p y.buf: %p y.buf_ptr: %p\n", &y, y.buf, y.buf_ptr);

  /* in Rust you couldn't access 'x' anymore, it have been 'moved' */
  x.buf[512] = 'a';
  printf("x: %p x.buf: %p x.buf_ptr: %p x.buf[512] %c\n", &x, x.buf, x.buf_ptr,
         *x.buf_ptr);
  printf("y: %p y.buf: %p y.buf_ptr: %p y.buf[512] %c\n", &y, y.buf, y.buf_ptr,
         *y.buf_ptr);
}
```

```sh
a.out
x: 0x7ffe7bac8fa0 x.buf: 0x7ffe7bac8fa0 x.buf_ptr: 0x7ffe7bac91a0
y: 0x7ffe7bac93b0 y.buf: 0x7ffe7bac93b0 y.buf_ptr: 0x7ffe7bac91a0
x: 0x7ffe7bac8fa0 x.buf: 0x7ffe7bac8fa0 x.buf_ptr: 0x7ffe7bac91a0 x.buf[512] a
y: 0x7ffe7bac93b0 y.buf: 0x7ffe7bac93b0 y.buf_ptr: 0x7ffe7bac91a0 y.buf[512] a
```

![self-referencing type](/images/self-ref-example.png)
