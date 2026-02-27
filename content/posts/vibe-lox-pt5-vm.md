---
title: "Vibe Coding a Lox Compiler, Part 5: The Bytecode VM"
description: How vibe-lox compiles Lox to bytecode and executes it on a stack-based virtual machine — roughly 3× faster than tree-walking.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - bytecode
  - virtual-machine
  - stack-machine
draft: false
---

{{< callout type="note" title="Written with AI" >}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{< /callout >}}


This is part 5 of a series on building a Lox compiler in Rust. Parts 1 through 4 covered the
language and compiler pipeline ([Part 1](vibe-lox-pt1-introduction)), the tokenizer
([Part 2](vibe-lox-pt2-tokenization)), the parser and AST ([Part 3](vibe-lox-pt3-parsing)),
and the tree-walk interpreter ([Part 4](vibe-lox-pt4-interpreter)).

The tree-walk interpreter is simple and correct — it traverses the AST nodes directly and
evaluates each one. The simplicity is a feature for understanding language semantics, but it
carries real cost at runtime: every loop iteration re-traverses the same AST nodes, every
operation goes through Rust enum matching and pointer chasing, and there is no compact
representation of the program that can be saved and reloaded. This post introduces the second
execution backend: a bytecode VM that is roughly 3× faster on compute-intensive programs and
can save its compiled output to a `.blox` file for repeated runs without recompilation.

---

## Why a VM?

The tree-walk interpreter has two categories of overhead that a bytecode VM eliminates.

The first is structural. Rust enums are heap-allocated when they hold variable-length data, and
traversing a tree means following pointer after pointer to find the next thing to evaluate.
Cache lines miss. The CPU prefetcher cannot predict what to load next. On a tight loop over a
large AST, this adds up quickly.

The second is algorithmic. Every time the `while` loop body executes, the interpreter walks the
same AST subtree it walked on the previous iteration. There is no compilation step — the same
tree nodes are visited again and again.

A bytecode VM fixes both. The AST is compiled *once* into a compact, flat sequence of
single-byte opcodes. At runtime the VM runs a tight `loop { match opcode { … } }` dispatch
loop over a contiguous byte array. Cache behaviour is excellent; branching is predictable;
there is no redundant traversal.

The practical result: on a naive recursive Fibonacci benchmark (`fib(20)`), the tree-walk
interpreter takes roughly 150 ms; the bytecode VM takes roughly 50 ms — a 3× speedup without
any heroics.

The bytecode representation also unlocks something the interpreter cannot offer: persistence.
Running `cargo run -- --compile-bytecode hello.lox` serialises the compiled `Chunk` to a
`hello.blox` file. Running `cargo run -- hello.blox` later detects the magic header and runs
it via the VM, skipping the scan-parse-compile pipeline entirely.

---

## The Bytecode Format

The fundamental unit of the VM is the `Chunk` — a bundle of bytecode instructions, a constant
pool, and a parallel line-number table for runtime error messages. Here is its definition from
`src/vm/chunk.rs`:

```rust
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Chunk {
    pub code: Vec<u8>,
    pub constants: Vec<Constant>,
    pub lines: Vec<usize>,
}
```

`code` is a flat `Vec<u8>`. Every instruction is one byte (the opcode), optionally followed by
one or two operand bytes depending on the opcode. `lines` is a parallel array of the same
length — `lines[i]` holds the source line that emitted `code[i]`, so the VM can produce
useful error messages. `constants` is the constant pool.

The full opcode set lives in the `OpCode` enum:

```rust
#[repr(u8)]
pub enum OpCode {
    // Literals
    Constant, Nil, True, False,
    // Stack management
    Pop,
    // Variable access
    GetLocal, SetLocal,
    GetGlobal, SetGlobal, DefineGlobal,
    GetUpvalue, SetUpvalue,
    // OOP
    GetProperty, SetProperty, GetSuper,
    // Comparisons
    Equal, Greater, Less,
    // Arithmetic
    Add, Subtract, Multiply, Divide, Not, Negate,
    // I/O
    Print,
    // Control flow
    Jump, JumpIfFalse, Loop,
    // Functions
    Call, Invoke, SuperInvoke, Closure, CloseUpvalue, Return,
    // Classes
    Class, Inherit, Method,
}
```

