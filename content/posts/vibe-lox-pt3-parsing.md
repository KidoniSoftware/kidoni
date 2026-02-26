---
title: "Vibe Coding a Lox Compiler, Part 3: Parsing & the Abstract Syntax Tree"
description: How vibe-lox turns a flat token stream into a typed Abstract Syntax Tree using a hand-written recursive descent parser.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - parsing
  - ast
  - recursive-descent
draft: false
---

{{% callout type="note" title="Written with AI" %}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{% /callout %}}


Previously in this series, [Part 1](vibe-lox-pt1-introduction) introduced the overall pipeline — scanner, parser, AST, and the multiple backends (tree-walk interpreter, bytecode VM, and LLVM codegen) — and [Part 2](vibe-lox-pt2-tokenization) covered tokenization: how winnow turns raw source text into a flat stream of typed tokens. Now we have that token stream in hand. The parser's job is to take that flat sequence and build a *tree* that captures the actual structure and meaning of the program.

## From Tokens to Structure

Here is why a flat list is not enough. Consider the expression `1 + 2 * 3`. After scanning, you have five tokens:

```
[ Number(1), Plus, Number(2), Star, Number(3) ]
```

That list has no inherent structure. It says nothing about which sub-expression to evaluate first. Should it be `(1 + 2) * 3 = 9` or `1 + (2 * 3) = 7`? Every programmer knows multiplication binds tighter than addition, so the correct reading is the second one. But a flat list of tokens cannot express that. A tree can:

```
      +
     / \
    1   *
       / \
      2   3
```

This is what S-expression notation encodes when the printer produces `(+ 1 (* 2 3))` — the nesting in the output directly mirrors the nesting in the tree. The left subtree of `+` is just the literal `1`; the right subtree is a whole multiplication sub-expression.

Trees also naturally represent nesting that has nothing to do with operator precedence. An `if` statement's then-branch is a sub-tree. A function body is a list of sub-trees. A class has a list of method sub-trees. The hierarchical nature of programs is what the Abstract Syntax Tree (AST) captures.

## Grammars and Recursive Descent

A *grammar* is a formal description of which sequences of tokens form valid programs. It is written as a set of rules, where each rule defines a syntactic concept in terms of other rules and terminal tokens. Here is a simplified excerpt of the Lox expression grammar, ordered from lowest to highest precedence:

```
expression  → assignment
assignment  → IDENTIFIER "=" assignment | or
or          → and ( "or" and )*
and         → equality ( "and" equality )*
equality    → comparison ( ( "!=" | "==" ) comparison )*
comparison  → term ( ( ">" | ">=" | "<" | "<=" ) term )*
term        → factor ( ( "-" | "+" ) factor )*
factor      → unary ( ( "/" | "*" ) unary )*
unary       → ( "!" | "-" ) unary | call
call        → primary ( "(" arguments? ")" | "." IDENTIFIER )*
primary     → NUMBER | STRING | "true" | "false" | "nil"
            | IDENTIFIER | "(" expression ")"
            | "this" | "super" "." IDENTIFIER
```

This is a *precedence ladder*. Rules near the bottom (`expression`, `assignment`) have the lowest precedence — they match the widest, loosest-binding constructs. Rules near the top (`primary`) have the highest precedence — they match the tightest, most atomic constructs.

*Recursive descent* is the technique of turning each grammar rule directly into a Rust method. When rule A references rule B, method `a()` simply calls `self.b()`. The precedence order falls out naturally from the call chain: to parse a `term`, you first call `factor()` for the left operand, then look for `+` or `-`, then call `factor()` again for the right operand. `factor` is always evaluated before `term`, so multiplication always binds tighter — no special-casing required.

The full chain in vibe-lox is:

```
expression → assignment → or → and → equality
          → comparison → term → factor → unary → call → primary
```

Each step in that chain is one Rust method.

## A Grammar Rule in Code

Let us look at three methods that together show the pattern clearly: `factor`, `unary`, and `primary`.

`factor` handles `*` and `/`. It follows the classic left-recursive binary operator pattern:

```rust
fn factor(&mut self) -> Result<Expr, CompileError> {
    let mut expr = self.unary()?;
    while let Some(op) = self.match_binary_op(&[TokenKind::Star, TokenKind::Slash]) {
        let right = self.unary()?;
        let span = Span::new(
            expr.span().offset,
            right.span().offset + right.span().len - expr.span().offset,
        );
        expr = Expr::Binary(BinaryExpr {
            id: next_id(),
            left: Box::new(expr),
            operator: op,
            right: Box::new(right),
            span,
        });
    }
    Ok(expr)
}
```

Parse the left side by calling `unary()`. Then loop: as long as there is a `*` or `/` token next, consume it, parse another `unary()` for the right side, and wrap everything into a `BinaryExpr`. The loop builds a left-associative chain — `a * b * c` becomes `((a * b) * c)` naturally.

`unary` handles prefix operators `!` and `-`. It is recursive rather than iterative, because prefix operators nest right-to-left (`!!x` means `!(!(x))`):

```rust
fn unary(&mut self) -> Result<Expr, CompileError> {
    if self.check(TokenKind::Bang) || self.check(TokenKind::Minus) {
        let start = self.current_span();
        let op = if self.match_token(TokenKind::Bang) {
            UnaryOp::Not
        } else {
            self.advance();
            UnaryOp::Negate
        };
        let operand = self.unary()?;   // recurse
        let span = Span::new(
            start.offset,
            operand.span().offset + operand.span().len - start.offset,
        );
        return Ok(Expr::Unary(UnaryExpr {
            id: next_id(),
            operator: op,
            operand: Box::new(operand),
            span,
        }));
    }
    self.call()
}
```

If neither `!` nor `-` is present, `unary` falls through to `call()` — the next level up the precedence ladder.

`primary` is the base case: it matches the atoms. It peeks at the current token and pattern-matches on its kind:

```rust
fn primary(&mut self) -> Result<Expr, CompileError> {
    let token = self.peek().clone();
    match token.kind {
        TokenKind::Number => {
            self.advance();
            let value: f64 = token
                .lexeme
                .parse()
                .expect("scanner guarantees valid number");
            Ok(Expr::Literal(LiteralExpr {
                id: next_id(),
                value: LiteralValue::Number(value),
                span: token.span,
            }))
        }
        TokenKind::True => {
            self.advance();
            Ok(Expr::Literal(LiteralExpr {
                id: next_id(),
                value: LiteralValue::Bool(true),
                span: token.span,
            }))
        }
        TokenKind::Identifier => {
            self.advance();
            Ok(Expr::Variable(VariableExpr {
                id: next_id(),
                name: token.lexeme,
                span: token.span,
            }))
        }
        TokenKind::LeftParen => {
            self.advance();
            let expr = self.expression()?;         // recurse back to the top
            self.consume(TokenKind::RightParen, "')' after expression")?;
            // ...
            Ok(Expr::Grouping(GroupingExpr { id: next_id(), expression: Box::new(expr), span }))
        }
        _ => Err(CompileError::parse(
            format!("expected expression, found '{}'", token.lexeme),
            token.span.offset,
            token.span.len.max(1),
        )),
    }
}
```

Notice the `LeftParen` arm: it calls `self.expression()`, which is the *top* of the precedence ladder. This is how parenthesised grouping works — the whole sub-expression inside the parens starts precedence resolution over from scratch.

## The AST in Rust

The AST is defined in `src/ast/mod.rs`. There are three top-level enums: `Decl` for declarations, `Stmt` for statements, and `Expr` for expressions.

```rust
pub enum Decl {
    Class(ClassDecl),
    Fun(FunDecl),
    Var(VarDecl),
    Statement(Stmt),
}

pub enum Stmt {
    Expression(ExprStmt),
    Print(PrintStmt),
    Return(ReturnStmt),
    Block(BlockStmt),
    If(IfStmt),
    While(WhileStmt),
}

pub enum Expr {
    Binary(BinaryExpr),
    Unary(UnaryExpr),
    Literal(LiteralExpr),
    Grouping(GroupingExpr),
    Variable(VariableExpr),
    Assign(AssignExpr),
    Logical(LogicalExpr),
    Call(CallExpr),
    Get(GetExpr),
    Set(SetExpr),
    This(ThisExpr),
    Super(SuperExpr),
}
```

