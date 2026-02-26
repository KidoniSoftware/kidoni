---
title: "Vibe Coding a Lox Compiler, Part 2: Tokenization"
description: How vibe-lox turns raw Lox source text into a stream of typed tokens using the winnow parser-combinator library.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - tokenization
  - winnow
  - parser-combinators
draft: false
---

{{% callout type="note" title="Written with AI" %}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{% /callout %}}


In [Part 1](vibe-lox-pt1-introduction) we introduced the Lox language and took a high-level tour of the full compiler pipeline — from raw source text all the way to native code. Now it's time to go deep on the first phase of that pipeline: tokenization. This is where a plain string of characters becomes something a parser can actually reason about.

## What is Tokenization?

When a compiler reads a source file, it starts with nothing more than a sequence of characters. Before any grammar rules can be applied, those characters have to be grouped into *tokens* — the smallest meaningful units of the language. This process goes by several names: tokenization, lexing, or scanning. Whatever you call it, the job is the same: walk left-to-right through the input, consume characters, and emit typed tokens.

A token has two key properties: its *kind* (what category it belongs to) and its *lexeme* (the actual text from the source). Consider this small Lox program:

```lox
if (x <= 123.4) print "hello\n";
```

The tokenizer sees the following distinct tokens:

- `if` — keyword
- `(` — left parenthesis
- `x` — identifier
- `<=` — two-character comparison operator
- `123.4` — numeric literal
- `)` — right parenthesis
- `print` — keyword
- `"hello\n"` — string literal (with the escape processed)
- `;` — semicolon

Whitespace between tokens is consumed and thrown away. Comments — anything from `//` to the end of the line — are consumed and thrown away too. Neither produces a token; they exist only as formatting for humans.

Notice that `<=` is a single token, not two. The scanner has to know that when it sees `<` followed immediately by `=`, those two characters belong together. That kind of lookahead is one of the more interesting decisions in scanner design.

## The Token Type

In vibe-lox, the token vocabulary lives in `src/scanner/token.rs`. The `TokenKind` enum lists every possible token type:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TokenKind {
    // Single-character tokens
    LeftParen, RightParen, LeftBrace, RightBrace,
    Comma, Dot, Minus, Plus, Semicolon, Slash, Star,

    // One or two character tokens
    Bang, BangEqual, Equal, EqualEqual,
    Greater, GreaterEqual, Less, LessEqual,

    // Literals
    Identifier,
    String,
    Number,

    // Keywords
    And, Class, Else, False, Fun, For, If, Nil, Or,
    Print, Return, Super, This, True, Var, While,

    Eof,
}
```

The grouping in comments isn't just decoration — it mirrors how the scanner handles them. Single-character tokens are trivial to match. The one-or-two-character group requires a one-character lookahead. Literals need their own sub-parsers. Keywords are syntactically identical to identifiers and are resolved by checking a lookup table after the identifier text is captured.

The `Eof` variant is always the final token in the stream. The parser uses it as a reliable sentinel instead of having to check for an empty list.

A token carries three things: its kind, the lexeme as an owned `String`, and a `Span`:

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Token {
    pub kind: TokenKind,
    pub lexeme: String,
    pub span: Span,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
pub struct Span {
    pub offset: usize,
    pub len: usize,
}
```

Owning the lexeme as a `String` is a deliberate choice. An alternative would be to store a `&str` slice into the original source — cheaper to create, no allocation — but then every type that holds a token needs a lifetime parameter, which spreads `'src` annotations throughout the AST, the interpreter, and the VM. The allocation cost at scan time is acceptable; the ergonomic cost of lifetime parameters everywhere is not.

`Span` stores a byte offset and a length, not a line and column. That might seem surprising, but it is actually the better design for a couple of reasons. First, during the hot scan loop the scanner never needs to count lines; it just records where it is in the byte stream. Second, line and column can always be computed on demand from the offset by counting newlines in the source text — and that only happens when formatting an error message, which is far off the hot path. The `miette` diagnostic library, which vibe-lox uses for error reporting, accepts `SourceSpan` values defined exactly this way, and `Span` has a trivial `From` impl for it.

## Why Parser Combinators? Why winnow?

There are several well-worn approaches to writing a tokenizer. Understanding the alternatives makes the choice clearer.

The most direct option is a **hand-written scanner**: a loop that inspects the current character, dispatches to a handler, and advances a cursor. This is completely transparent and gives you full control, but it also means writing a lot of repetitive character-inspection code, carefully handling all the multi-character cases, and managing the position cursor by hand. It works, but it's easy to introduce subtle bugs.