The `#[repr(u8)]` attribute ensures each variant is exactly one byte, which is what lets the
VM decode instructions with a direct `match op { … }` on a raw byte.

Constants are not embedded inline in the bytecode stream. Instead, they are stored in the
constant pool and referenced by index. A `Constant` opcode is followed by a single byte — the
pool index — and the VM looks up `constants[idx]` at runtime:

```rust
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Constant {
    Number(f64),
    String(String),
    /// A function prototype: name, arity, upvalue count, and its own nested chunk.
    Function {
        name: String,
        arity: usize,
        upvalue_count: usize,
        chunk: Chunk,
    },
}
```

Numbers and strings are straightforward. `Function` is recursive — a function's body is itself
a `Chunk`, so the data structure is a tree of chunks. The index is one byte, which caps each
chunk's constant pool at 256 entries. That is enough for any realistic Lox function; a function
with more than 256 distinct literals is deeply unusual, and the compiler panics with a clear
message if the limit is hit.

---

## Stack-Based Execution

The VM is a *stack machine*: operands are pushed onto a stack, instructions pop their inputs
and push their result, and at the end of an expression exactly one value sits on top of the
stack — the result.

Consider evaluating `1 + 2 * 3`. Precedence means this is really `1 + (2 * 3)`. The compiler
walks the AST left-to-right and emits:

```
Constant  1.0     ; push 1.0 onto the stack
Constant  2.0     ; push 2.0
Constant  3.0     ; push 3.0
Multiply          ; pop 2.0 and 3.0 → push 6.0
Add               ; pop 1.0 and 6.0 → push 7.0
```

After the `Multiply`, the stack holds `[1.0, 6.0]`. `Add` pops both and pushes `7.0`. Clean
and mechanical.

Stack machines are often contrasted with *register machines*, which is the style used by LLVM
IR and by Lua 5+. In a register machine, instructions name their source and destination
registers explicitly: `ADD r1, r2 → r3`. This can be more efficient because fewer instructions
are needed — you never push a value just to pop it one instruction later — but the instruction
format is more complex, and the register allocator is non-trivial to write correctly.

For a teaching-scale implementation of Lox, a stack VM is the obvious choice. The instruction
format is minimal (an opcode, sometimes one operand byte), the dispatch loop is short enough to
fit in your head, and the semantics map directly onto what the source code says.

The dispatch loop itself lives in `Vm::run()` in `src/vm/vm.rs`:

```rust
fn run(&mut self) -> Result<(), RuntimeError> {
    loop {
        let frame_idx = self.frames.len() - 1;
        let ip = self.frames[frame_idx].ip;
        let chunk = &self.frames[frame_idx].closure.function.chunk;

        let op = chunk.code[ip];
        self.frames[frame_idx].ip += 1;

        match OpCode::try_from(op) {
            Ok(OpCode::Add) => {
                let b = self.stack.pop().expect("stack");
                let a = self.stack.pop().expect("stack");
                match (&a, &b) {
                    (VmValue::Number(x), VmValue::Number(y)) => {
                        self.stack.push(VmValue::Number(x + y));
                    }
                    (VmValue::String(x), VmValue::String(y)) => {
                        self.stack.push(VmValue::String(Rc::new(format!("{x}{y}"))));
                    }
                    _ => return Err(self.runtime_error("operands must be two numbers or two strings")),
                }
            }
            // ... all other opcodes
        }
    }
}
```

Each arm pops operands, computes a result, and pushes it. The `ip` is advanced past any
operand bytes by helper methods (`read_byte`, `read_u16`) that also increment `ip` as they go.
The `Vm` struct holding it all together:

```rust
pub struct Vm {
    stack: Vec<VmValue>,
    frames: Vec<CallFrame>,
    globals: HashMap<String, VmValue>,
    open_upvalues: Vec<Rc<RefCell<VmUpvalue>>>,
    output: Vec<String>,
    writer: Box<dyn Write>,
}
```