Rust enums are a particularly good fit for ASTs for a few reasons:

**Exhaustive pattern matching.** When the interpreter visits an `Expr`, the compiler forces it to handle every variant. Add a new expression kind and every `match` on `Expr` that doesn't have a wildcard arm will fail to compile. This is exactly the kind of help you want when evolving a language.

**No nulls, no dynamic dispatch.** Each variant carries exactly the data it needs and nothing more. A `LiteralExpr` holds an `id`, a `LiteralValue`, and a `Span`. A `BinaryExpr` holds two boxed child `Expr`s and a `BinaryOp`. There is no base class, no `Option<Box<dyn Expr>>`, no runtime type checking.

**`LiteralValue`** is its own enum:

```rust
pub enum LiteralValue {
    Number(f64),
    String(String),
    Bool(bool),
    Nil,
}
```

Four variants, four possibilities, no ambiguity.

**Owned data.** AST nodes own their strings. There are no lifetimes tying AST nodes to the original source buffer. Nodes are freely clonable, which matters when the resolver needs to insert derived nodes (for instance, the synthetic `true` literal injected as a `for`-loop condition).

**`Span` on every node.** Every struct carries a `Span` — a `(offset, len)` pair into the original source text. Every expression, statement, and declaration knows exactly where it came from. This is what powers precise error messages: when a type error occurs at runtime, the interpreter can point at the exact characters in the source file that caused it.

**`ExprId` — a lightweight unique ID.** Each expression node has an `id: ExprId` field, generated from a global atomic counter at parse time:

```rust
static NEXT_EXPR_ID: AtomicUsize = AtomicUsize::new(0);

fn next_id() -> ExprId {
    NEXT_EXPR_ID.fetch_add(1, Ordering::Relaxed)
}
```

The resolver (covered in the next post) needs to annotate each variable reference with how many scope levels deep the variable lives. Rather than mutating the AST or wrapping expressions in a new type, the resolver just builds a `HashMap<ExprId, usize>`. The interpreter looks up the ID of each `Variable` or `Assign` expression at runtime to find the right scope depth. A clean separation with no structural changes to the AST.

## Error Recovery

Most toy parsers stop at the very first syntax error and bail out. That is convenient to implement but frustrating to use — fix one error, recompile, find the next error, repeat. vibe-lox reports *all* syntax errors in one pass.

The technique is called *panic-mode synchronisation*. When the parser encounters an unexpected token, it records the error, then calls `synchronize()`:

```rust
fn synchronize(&mut self) {
    self.advance();
    while !self.is_at_end() {
        if self.tokens[self.current - 1].kind == TokenKind::Semicolon {
            return;
        }
        match self.peek().kind {
            TokenKind::Class
            | TokenKind::Fun
            | TokenKind::Var
            | TokenKind::For
            | TokenKind::If
            | TokenKind::While
            | TokenKind::Print
            | TokenKind::Return => return,
            _ => {
                self.advance();
            }
        }
    }
}
```

The idea: skip tokens until you find something that looks like the start of a new statement — a semicolon (end of the previous statement), or a keyword that begins a fresh construct. Once there, resume normal parsing. Each recovered synchronisation point gives you an independent chance to find another error.

The top-level `parse()` loop illustrates how this ties together:

```rust
pub fn parse(mut self) -> Result<Program, Vec<CompileError>> {
    let mut declarations = Vec::new();
    while !self.is_at_end() {
        match self.declaration() {
            Ok(decl) => declarations.push(decl),
            Err(e) => {
                self.errors.push(e);
                self.synchronize();
            }
        }
    }
    if self.errors.is_empty() {
        Ok(Program { declarations })
    } else {
        Err(self.errors)
    }
}
```

Errors accumulate into a `Vec`. If there are five syntax errors in the file, all five are reported in one compiler run.

## Desugaring `for` Loops