**`logos`** is a popular Rust crate that lets you derive a `Lexer` from an attribute-annotated enum. You annotate each variant with a regex or literal pattern and `logos` generates a DFA-based scanner. It's genuinely fast. The downside is that the generated tables are opaque — when something goes wrong, you're debugging through generated code — and customizing behavior (like escape sequences in strings) requires jumping through hoops.

**`nom`** is the original Rust parser-combinator library, with a large user base and lots of documentation. winnow is a fork of nom with a cleaner API, better error messages, and some ergonomic improvements that matter in practice.

**`pest`** uses a Parsing Expression Grammar written in a separate `.pest` file and generates Rust code from it. It's elegant if you prefer grammar-file-centric workflow, but it separates the grammar from the Rust types that consume it, which can feel awkward.

winnow wins for vibe-lox for a few concrete reasons:

- **Composability.** Each scanner function is a small piece that recognises one thing. They snap together with `alt` (try each alternative in order) and sequential application. You can read `scan_token` and see exactly what it tries, in what order, without tracing through a state machine.
- **`LocatingSlice<&str>`** is a built-in wrapper type that transparently tracks the current byte offset as parsing advances. Span tracking becomes free — call `input.current_token_start()` at the beginning and end of any sub-parser and you have your offsets.
- **Rust-native types.** Combinators return `Result` values; errors are just values; composition uses ordinary function calls. There's no code-generation step, no macro magic beyond what winnow provides for convenience, and no separate grammar file to keep in sync.

## Key Scanner Functions

All the action happens in `src/scanner/lexer.rs`. Let's walk through the main functions.

### The input type

```rust
type Input<'a> = LocatingSlice<&'a str>;
```

This type alias appears at the top of the file and threads through every scanner function. `LocatingSlice` wraps a `&str` and maintains an internal byte counter, so every parser automatically knows where it is in the source without any manual bookkeeping.

### `scan_all` — the entry point

```rust
pub fn scan_all(source: &str) -> Result<Vec<Token>, Vec<CompileError>> {
    let mut input = LocatingSlice::new(source);
    let _ = opt(shebang).parse_next(&mut input);
    let mut tokens = Vec::new();
    let mut errors = Vec::new();

    loop {
        if whitespace_and_comments(&mut input).is_err() {
            break;
        }
        if input.is_empty() {
            break;
        }
        match scan_token(&mut input) {
            Ok(token) => tokens.push(token),
            Err(_) => {
                let offset = input.current_token_start();
                let c = any::<_, ContextError>.parse_next(&mut input).ok();
                let ch = c.unwrap_or('?');
                errors.push(CompileError::scan(
                    format!("unexpected character '{ch}'"),
                    offset,
                    1,
                ));
            }
        }
    }

    let eof_offset = source.len();
    tokens.push(Token::new(TokenKind::Eof, "", Span::new(eof_offset, 0)));

    if errors.is_empty() {
        Ok(tokens)
    } else {
        Err(errors)
    }
}
```

The structure is a simple loop: skip whitespace and comments, check for end-of-input, try to scan the next token. If `scan_token` fails, consume one character and record an error — then keep going. At the end, always append the `Eof` sentinel.

The two error-path steps — consume one character, keep looping — are important. Without them, an unexpected character would leave the input cursor stuck in place and the loop would spin forever. With them, the scanner always makes progress, and all errors in the file get reported in one shot rather than stopping at the first problem.

### `scan_token` — the dispatcher

```rust
fn scan_token<'a>(input: &mut Input<'a>) -> ModalResult<Token> {
    alt((
        string_literal,
        number_literal,
        identifier_or_keyword,
        two_char_token,
        single_char_token,
    ))
    .parse_next(input)
}
```

winnow's `alt` tries each alternative in order and returns the first one that succeeds. The ordering here is intentional: string literals start with `"`, numbers start with a digit, identifiers start with a letter or underscore — these three can't be confused with each other. The two-character group comes before single characters so that `!=` is never accidentally consumed as `!` followed by `=`.

### `two_char_token` — handling `==`, `!=`, `<=`, `>=`

```rust
fn two_char_token<'a>(input: &mut Input<'a>) -> ModalResult<Token> {
    let start = input.current_token_start();
    let (kind, lexeme) = alt((
        "!=".value((TokenKind::BangEqual, "!=")),
        "==".value((TokenKind::EqualEqual, "==")),
        ">=".value((TokenKind::GreaterEqual, ">=")),
        "<=".value((TokenKind::LessEqual, "<=")),
    ))
    .parse_next(input)?;
    Ok(Token::new(kind, lexeme, Span::new(start, 2)))
}
```