`stack` is the operand stack. `frames` is the call stack — one `CallFrame` per active function
call. `globals` is the global variable table. `open_upvalues` tracks live closures; more on
that shortly.

---

## The Single-Pass Compiler

The bytecode compiler in `src/vm/compiler.rs` is deliberately simple: it is a single-pass
compiler that walks the AST once and emits instructions directly. There is no intermediate
representation, no optimisation pass, no register allocation. AST in, bytecode out.

The key state struct is `CompilerState`:

```rust
struct CompilerState {
    function_type: FunctionType,
    chunk: Chunk,
    locals: Vec<Local>,
    upvalues: Vec<Upvalue>,
    scope_depth: i32,
    line: usize,
}
```

`chunk` accumulates the instructions being emitted. `locals` tracks every local variable in
scope — not as a hash map but as a simple `Vec<Local>`, where the position in the vector is
the slot number on the VM's stack. `scope_depth` tracks how deeply nested the current block is
(0 = global scope). `upvalues` records variables captured from enclosing functions.

When the compiler encounters a nested function, it pushes a new `CompilerState` onto a `states`
stack. When the function is done, it pops the state, wraps the emitted chunk in a
`Constant::Function`, and emits a `Closure` opcode in the *enclosing* chunk. This is why
functions are always represented as `Closure` at runtime — the constant pool holds the
prototype; the `Closure` opcode instantiates it.

Local variables are stored in the VM's stack frame at fixed slot positions. When the compiler
sees `var x = 1;` inside a block, it does not add `"x"` to any hash map — it just records
`x` in `locals` at position `locals.len()`. When it later sees `x` used in an expression, it
calls `resolve_local`, which walks `locals` from the end to find a matching name and returns its
index as the stack slot. `GetLocal 2` then tells the VM "push the value at slot 2 of the current
frame onto the operand stack." No hash lookup at runtime.

**Forward jumps** are the tricky part. When compiling an `if` statement, the compiler needs to
emit a `JumpIfFalse` instruction before it knows where the false branch begins — the target
offset is unknown until the then-branch has been compiled. The solution is backpatching:

```rust
fn emit_jump(&mut self, op: OpCode) -> usize {
    self.emit_op(op);
    let line = self.current().line;
    // Emit a placeholder 0xFFFF offset — we'll fill it in later
    self.current_mut().chunk.write_u16(0xffff, line);
    // Return the position of the placeholder bytes
    self.current().chunk.code.len() - 2
}

fn patch_jump(&mut self, offset: usize) {
    // Calculate how many bytes to jump over
    let jump = self.current().chunk.code.len() - offset - 2;
    // Write the real offset back into the placeholder slots
    self.current_mut().chunk.code[offset] = (jump >> 8) as u8;
    self.current_mut().chunk.code[offset + 1] = (jump & 0xff) as u8;
}
```

And the `if` compiler uses it like this:

```rust
self.compile_expr(&i.condition)?;
let then_jump = self.emit_jump(OpCode::JumpIfFalse);
self.emit_op(OpCode::Pop);
self.compile_stmt(&i.then_branch)?;
let else_jump = self.emit_jump(OpCode::Jump);
self.patch_jump(then_jump);   // now we know where the else branch starts
self.emit_op(OpCode::Pop);
if let Some(ref else_branch) = i.else_branch {
    self.compile_stmt(else_branch)?;
}
self.patch_jump(else_jump);   // now we know where past the else branch is
```

**Backward jumps** for `while` loops work differently: we know the loop-start offset *before*
emitting the loop body, so we can compute the backward offset directly when we reach the end:

```rust
fn emit_loop(&mut self, loop_start: usize) {
    self.emit_op(OpCode::Loop);
    // offset = current position - loop_start + 2 (for the two operand bytes we're about to write)
    let offset = self.current().chunk.code.len() - loop_start + 2;
    let line = self.current().line;
    self.current_mut().chunk.write_u16(offset as u16, line);
}
```

