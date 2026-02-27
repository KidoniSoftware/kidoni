---
title: "Vibe Coding a Lox Compiler, Part 1: Introduction & Compilers 101"
description: An introduction to the series and a Compilers 101 primer covering tokenization, parsing, ASTs, interpreters, VMs, and native compilation.
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

{{< callout type="note" title="Written with AI" >}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{< /callout >}}


If you have ever been curious about how programming languages actually work — how text you type into an editor ends up running as a program — this series is for you. We are going to build a complete compiler for a language called Lox, from scratch, in Rust. By the end you will have seen every layer of a real language implementation: the tokenizer, the parser, a tree-walk interpreter, a bytecode virtual machine, and an LLVM-powered native code compiler.

This first post sets the stage. We will meet the Lox language, walk through the conceptual pipeline that every compiler follows, and survey the three execution backends that vibe-lox implements. Later posts each take one of those layers and go deep. Let's start at the beginning.

---

## The Lox Language

Lox was designed by Robert Nystrom for his book [_Crafting Interpreters_](https://craftinginterpreters.com/), which is arguably the best introduction to language implementation ever written. Nystrom's goal was a language that hits a sweet spot: rich enough to be genuinely interesting, but small enough that one person can implement it completely in a single book. He nailed it.

Lox is dynamically typed, garbage collected, and object-oriented, with closures and single inheritance. That sounds like a lot — and it is — but the surface syntax is clean and familiar. Here is a taste:

```lox
fun fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}

print fib(10); // 55
```

And here is a class example showing inheritance:

```lox
class Animal {
  init(name) {
    this.name = name;
  }

  speak() {
    print this.name + " makes a sound.";
  }
}

class Dog < Animal {
  speak() {
    print this.name + " barks.";
  }
}

var d = Dog("Rex");
d.speak(); // Rex barks.
```

Real closures, real classes, real inheritance — in a language whose entire grammar fits in a couple of pages. That is why Lox makes such a good teaching subject: there is nowhere to hide complexity, and every design decision is visible.

The project we are building together is called **vibe-lox** and lives at [github.com/raysuliteanu/vibe-lox](https://github.com/raysuliteanu/vibe-lox). It implements the complete Lox language with three different execution backends, which we will explore throughout this series.

---

## Compilers 101: The Pipeline

Every language implementation — whether it is CPython, the Go compiler, GHC, or vibe-lox — runs source text through roughly the same conceptual pipeline:

```
Source Text
    |
    v
 Scanner / Tokenizer
    |
    v
   Tokens
    |
    v
   Parser
    |
    v
    AST  (Abstract Syntax Tree)
    |
    v
 [Optional: Semantic Analysis / Resolution]
    |
    v
  Execution
  (Interpreter / VM / Code Generator)
```

This pipeline is not a Lox-specific thing. It is not a Rust thing. It is a fundamental decomposition that has been refined over sixty years of language implementation. You will find it in every production compiler and interpreter ever written, just with different names and varying amounts of elaboration between the stages.

Each stage has one job: take a representation from the previous stage, do some work, and produce a better-structured representation for the next stage. Raw text is hard to work with directly. Tokens are easier. An AST — a tree that captures the grammatical structure — is easier still. Execution backends then consume the AST and do something useful with it.

vibe-lox implements the scanner, parser, and AST stages once, and then provides three different execution backends. Those backends are the interesting part of the story.

---

## Tokenization

Before a compiler can do anything useful, it needs to stop treating source code as a flat sequence of characters and start seeing it as meaningful units. Those units are called **tokens**.

Consider this expression:

```lox
var result = 123.4 * (x + 1);
```

The tokenizer reads this left to right and produces a stream roughly like:

| Lexeme   | Token type |
| -------- | ---------- |
| `var`    | Keyword    |
| `result` | Identifier |
| `=`      | Equal      |
| `123.4`  | Number     |
| `*`      | Star       |
| `(`      | LeftParen  |
| `x`      | Identifier |
| `+`      | Plus       |
| `1`      | Number     |
| `)`      | RightParen |
| `;`      | Semicolon  |

Whitespace and comments are consumed and discarded — they are not tokens, just separators. Multi-character sequences like `==` and `!=` are recognised as single tokens. Keywords like `var`, `if`, `class`, and `fun` are distinguished from user-chosen identifiers. Number literals are classified as numbers, string literals as strings.

By the time the tokenizer is done, the parser never has to think about individual characters. It works entirely in terms of typed tokens. This clean boundary makes each stage much simpler. Post 2 of this series goes deep on how vibe-lox implements the tokenizer using the `winnow` parser-combinator library.

---

## Parsing & the AST

With a token stream in hand, the parser's job is to figure out the grammatical structure of the program. "What is this sequence of tokens trying to say?" It does this by matching the token stream against a formal grammar — a set of rules that defines what valid Lox programs look like.

The style vibe-lox uses is called **recursive descent**: each grammar rule becomes a function, and parsing a rule may call the functions for other rules. The resulting call stack mirrors the nested structure of the program itself. Recursive descent is simple to write by hand, easy to extend, and produces good error messages — which is why nearly every production compiler uses it.

The output of the parser is an **Abstract Syntax Tree** (AST). Consider the expression `1 + 2 * 3`. The tokenizer sees five tokens. The parser, following the rule that multiplication binds tighter than addition, builds this tree:

```
    +
   / \
  1   *
     / \
    2   3
```

Notice that you do not need to know operator precedence rules to evaluate this tree correctly. The structure _is_ the precedence. To evaluate the tree you just walk it bottom-up: evaluate `2 * 3` first (because it is deeper), get 6, then evaluate `1 + 6` to get 7. No precedence tables needed at evaluation time.

Here is how vibe-lox represents expressions in Rust. The `Expr` enum from `src/ast/mod.rs` has a variant for every kind of expression the language supports:

```rust
pub enum Expr {
    Binary(BinaryExpr),    // e.g. a + b, x == y
    Unary(UnaryExpr),      // e.g. -x, !flag
    Literal(LiteralExpr),  // e.g. 42, "hello", true, nil
    Grouping(GroupingExpr),// e.g. (expr)
    Variable(VariableExpr),// e.g. x
    Assign(AssignExpr),    // e.g. x = expr
    Logical(LogicalExpr),  // e.g. a and b, a or b
    Call(CallExpr),        // e.g. foo(1, 2)
    Get(GetExpr),          // e.g. obj.field
    Set(SetExpr),          // e.g. obj.field = value
    This(ThisExpr),        // `this` inside a method
    Super(SuperExpr),      // e.g. super.method()
}
```

Each variant carries a struct with its specific fields. `BinaryExpr`, for example, holds a `left` expression, an `operator` (add, subtract, multiply, etc.), and a `right` expression — plus a source `span` for error reporting. The entire Lox grammar is encoded in these types, which means the Rust type system catches a whole class of bugs at compile time: you cannot accidentally treat a `CallExpr` as a `LiteralExpr`.

Post 3 covers the parser and AST in full detail.

---

## Three Execution Strategies

Once the AST is built, you have choices. vibe-lox implements three distinct strategies for turning the AST into results.

### Tree-Walk Interpretation

The simplest approach is to walk the AST recursively and evaluate each node directly. When you hit a `BinaryExpr`, evaluate the left subtree, evaluate the right subtree, apply the operator, return the result. When you hit a `CallExpr`, evaluate the arguments and call the function. No compilation step — you just traverse the tree and execute as you go.

This is the approach taken in the first half of _Crafting Interpreters_ and it is the default backend in vibe-lox. It is remarkably easy to implement and covers the full language, but it is slow: every operation requires multiple pointer dereferences to navigate the tree, and the overhead accumulates quickly on hot code.

When to use it: prototyping, scripting, any case where startup time matters more than throughput.

### Bytecode VM

The second approach compiles the AST into a sequence of compact instructions — **bytecode** — and runs those instructions in a tight dispatch loop called a virtual machine. The bytecode is much closer to what a real CPU does: push a constant, add two values, jump to an offset, call a function. The VM reads one instruction at a time and carries out the corresponding operation.

vibe-lox serialises its bytecode to `.blox` files using MessagePack, so you can compile once and run many times. The VM itself is a stack machine: instructions push operands and results onto a value stack, which avoids the need for explicit registers.

This is the approach taken in the second half of _Crafting Interpreters_ and it is significantly faster than tree-walking, because the dispatch loop is tight and the in-memory representation is compact. The trade-off is that you need a compiler that translates the AST to bytecode — which is another piece of code to write and maintain.

When to use it: general-purpose scripting, embedded languages, anywhere you want good runtime performance without the complexity of native compilation.

### Native Compilation via LLVM

The third approach goes all the way: compile the program to machine code. vibe-lox does this via **LLVM**, which we will cover in the next section. The result is a native ELF executable that runs at hardware speed with no interpreter overhead at all. Reaching this is the most complex path, but for compute-intensive programs the difference in performance can be dramatic.

When to use it: performance-critical applications where you need to squeeze out every cycle.

---

## What is LLVM?

LLVM is a compiler infrastructure project originally created at the University of Illinois and now maintained by a large open-source community (and backed heavily by Apple, Google, and others). Its central idea is an **Intermediate Representation** — LLVM IR — which is essentially a portable, typed assembly language. You compile your language to LLVM IR, and LLVM's optimiser and code-generation backends take it from there: they apply decades of compiler research (inlining, loop optimisation, register allocation, and much more) and emit machine code for x86, ARM, WebAssembly, RISC-V, and many other targets.

The upshot for language implementers is enormous: by targeting LLVM IR you get a production-quality optimising compiler backend for free, and you automatically support every platform LLVM supports. This is how Clang (C/C++), Rust, Swift, and Julia all achieve their performance. vibe-lox uses the `inkwell` crate to drive LLVM from Rust.

---

## The vibe-lox Architecture

Putting all of this together, here is how the pieces fit:

```
Source Code
    |
    v
  Scanner (src/scanner/)
  winnow-based tokenizer
    |
    v
   Tokens
    |
    v
  Parser (src/parser/)
  recursive descent
    |
    v
    AST (src/ast/)
    |
    v
  Resolver (src/interpreter/resolver.rs)
  variable resolution & scope analysis
    |
    +------------------------------------+------------------------------------+
    |                                    |                                    |
    v                                    v                                    v
Tree-Walk Interpreter            Bytecode Compiler                   LLVM IR Codegen
(src/interpreter/)               -> Bytecode VM                      (src/codegen/)
                                 (src/vm/)                                   |
                                     |                              +--------+--------+
                                     v                              |                 |
                              .blox bytecode                  LLVM IR (.ll)    Native ELF
                              + VM dispatch loop              via `lli`         executable
```

The key source modules are:

- **`src/scanner/`** — The tokenizer, implemented with the `winnow` parser-combinator library. Winnow lets you compose small recognisers into larger ones declaratively, which produces more maintainable scanner code than hand-rolling character-by-character loops.
- **`src/parser/`** — The recursive descent parser that turns the token stream into an AST.
- **`src/ast/`** — All the AST node type definitions, plus printers that render the AST as S-expressions or JSON (useful for debugging).
- **`src/interpreter/`** — The tree-walk interpreter, including the variable resolver that runs a semantic analysis pass over the AST before execution.
- **`src/vm/`** — The bytecode compiler, the bytecode chunk format, the disassembler, and the stack-based virtual machine.
- **`src/codegen/`** — LLVM IR generation via `inkwell`, plus a native compilation path that links the output into a standalone executable.
- **`src/repl.rs`** — The interactive Read-Eval-Print Loop, which lets you type Lox expressions and see results immediately.

The top-level dispatch in `src/main.rs` detects what the user wants based on CLI flags and routes accordingly — it will scan, parse, and then hand off to whichever backend is selected:

```rust
fn run_source(source: &str, filename: &str) -> Result<()> {
    let tokens = scanner::scan(source)
        .map_err(|errors| report_compile_errors(errors, filename, source))?;
    let program = LoxParser::new(tokens)
        .parse()
        .map_err(|errors| report_compile_errors(errors, filename, source))?;
    let locals = Resolver::new()
        .resolve(&program)
        .map_err(|errors| report_compile_errors(errors, filename, source))?;
    let mut interpreter = Interpreter::new();
    interpreter.set_source(source);
    interpreter
        .interpret(&program, locals)
        .map_err(|e| report_runtime_error(&e, Some(source)))?;
    Ok(())
}
```

Scan, parse, resolve, interpret. Four lines of meaningful work. Each stage is cleanly separated, which means swapping in a different backend is a matter of changing what happens after `resolve` — and that is exactly what the bytecode and LLVM paths do.

---

## What's Coming

This series has six more posts after this one, each taking a single layer of the pipeline:

- **Part 2 — Tokenization with winnow** dives into how the scanner works: what parser combinators are, how vibe-lox recognises numbers, strings, identifiers, and operators, and how it handles edge cases like unterminated strings and shebang lines.
- **Part 3 — Parsing & the AST** walks through the recursive descent parser in detail, covering operator precedence, statement parsing, and how the AST types are designed.
- **Part 4 — The Tree-Walk Interpreter** explains how the interpreter evaluates the AST, manages environments and scopes, implements closures, and handles Lox's class system.
- **Part 5 — The Bytecode VM** covers the bytecode compiler, the chunk format, the stack machine architecture, and how the VM executes instructions efficiently.
- **Part 6 — LLVM IR & Native Compilation** goes into the `inkwell` bindings, how Lox values are represented in LLVM's type system, and what it takes to emit correct machine code for a dynamically typed language.
- **Part 7 — The REPL** wraps up with a look at the interactive environment: incremental parsing, state persistence across lines, and the small details that make a REPL feel good to use.

Clone the repo, browse the code, and follow along. Each post will include the actual source so you can run the examples yourself. See you in Part 2.