Literal strings like `"!="` act as parsers in winnow: they consume exactly those bytes from the input and fail if they're not present. `.value(...)` transforms a successful match into a specific value. The result is declarative and readable: each arm says "if the input starts with this two-character sequence, produce this token kind."

### `identifier_or_keyword` — identifiers and keyword lookup

```rust
fn identifier_or_keyword<'a>(input: &mut Input<'a>) -> ModalResult<Token> {
    let start = input.current_token_start();
    let first: char = any
        .verify(|c: &char| c.is_ascii_alphabetic() || *c == '_')
        .parse_next(input)?;
    let rest: &str =
        take_while(0.., |c: char| c.is_ascii_alphanumeric() || c == '_').parse_next(input)?;
    let end = input.current_token_start();
    let mut lexeme = String::with_capacity(1 + rest.len());
    lexeme.push(first);
    lexeme.push_str(rest);
    let kind = keyword_kind(&lexeme).unwrap_or(TokenKind::Identifier);
    Ok(Token::new(kind, lexeme, Span::new(start, end - start)))
}
```

An identifier starts with an ASCII letter or underscore, then zero or more alphanumeric characters or underscores. After capturing that text, `keyword_kind` checks whether it matches a reserved word. If it does, the token gets the keyword kind; otherwise it's an `Identifier`. This is the standard way to handle keywords in a scanner — treating them syntactically as identifiers and resolving the distinction after the fact keeps the grammar simple.

The `keyword_kind` function in `token.rs` is a plain `match` expression over string slices:

```rust
pub fn keyword_kind(ident: &str) -> Option<TokenKind> {
    match ident {
        "and"    => Some(TokenKind::And),
        "class"  => Some(TokenKind::Class),
        "else"   => Some(TokenKind::Else),
        "false"  => Some(TokenKind::False),
        // ... and so on for all 16 keywords
        _        => None,
    }
}
```

### `string_literal` — escape sequences and all

```rust
fn string_literal<'a>(input: &mut Input<'a>) -> ModalResult<Token> {
    let start = input.current_token_start();
    '"'.parse_next(input)?;
    let mut s = String::new();
    loop {
        let c = any.parse_next(input)
            .map_err(|_| winnow::error::ErrMode::Cut(ContextError::new()))?;
        match c {
            '"' => break,
            '\\' => {
                let esc = any.parse_next(input)
                    .map_err(|_| winnow::error::ErrMode::Cut(ContextError::new()))?;
                match esc {
                    'n'  => s.push('\n'),
                    't'  => s.push('\t'),
                    '\\' => s.push('\\'),
                    '"'  => s.push('"'),
                    other => { s.push('\\'); s.push(other); }
                }
            }
            other => s.push(other),
        }
    }
    let end = input.current_token_start();
    Ok(Token::new(TokenKind::String, s, Span::new(start, end - start)))
}
```

String parsing is character-by-character. After the opening `"`, each character is read with `any` and accumulated into a `String`. When a `\` is encountered, the next character is consumed and translated: `\n` becomes a real newline, `\t` a real tab, and so on. Unrecognized escape sequences pass through with the backslash intact — a conservative choice.

The `.map_err(|_| ErrMode::Cut(...))` calls are important. Without them, a failure inside the string (such as hitting end-of-input before a closing `"`) would produce a *backtrackable* error that causes `alt` in `scan_token` to try the next alternative. Converting to `Cut` makes the error unrecoverable: "we are definitely inside a string, there is no alternative to try, this is an unterminated string literal."

The lexeme stored in the token is the *processed* value — the actual string content with escapes resolved — not the raw source text. When the parser later evaluates a string literal, it uses the lexeme directly.

### `number_literal` — integers and decimals, no trailing dot

```rust
fn number_literal<'a>(input: &mut Input<'a>) -> ModalResult<Token> {
    let start = input.current_token_start();
    let whole: &str =
        take_while(1.., |c: char| c.is_ascii_digit()).parse_next(input)?;
    let mut lexeme = whole.to_string();

    let checkpoint = input.checkpoint();
    let dot_result = '.'.parse_next(input);
    if dot_result.is_ok() {
        match take_while::<_, _, ContextError>(1.., |c: char| c.is_ascii_digit())
            .parse_next(input)
        {
            Ok(frac) => { lexeme.push('.'); lexeme.push_str(frac); }
            Err(_)   => { input.reset(&checkpoint); }
        }
    }
    // ...
}
```