The `Loop` opcode subtracts its operand from `ip`, jumping backward to the loop condition.

---

## Closures and Upvalues

Closures in Lox are the classic challenge: a nested function can refer to variables in an
enclosing scope, but those variables live on the stack and get popped when the enclosing
function returns. How does the captured value survive?

The answer is upvalues, a technique from *Crafting Interpreters*. An upvalue starts as a
pointer into the stack:

```rust
#[derive(Debug, Clone)]
enum VmUpvalue {
    Open(usize),    // stack index: variable is still alive on the stack
    Closed(VmValue), // variable has been moved to the heap
}
```

While the enclosing function is still running, the upvalue is `Open(stack_idx)` — it points
directly to the stack slot holding the variable. When the variable goes out of scope, the
`CloseUpvalue` opcode fires: it reads the current stack value, transitions the upvalue to
`Closed(value)`, and pops the stack slot. From that point, any closure that holds a reference
to the upvalue reads and writes the heap-allocated `Closed` value instead.

This means closures always stay valid: if the enclosing function has returned, the upvalue is
`Closed` and holds its own copy; if the enclosing function is still on the stack, the upvalue
is `Open` and both the closure and the local variable see the same slot.

Multiple closures can share the same upvalue — the VM's `capture_upvalue` method checks
`open_upvalues` first and reuses an existing open upvalue for the same stack index. This is
what makes two closures that both capture the same variable correctly see each other's mutations.

All user-defined functions are represented at runtime as `VmClosure`, even functions that
capture nothing. A plain function is just a `VmClosure` with an empty `upvalues` vec. This
uniformity means the `Call` opcode always handles a `VmValue::Closure` — there is no special
case for "regular function vs closure," and no branching in the dispatch loop for this
distinction.

---

## Invoke Optimization

Method calls are extremely common in OOP-heavy Lox code. The naive implementation requires
two operations: `GetProperty` to look up the method on the instance (creating a temporary
`BoundMethod` object), followed by `Call` to invoke it.

The `Invoke` opcode fuses these into one. When the compiler sees a call expression of the form
`object.method(args)` — specifically a `Get` expression used directly as a callee — it emits
`Invoke` instead of `GetProperty` + `Call`:

```rust
Ok(OpCode::Invoke) => {
    let name = self.read_string_constant();
    let arg_count = self.read_byte() as usize;
    let receiver_idx = self.stack.len() - 1 - arg_count;
    let receiver = self.stack[receiver_idx].clone();
    if let VmValue::Instance(inst) = &receiver {
        // Check fields first (a field could shadow a method)
        if let Some(field) = inst.borrow().fields.get(&name).cloned() {
            self.stack[receiver_idx] = field.clone();
            self.call_value(field, arg_count)?;
        } else {
            let class = inst.borrow().class.clone();
            self.invoke_from_class(&class, &name, arg_count)?;
        }
    } else {
        return Err(self.runtime_error("only instances have methods"));
    }
}
```

The receiver stays at `stack[receiver_idx]` — slot 0 of the new frame, where `this` expects
it. No `BoundMethod` allocation, no extra stack push, one fewer opcode per method call. For
programs that call methods in a tight loop this is a meaningful win.

---

## The .blox Format and rmp-serde

Running `cargo run -- --compile-bytecode hello.lox` serialises the compiled `Chunk` to
`hello.blox`. The format is a 4-byte magic header followed by a MessagePack payload:

```rust
const BLOX_MAGIC: &[u8; 4] = b"blox";

fn save_chunk(compiled: &chunk::Chunk, path: &PathBuf) -> Result<()> {
    let payload = rmp_serde::to_vec(compiled)
        .context("serialize bytecode to MessagePack")?;
    let mut bytes = Vec::with_capacity(BLOX_MAGIC.len() + payload.len());
    bytes.extend_from_slice(BLOX_MAGIC);
    bytes.extend_from_slice(&payload);
    std::fs::write(path, bytes)
        .with_context(|| format!("write bytecode to '{}'", path.display()))
}
```

