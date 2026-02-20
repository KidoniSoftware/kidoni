---
title: "Vibe Coding a Lox Compiler, Part 7: The REPL"
description: Building an interactive Lox REPL with backslash commands and tab completion using the rustyline crate.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - repl
  - rustyline
  - readline
draft: false
---

> [!note] Written with AI
> This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.

Previously in this series: [Part 1 — Introduction](vibe-lox-pt1-introduction), [Part 2 — Tokenization](vibe-lox-pt2-tokenization), [Part 3 — Parsing](vibe-lox-pt3-parsing), [Part 4 — The Tree-Walk Interpreter](vibe-lox-pt4-interpreter), [Part 5 — The Bytecode VM](vibe-lox-pt5-vm), and [Part 6 — LLVM Compilation](vibe-lox-pt6-llvm). This is the final post in the series.

Over six posts we have built the complete compiler pipeline: a winnow-based scanner, a recursive-descent parser, an AST, a tree-walk interpreter, a bytecode VM with its own compiler, and an LLVM IR code generator. What we have not talked about yet is the part that most users will touch first — typing something at a prompt and seeing what happens. This post is about the REPL.

## What Makes a Good REPL?

A REPL — Read–Eval–Print Loop — is the most immediate interface to a language. You type an expression, the interpreter runs it, and you see the result. The loop repeats. It sounds simple, but there are a few properties that separate a good REPL from a frustrating one.

**Persistent environment.** Variables and functions you define on line 1 are still there on line 10. If each iteration started fresh, you couldn't build anything incrementally — the REPL would be useful only for throwaway one-liners.

**Bare expression auto-printing.** In a script you write `print 1 + 2;`. In a REPL that's noise. When you type `1 + 2` at a prompt you want to see `3`, not silence. The REPL should detect bare expressions and print their values automatically.

**Line editing.** Without it, you can't use the arrow keys. Every typo requires a re-type of the whole line. History (up/down arrows) and reverse search (Ctrl-R) turn a REPL from a curiosity into a productive tool.

**Discoverability.** If the REPL has special commands, users should be able to find them. At minimum, `\help` (or equivalent) should list what's available. Tab completion makes that even better.

The vibe-lox REPL addresses all four.

## Persistent Environment

The interpreter is created once, before the loop starts, and reused across every iteration:

```rust
let mut interpreter = Interpreter::new();

loop {
    // ... read input ...

    let locals = match Resolver::new().resolve(&program) {
        Ok(l) => l,
        Err(errors) => { /* report and continue */ }
    };

    interpreter.merge_locals(locals);
    interpreter.set_source(&source);
    if let Err(e) = interpreter.interpret_additional(&program)
        && !e.is_return()
    {
        eprintln!("{}", e.display_with_line(&source));
    }
}
```

The key is `merge_locals`. The variable resolver runs fresh on each line — it doesn't know about previous lines. What `merge_locals` does is take the resolver's output for the new line and fold it into the interpreter's existing locals map rather than replacing it. The interpreter's global environment (where `var` declarations land) and its closure state also persist naturally because the `Interpreter` struct itself persists.

This means you can do exactly what you'd expect:

```lox
> var greeting = "hello";
> fun greet(name) { print greeting + ", " + name + "!"; }
> greet("world");
hello, world!
```

Each line is parsed and resolved independently, but the runtime state accumulates.

## Bare Expression Auto-Printing

The REPL wraps bare expressions in a `print` statement automatically. The decision lives in a small heuristic function:

```rust
/// Heuristic: treat the line as a bare expression if it doesn't end with
/// ';' or '}' and doesn't start with a keyword that begins a declaration
/// or statement.
fn is_bare_expression(line: &str) -> bool {
    if line.ends_with(';') || line.ends_with('}') {
        return false;
    }
    let first_word = line.split_whitespace().next().unwrap_or("");
    !matches!(
        first_word,
        "var" | "fun" | "class" | "if" | "while" | "for" | "print" | "return" | "{"
    )
}
```

If `is_bare_expression` returns `true`, the input is wrapped before scanning:

```rust
let source = if is_bare_expression(trimmed) {
    format!("print {trimmed};")
} else {
    trimmed.to_string()
};
```

The heuristic is deliberately simple. It is not perfect — a multi-line expression or one that ends with a closing parenthesis on its own line will not be wrapped correctly — but for the common single-line REPL case it works very well. A more sophisticated approach would require partial parsing to detect expression vs. statement, which adds significant complexity for a fairly rare edge case.

The unit tests give a sense of where the heuristic draws the line:

```rust
assert!(is_bare_expression("1 + 2"));
assert!(is_bare_expression("x"));
assert!(!is_bare_expression("var x = 1;"));
assert!(!is_bare_expression("print 1;"));
assert!(!is_bare_expression("{ var x = 1; }"));
assert!(!is_bare_expression("if (true) print 1;"));
assert!(!is_bare_expression("fun foo() {}"));
```

## Backslash Commands

The REPL supports four meta-commands for controlling the session itself:

| Short | Long       | Description                   |
|-------|------------|-------------------------------|
| `\h`  | `\help`    | Show available REPL commands  |
| `\q`  | `\quit`    | Exit the REPL                 |
| `\c`  | `\clear`   | Clear the terminal screen     |
| `\v`  | `\version` | Print the interpreter version |

The choice of `\` as the command prefix is intentional. Lox uses `/` as the division operator, so `/help` at the REPL prompt would be parsed as the division of an implicit left-hand side by `help` — a syntax error, not a command. Backslash is not a valid token in Lox (outside string literals), so `\quit` is unambiguously not a Lox expression. The dispatcher checks for the leading backslash before the input ever reaches the scanner:

```rust
if trimmed.starts_with('\\') {
    let mut parts = trimmed.split_whitespace();
    let cmd = parts.next().unwrap_or("");
    let args: Vec<&str> = parts.collect();
    if handle_command(cmd, &args) {
        break;
    }
    continue;
}
```

The `handle_command` function returns `true` when the REPL should exit, so `\quit` cleanly exits the loop without ever touching the parser:

```rust
/// Dispatch a backslash command. Returns `true` if the REPL should exit.
fn handle_command(cmd: &str, args: &[&str]) -> bool {
    if !args.is_empty() {
        eprintln!("warning: '{cmd}' does not accept arguments");
    }
    match cmd {
        "\\h" | "\\help" => {
            println!("REPL commands:");
            println!("  \\h, \\help     Show this help message");
            println!("  \\q, \\quit     Exit the REPL");
            println!("  \\c, \\clear    Clear the terminal screen");
            println!("  \\v, \\version  Show the interpreter version");
            false
        }
        "\\q" | "\\quit" => true,
        "\\c" | "\\clear" => {
            print!("\x1b[2J\x1b[H");
            io::stdout().flush().expect("flush stdout");
            false
        }
        "\\v" | "\\version" => {
            println!("{}", env!("CARGO_PKG_VERSION"));
            false
        }
        other => {
            eprintln!("Unknown command '{other}'. Type \\help for available commands.");
            false
        }
    }
}
```

The ANSI escape sequence `\x1b[2J\x1b[H` in `\clear` erases the screen and moves the cursor to the top-left — the same thing your terminal does when you run `clear` — without forking a subprocess.

## rustyline: readline for Rust

The earliest version of the REPL used `stdin.lock().read_line()`. That gives you exactly one feature: reading a line. No arrow keys. No history. No tab completion. Typing `greet("world")` incorrectly means retyping it from scratch.

Several crates address this. Here is why rustyline was chosen over the alternatives:

**`reedline`** is the line editor powering NuShell and is genuinely capable — syntax highlighting, multi-line input, menus, custom key bindings. But it is pre-1.0, and its API has shifted meaningfully between minor versions. More importantly, wiring up even basic tab completion requires coordinating three separate objects (a completer, a menu, and a key binding), which is more ceremony than the four static commands here warrant.

**`liner`** is minimalist but is effectively unmaintained, Unix-only, and poorly documented. Starting a new project on it would be a mistake.

**DIY via `crossterm`** is viable. Crossterm gives you cross-platform raw-mode terminal access. But a correct implementation — backspace, left/right arrow, Ctrl-A/Ctrl-E home/end, Ctrl-R reverse search, Unicode column math, bracketed paste — is 300–500 lines of careful code. These are all solved problems. rustyline already solves them.

**`rustyline`** is at v17, has had a stable API for nearly a decade, works on Linux, macOS, and Windows, and gives you Ctrl-R reverse search and arrow-key history for free the moment you use `Editor::readline`. The trait-based completion API is straightforward. It was the right choice here.

Setting up the editor takes four lines:

```rust
let config = Config::builder()
    .completion_type(CompletionType::List)
    .build();

let mut rl: Editor<ReplHelper, rustyline::history::DefaultHistory> =
    Editor::with_config(config).expect("rustyline init cannot fail with valid config");
rl.set_helper(Some(ReplHelper));
```

`CompletionType::List` gives Bash-style behaviour: on first Tab, expand to the longest common prefix; on second Tab, list all matches. That's the behaviour most developers already have muscle memory for.

## Tab Completion Implementation

Tab completion in rustyline comes from implementing the `Completer` trait, which has one method: given the current line and cursor position, return the start position of the completion token and a list of candidates.

The `ReplHelper` struct implements the full set of rustyline helper traits (`Completer`, `Hinter`, `Highlighter`, `Validator`, and the marker `Helper`). Only `Completer` has any real logic:

```rust
impl Completer for ReplHelper {
    type Candidate = Pair;

    fn complete(
        &self,
        line: &str,
        pos: usize,
        _ctx: &Context<'_>,
    ) -> rustyline::Result<(usize, Vec<Pair>)> {
        let prefix = &line[..pos];
        // Only complete backslash commands at the start of an otherwise empty line.
        if !prefix.starts_with('\\') || prefix.contains(char::is_whitespace) {
            return Ok((pos, vec![]));
        }
        Ok((0, complete_commands(prefix)))
    }
}
```

The actual filtering is extracted into its own function:

```rust
/// Return the commands from `COMMANDS` whose name starts with `prefix`.
fn complete_commands(prefix: &str) -> Vec<Pair> {
    COMMANDS
        .iter()
        .filter(|(cmd, _)| cmd.starts_with(prefix))
        .map(|(cmd, desc)| Pair {
            replacement: cmd.to_string(),
            display: format!("{cmd}  {desc}"),
        })
        .collect()
}
```

`COMMANDS` is a static slice of `(name, description)` pairs:

```rust
const COMMANDS: &[(&str, &str)] = &[
    ("\\help", "show this help message"),
    ("\\quit", "exit the REPL"),
    ("\\clear", "clear the terminal screen"),
    ("\\version", "show the interpreter version"),
];
```

The clever part: only the long forms are in `COMMANDS`, but prefix matching means the short forms work automatically. When the user types `\q` and presses Tab, `complete_commands("\\q")` finds `"\\quit"` (because `"\\quit".starts_with("\\q")`), and rustyline replaces the input with `\quit`. The short forms tab-complete to their long forms with no special handling.

Returning `(0, candidates)` instead of `(pos, candidates)` tells rustyline to start the replacement at position 0 — the very beginning of the line — so the entire `\q` is replaced by `\quit`, not appended to.

Extracting `complete_commands` as a standalone function rather than inlining it into the `Completer` impl has a concrete payoff: it is trivially testable without constructing a rustyline `Context`:

```rust
#[test]
fn complete_commands_all_on_backslash_only() {
    assert_eq!(complete_commands("\\").len(), 4);
}

#[test]
fn complete_commands_single_match() {
    let matches = complete_commands("\\q");
    assert_eq!(matches.len(), 1);
    assert_eq!(matches[0].replacement, "\\quit");
}

#[test]
fn complete_commands_short_forms_expand_to_long() {
    assert_eq!(complete_commands("\\h")[0].replacement, "\\help");
    assert_eq!(complete_commands("\\c")[0].replacement, "\\clear");
    assert_eq!(complete_commands("\\v")[0].replacement, "\\version");
}

#[test]
fn complete_commands_empty_for_unknown_prefix() {
    assert!(complete_commands("\\xyz").is_empty());
}
```

## What Goes in History

Only Lox expressions are added to the arrow-key history buffer:

```rust
// Only Lox expressions go into history, keeping it focused on code.
let _ = rl.add_history_entry(trimmed);
```

This call happens after the backslash-command check, so `\quit`, `\help`, and the rest never enter history. The reason is practical: history is for recalling and editing code you have written. `\quit` is a session control command — you would not want pressing the up-arrow to replay it, potentially exiting the REPL before you realise what happened. Keeping history clean means it stays useful.

## Where Next?

That wraps up the series. We started with a grammar document and a blank Rust project, and ended up with a tokenizer, a parser, a tree-walk interpreter, a bytecode compiler and VM, an LLVM IR code generator, and now an interactive REPL with history and tab completion.

The REPL as it stands is solid for everyday Lox experimentation, but there are obvious directions it could grow. Persistent history across sessions — so your arrow-key history survives after you close the terminal — is straightforward: rustyline supports it natively via the `with-file-history` feature flag and a `load_history` / `save_history` call pair. Multi-line input, so you can define a function body across several lines before execution, would require detecting unclosed braces and changing the prompt accordingly. Syntax highlighting is available through rustyline's `Highlighter` trait, which can colorize tokens as you type.

All seven posts cover the full pipeline: [tokenization](vibe-lox-pt2-tokenization), [parsing](vibe-lox-pt3-parsing), [the tree-walk interpreter](vibe-lox-pt4-interpreter), [the bytecode VM](vibe-lox-pt5-vm), [LLVM compilation](vibe-lox-pt6-llvm), and finally the REPL. The full source is on GitHub at [raysuliteanu/vibe-lox](https://github.com/raysuliteanu/vibe-lox) if you want to dig into any part of it.

Thanks for reading.