One elegant thing a parser can do — beyond just recognising structure — is *desugaring*: translating one syntactic form into another, simpler one. The `for` statement is the clearest example in Lox.

A `for` loop in Lox looks like C:

```lox
for (var i = 0; i < 10; i = i + 1) {
    print i;
}
```

Rather than teaching every downstream component (interpreter, bytecode compiler, LLVM codegen) how to handle `for`, the parser rewrites it immediately into a `while` loop with an initializer block:

```rust
/// Desugar `for` into `while`.
fn for_statement(&mut self) -> Result<Stmt, CompileError> {
    // ... parse initializer, condition, increment, body ...

    // Append increment to body
    if let Some(inc) = increment {
        let inc_span = inc.span();
        body = Stmt::Block(BlockStmt {
            declarations: vec![
                Decl::Statement(body),
                Decl::Statement(Stmt::Expression(ExprStmt {
                    expression: inc,
                    span: inc_span,
                })),
            ],
            span: self.span_from(start),
        });
    }

    // Wrap in while
    let while_span = self.span_from(start);
    body = Stmt::While(WhileStmt {
        condition,
        body: Box::new(body),
        span: while_span,
    });

    // Wrap with initializer
    if let Some(init) = initializer {
        let block_span = self.span_from(start);
        body = Stmt::Block(BlockStmt {
            declarations: vec![init, Decl::Statement(body)],
            span: block_span,
        });
    }

    Ok(body)
}
```

The output is a `Stmt::Block` containing the initializer, wrapping a `Stmt::While` whose body is the original loop body followed by the increment expression. No `Stmt::For` variant exists in the AST at all. Every backend gets `while` for free.

If the condition clause is empty (i.e., `for (;;)` — a C-style infinite loop), the parser synthesises a `true` literal:

```rust
let condition = if !self.check(TokenKind::Semicolon) {
    self.expression()?
} else {
    Expr::Literal(LiteralExpr {
        id: next_id(),
        value: LiteralValue::Bool(true),
        span: self.current_span(),
    })
};
```

The desugared AST for `for (var i = 0; i < 10; i = i + 1) print i;` is confirmed by a unit test:

```rust
#[test]
fn for_desugars_to_while() {
    let sexp = parse_sexp("for (var i = 0; i < 10; i = i + 1) print i;");
    assert!(sexp.contains("while"));
    assert!(sexp.contains("var i"));
}
```

## Viewing the AST

When debugging the parser — or just satisfying curiosity about what the tree looks like — the `--dump-ast` flag is invaluable:

```
$ cargo run -- --dump-ast examples/fib.lox
```

The `to_sexp()` function in `src/ast/printer.rs` walks the AST and produces nested S-expressions:

```rust
pub fn to_sexp(program: &Program) -> String {
    let mut buf = String::new();
    for decl in &program.declarations {
        sexp_decl(&mut buf, decl);
        buf.push('\n');
    }
    buf
}
```

For `1 + 2 * 3;` it produces:

```
(+ 1 (* 2 3))
```

The nesting in the output directly mirrors the tree structure — `*` is nested inside `+`, confirming that multiplication was given higher precedence. For a function declaration like `fun foo(a, b) { return a + b; }`:

```
(fun foo (a b) (return (+ a b)))
```

For machine-readable inspection — useful when writing tooling or just staring at a very large program — the `--dump-ast` flag with JSON output serialises the entire tree via `to_json()`:

```rust
pub fn to_json(program: &Program) -> String {
    serde_json::to_string_pretty(program).expect("AST should be serializable")
}
```

Every node carries its `type` tag, all child nodes, and its `span`. You can pipe it through `jq` to query specific parts of the tree.

---

That covers the parser. We have a token stream going in and a typed, span-annotated, richly-structured Rust value coming out — with all `for` loops already desugared to `while` and multiple errors reported in a single pass.

Next up: the *tree-walk interpreter*. [Part 4](vibe-lox-pt4-interpreter) covers the first execution backend — including the resolver pass that determines exactly which declaration each identifier refers to and how many scope levels away it lives, the scoped environment chain that gives Lox its lexical scoping, closures, and the full OOP runtime for classes and instances.