When the CLI receives a file argument, it reads the first four bytes and checks for the magic
number. If it matches, the file is deserialised and handed directly to the VM. If not, it is
treated as Lox source and run through the full pipeline. No file-extension sniffing.

The serialisation format is [MessagePack](https://msgpack.org/), via the `rmp-serde` crate.
Why MessagePack? The alternatives each have a real drawback for this use case:

- **`serde_json`**: human-readable but bloated for binary data. IEEE 754 doubles serialised as
  JSON decimal strings can lose precision in the round-trip, and the files are much larger.
- **`bincode`**: compact but not self-describing. If the field layout of `Chunk` or `Constant`
  changes, old `.blox` files silently deserialise into garbage or panic.
- **Raw bytecode**: minimal size but requires writing and maintaining custom serialisation for
  every field, including the recursive `Constant::Function` variant.
- **MessagePack**: compact binary (typically 2–3× smaller than JSON), self-describing (field
  tags are embedded, so the format is robust to additive schema changes), and zero extra work —
  `Chunk`, `Constant`, and `OpCode` already derive `serde::Serialize` and `Deserialize`, so
  `rmp_serde::to_vec(&chunk)` is all it takes.

To see what the compiler produces for a given program, the `--disassemble` flag prints a
human-readable listing. Here is what the output looks like for the Fibonacci function from
`fixtures/fib.lox`:

```lox
fun fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
```

Running `cargo run -- --disassemble fixtures/fib.lox` produces output like:

```
Compiled from "fixtures/fib.lox"
script;
  Constants:
    #0 = Function        fib

  Code:
      0: closure             #0     // <fn fib>
      2: define_global       #0     // fib
    ...

fun fib(_0);  // arity=1
  Constants:
    #0 = Number          1
    #1 = String          "fib"
    #2 = Number          1
    #3 = Number          2

  Code:
      0: get_local           1
      2: constant            #0     // 1
      4: less_equal          ...
      ...
     14: get_global          #1     // fib
     16: get_local           1
     18: constant            #2     // 1
     20: subtract
     21: call               1
     23: get_global          #1     // fib
     25: get_local           1
     27: constant            #3     // 2
     29: subtract
     30: call               1
     32: add
     33: return
```

Each line shows the byte offset, the opcode name in snake_case, and any operand — plus a `//`
comment for constant references. Nested functions are disassembled recursively below the
top-level script section, so the entire compilation unit is visible at once.

The disassembler lives in `chunk::disassemble` in `src/vm/chunk.rs` and is also available for
`.blox` files: `cargo run -- --disassemble hello.blox` works identically, loading and
disassembling the serialised chunk without re-running the compiler.

---

## Putting It All Together

The complete pipeline for bytecode execution is:

1. `scanner::scan(source)` — tokenise
2. `Parser::new(tokens).parse()` — build the AST
3. `Compiler::new().compile(&program)` — single-pass AST-to-bytecode compilation, producing a `Chunk`
4. `Vm::new().interpret(chunk)` — execute the dispatch loop

Steps 1–3 happen at compile time. If `--compile-bytecode` is passed, the `Chunk` is
serialised to disk here and the VM never runs. On subsequent runs, step 3 is replaced by
`load_chunk(path)` — deserialise directly from `.blox` — skipping the scanner, parser, and
compiler entirely.

The `Chunk` is also the input to the disassembler. The disassembler is not a separate tool; it
is just a function in `chunk.rs` that iterates over `code` the same way the VM does, printing
each instruction in human-readable form rather than executing it.

---

## What Is Next

With two execution backends in place — the tree-walk interpreter and the bytecode VM — the
natural question is: how fast can Lox programs go? In [Part 6](vibe-lox-pt6-llvm) we push
further: compiling Lox all the way to LLVM IR and from there to a native ELF executable. The
value representation changes (a tagged `{i8, i64}` struct instead of a Rust enum), a C runtime
library enters the picture, and the `inkwell` crate gives us safe Rust bindings for the LLVM
API. The result is Lox programs that run at native machine-code speed.