Integers are straightforward: consume one or more digits. The fractional part requires a checkpoint. The scanner tries to consume a `.` — if that succeeds, it then looks for at least one more digit. If there are no digits after the dot (think `42.foo`), the checkpoint is restored so the `.` goes back into the input. This correctly handles Lox's rule that a trailing dot is not part of a number literal.

## Error Recovery

Most simple scanners stop at the first error. That's frustrating when you're fixing a file with several mistakes: fix the first error, recompile, find the next error, repeat. vibe-lox's scanner collects errors and continues.

The public API makes this contract explicit:

```rust
pub fn scan(source: &str) -> Result<Vec<Token>, Vec<CompileError>> {
    lexer::scan_all(source)
}
```

On success you get `Ok(Vec<Token>)`. On failure you get `Err(Vec<CompileError>)` — a list, not a single error. The scanner drives this by maintaining separate `tokens` and `errors` vectors in `scan_all`, accumulating into whichever is appropriate, and only deciding at the end which `Result` variant to return.

Each `CompileError` is a `miette::Diagnostic`, which means the error formatter can render it with source-code context, a caret pointing at the problematic character, and a diagnostic code. That makes for a much friendlier experience than a bare line-and-column message. Error reporting deserves its own post, so we won't linger here — just know the foundation is in place from the very first phase.

## A Fun Edge Case: Shebang Lines

Lox files can be made directly executable on Unix by adding a shebang:

```lox
#!/usr/bin/env -S cargo run --
print "hello, world!";
```

After a `chmod +x hello.lox`, you can run `./hello.lox` directly from the shell. The shell reads the shebang and invokes `cargo run -- hello.lox`.

The problem: `#` is not valid Lox syntax. Passing a file with a shebang to the scanner would produce an immediate "unexpected character '#'" error. The fix is a dedicated combinator:

```rust
fn shebang<'a>(input: &mut Input<'a>) -> ModalResult<()> {
    ("#!", take_till(0.., '\n'), opt('\n'))
        .void()
        .parse_next(input)
}
```

This consumes `#!`, then everything up to (but not including) the newline, then optionally the newline itself. It produces no token — `.void()` discards the matched text. In `scan_all`, it runs at the very top before the main loop:

```rust
let mut input = LocatingSlice::new(source);
let _ = opt(shebang).parse_next(&mut input);
```

The `opt` wrapper makes the shebang optional: if the file doesn't start with `#!`, the combinator simply does nothing and parsing continues normally.

Here's the subtle part: the shebang is skipped *inside the scanner, after `LocatingSlice` is set up*, not stripped by the caller before passing the string in. If the caller stripped it, the `LocatingSlice` would start at byte 0 of the already-truncated string, so all span offsets would be wrong — every error message would point to the wrong location. By consuming the shebang through the same `LocatingSlice` machinery, the byte counter advances past the shebang line, and all subsequent spans correctly reflect positions in the original file.

A test confirms this:

```rust
#[test]
fn shebang_code_spans_are_after_shebang_line() {
    // "#!/usr/bin/env lox\n" is 19 bytes, so `print` starts at offset 19
    let source = "#!/usr/bin/env lox\nprint 1;";
    let tokens = scan_ok(source);
    let print_span = tokens[0].span;
    assert_eq!(
        print_span.offset, 19,
        "print token should start after shebang line"
    );
}
```

The payoff is seamless: drop a shebang in a `.lox` file, `chmod +x` it, and it just runs. The rest of the toolchain — the parser, the interpreter, the error reporter — never has to know the shebang existed.

## Putting It Together

The scanner is the narrowest part of the compiler pipeline — it only ever moves forward through the input, one character at a time — but it establishes the vocabulary that every subsequent phase depends on. Get it wrong and parsing becomes impossible. Get it right and the parser sees a clean, well-typed stream of tokens to work with.

What makes the winnow approach satisfying is how directly the code maps to the intent. `scan_token` reads like a specification: "a token is a string literal, or a number, or an identifier-or-keyword, or a two-character operator, or a single-character operator, in that order of precedence." Each sub-parser is self-contained and testable in isolation. And the `LocatingSlice` wrapper gives span tracking for free, with no manual cursor arithmetic.

Next up in [Part 3](vibe-lox-pt3-parsing): the recursive-descent parser that consumes this token stream and produces an Abstract Syntax Tree.
