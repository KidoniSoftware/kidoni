---
title: "Vibe Coding a Lox Compiler, Part 6: LLVM IR & Native Compilation"
description: How vibe-lox compiles Lox to LLVM IR and native executables using the inkwell crate, a C runtime, and LLVM's TargetMachine.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - llvm
  - inkwell
  - native-compilation
  - codegen
draft: false
---

{{% callout type="note" title="Written with AI" %}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{% /callout %}}


Previously in this series, [Part 1](vibe-lox-pt1-introduction) introduced the project and the Lox language. [Part 2](vibe-lox-pt2-tokenization) built the tokenizer using `winnow`, [Part 3](vibe-lox-pt3-parsing) wrote the recursive descent parser, [Part 4](vibe-lox-pt4-interpreter) covered the tree-walk interpreter, and [Part 5](vibe-lox-pt5-vm) added a bytecode virtual machine as a second execution backend. At this point, vibe-lox has two ways to run a Lox program: walk the AST directly, or compile to bytecode and run it in a stack VM. This post covers the most ambitious backend yet: compiling Lox all the way to native machine code via LLVM.

---

## What is LLVM?

LLVM is a compiler infrastructure project, originally from the University of Illinois, now maintained by a large open-source community. At its core is the **LLVM IR** (Intermediate Representation): a typed, SSA-form assembly language that sits between your source language and machine code. It is higher-level than x86 — you have named registers, explicit types, structured control flow — but lower-level than most source languages. There are no loops or `if` statements in the way you write them in Rust; instead you have conditional branches, basic blocks, and phi nodes.

The key insight is: **target LLVM IR once, and LLVM's optimiser and backends turn it into fast machine code for every platform**. Want to emit x86? ARM? WebAssembly? RISC-V? LLVM handles the machine-specific details. You also get decades of compiler optimisation work — inlining, dead code elimination, auto-vectorisation, and much more — for free.

That bargain has attracted production languages: Clang (C and C++), Swift, Rust itself, Julia, and Zig all use LLVM as their backend. When you write a compiler that targets LLVM IR, you are plugging into the same infrastructure that compiles virtually all of today's native software.

LLVM IR is in **static single assignment (SSA)** form: every value is assigned exactly once and each use names that assignment directly. No mutable registers; instead, `alloca` instructions create stack slots, and `load`/`store` read and write them. `phi` nodes merge values from multiple predecessor blocks at join points in the control flow graph. It sounds complicated at first, but the `inkwell` crate — which vibe-lox uses — hides almost all of the SSA bookkeeping from you.

---

## inkwell: Safe Rust Bindings for LLVM

There are several options for generating LLVM IR from Rust:

- **Generating IR text by hand**: write strings like `%result = add i32 %a, %b`. This works for trivial examples but falls apart quickly — no type safety, brittle string formatting, impossible to maintain for a language with closures and classes.
- **`llvm-sys`**: raw FFI bindings to the LLVM C API. Works, but requires `unsafe` everywhere and careful manual lifetime management.
- **`cranelift`**: a pure-Rust code generator used by Wasmtime and rustc's debug backend. No LLVM dependency, which is attractive, but fewer optimisation passes and a smaller target ecosystem than LLVM.
- **`inkwell`**: wraps `llvm-sys` with a safe, ergonomic API. You work with Rust types like `Context`, `Module`, `Builder`, `FunctionValue`, `StructValue`. The `llvm21-1` feature flag in vibe-lox's `Cargo.toml` pins to LLVM 21.

inkwell maps cleanly to LLVM's three-layer model. A `Context` owns all LLVM type and value instances (the lifetime parameter `'ctx` you see everywhere in the codegen code is the context's lifetime). A `Module` holds a collection of functions and global declarations. A `Builder` is the cursor you use to emit instructions into a function; you position it at the end of a basic block and call methods like `build_call`, `build_conditional_branch`, `build_load`.

The `CodeGen` struct in `src/codegen/compiler.rs` holds all three:

```rust
pub struct CodeGen<'ctx> {
    context: &'ctx Context,
    module: Module<'ctx>,
    builder: Builder<'ctx>,
    lox_value: LoxValueType<'ctx>,
    runtime: RuntimeDecls<'ctx>,
    current_fn: Option<FunctionValue<'ctx>>,
    locals: HashMap<ExprId, usize>,
    scopes: Vec<HashMap<String, VarStorage<'ctx>>>,
    captures: CaptureInfo,
    current_lox_fn: String,
    return_target: Option<(PointerValue<'ctx>, inkwell::basic_block::BasicBlock<'ctx>)>,
    source: String,
}
```

`lox_value` and `runtime` are helpers we will cover shortly. `scopes` is a stack of variable bindings, and `captures` holds the results of a pre-pass that determines which variables are captured by closures. `return_target` tracks the alloca and exit block for structured early-return handling.

The top-level entry point is `codegen.emit(program)`, which calls `emit_main`, synthesises a C-compatible `main` function, walks every top-level declaration, and returns the finished `Module`.

---

## Representing Lox Values in LLVM

This is the conceptual heart of the whole backend, so it is worth being precise.

LLVM IR is **statically typed**: every instruction names an explicit type. `add i32` adds two 32-bit integers; `fadd double` adds two 64-bit floats. But Lox is **dynamically typed**: a variable can hold a number, a string, a class instance, or `nil`, and the type is only known at runtime.

The solution is a **tagged union**. Every Lox value is represented as a single LLVM struct with two fields:

```
{ i8, i64 }
  ^^^  ^^^
  tag  payload
```

The `i8` tag encodes the runtime type, and the `i64` payload carries the data, interpreted differently depending on the tag. The constants — which must match identically between the Rust codegen and the C runtime — are defined in `src/codegen/types.rs`:

```rust
pub const TAG_NIL:      u8 = 0;
pub const TAG_BOOL:     u8 = 1;
pub const TAG_NUMBER:   u8 = 2;
pub const TAG_STRING:   u8 = 3;
pub const TAG_FUNCTION: u8 = 4;  // closure
pub const TAG_CLASS:    u8 = 5;
pub const TAG_INSTANCE: u8 = 6;
```

For `nil`, the payload is zero. For `bool`, the payload is 0 or 1. For `string`, the payload stores a pointer to a null-terminated C string, cast to `i64`. For `function`, `class`, and `instance`, the payload is a pointer to a heap-allocated C struct, again cast to `i64`.

The tricky case is `number`. Lox numbers are 64-bit floats (`f64`), but the payload field is `i64`. You cannot directly store a float in an integer slot. The solution is a **bit-cast**: reinterpret the 8 bytes of the `f64` as an `i64` without any arithmetic conversion. The bits are preserved exactly; only their type interpretation changes. `build_number` in `LoxValueType` does this:

```rust
pub fn build_number(&self, builder: &Builder<'ctx>, value: f64) -> StructValue<'ctx> {
    let f = self.context.f64_type().const_float(value);
    let payload = builder
        .build_bit_cast(f, self.context.i64_type(), "num_to_i64")
        .expect("bitcast f64 to i64")
        .into_int_value();
    self.build_tagged_value(builder, TAG_NUMBER, payload)
}
```

And `extract_number` reverses it when you need to do arithmetic:

```rust
pub fn extract_number(&self, builder: &Builder<'ctx>, value: StructValue<'ctx>)
    -> FloatValue<'ctx>
{
    let payload = self.extract_payload(builder, value);
    builder
        .build_bit_cast(payload, self.context.f64_type(), "i64_to_f64")
        .expect("bitcast i64 to f64")
        .into_float_value()
}
```

To read the type tag from a live `LoxValue` struct, `extract_tag` uses `build_extract_value` — LLVM's instruction for pulling a field out of an aggregate (struct or array) value:

```rust
pub fn extract_tag(&self, builder: &Builder<'ctx>, value: StructValue<'ctx>) -> IntValue<'ctx> {
    builder
        .build_extract_value(value, 0, "tag")
        .expect("extract tag from LoxValue")
        .into_int_value()
}
```

The same header definition in `runtime/lox_runtime.h` captures the exact same layout in C:

```c
typedef struct {
    int8_t  tag;
    int64_t payload;
} LoxValue;
```

This shared layout is what allows Lox IR and the C runtime to exchange values seamlessly across the FFI boundary.

---

## The C Runtime

LLVM IR can call any C function. vibe-lox uses this heavily: everything that requires heap allocation, string manipulation, or complex data structures lives in a C runtime at `runtime/lox_runtime.c`.

The runtime is compiled to `lox_runtime.o` by `build.rs` at Cargo build time, so it is an invisible part of every build. The relevant `build.rs` code:

```rust
fn main() {
    println!("cargo:rerun-if-changed=runtime/lox_runtime.c");
    println!("cargo:rerun-if-changed=runtime/lox_runtime.h");

    let cc = env::var("CC").unwrap_or_else(|_| "gcc".to_string());
    Command::new(&cc)
        .args(["-Wall", "-Wextra", "-O2", "-fPIC", "-c", "-o"])
        .arg(&obj_output)
        .arg(&source)
        .status()
        // ...

    println!("cargo:rustc-env=LOX_RUNTIME_OBJ={}", obj_output.display());
}
```

The `LOX_RUNTIME_OBJ` env variable is baked into the binary at compile time (via `env!`), so `native.rs` always knows where the object file lives at link time.

The key runtime functions, declared in `src/codegen/runtime.rs` as `extern` prototypes so inkwell knows their signatures:

- **`lox_print(LoxValue)`** — switches on the tag and prints in the correct format. Numbers get special handling: integers are printed without a `.0` suffix (matching Lox semantics), which requires checking `floor(d) == d` in C.
- **`lox_global_get` / `lox_global_set`** — a simple linear-search table for global variables. Fast enough for typical Lox programs, which have few globals.
- **`lox_value_truthy(LoxValue) -> i1`** — `nil` and `false` are falsy; everything else is truthy.
- **`lox_alloc_closure`** — allocates a `LoxClosure` struct on the heap, storing the function pointer, arity, name, and a copy of the captured-variable pointer array.
- **`lox_alloc_cell` / `lox_cell_get` / `lox_cell_set`** — allocate and access a single heap-allocated `LoxValue`, used as the mutable shared cell for captured variables.
- **`lox_alloc_instance`** — allocates a `LoxInstance` struct and returns a `LoxValue` with `TAG_INSTANCE`.
- **`lox_instance_get_property`** — first checks the instance's field array by name, then walks the class's method table (and up the superclass chain) and returns a bound method closure if found.
- **`lox_class_find_method`** — walks the class hierarchy: `for (LoxClassDesc *k = klass; k != NULL; k = k->superclass)`.

Because `lli` (the LLVM IR interpreter) cannot link against object files by default, you must pass the runtime explicitly:

```bash
lli --extra-object runtime/lox_runtime.o hello.ll
```

---

## Capture Analysis

Before generating any IR, vibe-lox runs a pre-pass over the entire AST: `analyze_captures` in `src/codegen/capture.rs`. Its purpose is to answer a single question for every variable: **does any inner function reference this variable?**

If yes, the variable must live on the heap — in a `LoxCell` — so that closures and the enclosing scope share the same storage and mutations are visible to all. If no, the variable can be a plain stack `alloca` (just an `i64` on the function's stack frame, cheap and fast).

The `CaptureInfo` struct records two things:

```rust
pub struct CaptureInfo {
    /// Variables captured by at least one inner function,
    /// keyed by (var_name, declaring_function).
    pub captured_vars: HashSet<CapturedVar>,

    /// For each function, the ordered list of variable names
    /// it captures from enclosing scopes.
    pub function_captures: HashMap<String, Vec<String>>,
}
```

The analyser works by maintaining a stack of function scopes. When it encounters a variable reference, it walks the stack from innermost to outermost. If it finds the variable's declaration in a different function scope, the variable is captured. Intermediate functions in the call chain are also marked as needing to thread that variable through their environment, which is how deeply nested closures work.

`VarStorage` in `compiler.rs` reflects the result:

```rust
enum VarStorage<'ctx> {
    /// Stack-allocated alloca (not captured).
    Alloca(PointerValue<'ctx>),
    /// Heap-allocated cell (captured by at least one closure).
    Cell(PointerValue<'ctx>),
}
```

At every variable declaration site, the codegen checks `captures.captured_vars` and allocates either an `alloca` or a `lox_alloc_cell` call accordingly.

---

## Generating LLVM IR

With value representation and capture analysis in hand, the codegen walks the AST and emits instructions.

### Functions

Every Lox function declaration becomes an LLVM function. Its signature takes a pointer to the captured-variable environment array as the first parameter, followed by one `LoxValue` per Lox parameter, and returns a `LoxValue`:

```
define lox_fn_add(%env: ptr, %a: {i8, i64}, %b: {i8, i64}) -> {i8, i64}
```

The codegen in `compile_fun_decl` saves all current compilation state (current function, scopes, return target, builder position), compiles the function body, then restores the state. This lets functions be compiled inline as they are encountered in the source — including nested function definitions.

The captured environment is passed as an array of cell pointers (`LoxValue**`). At the entry block of each function, the codegen GEPs into that array to load each captured cell pointer:

```rust
let cell_ptr_ptr = unsafe {
    self.builder.build_gep(
        ptr_type,
        env_param,
        &[self.context.i64_type().const_int(i as u64, false)],
        &format!("env_{cap_name}_ptr"),
    ).expect("GEP into env array")
};
let cell_ptr = self.builder
    .build_load(ptr_type, cell_ptr_ptr, &format!("env_{cap_name}"))
    .expect("load cell ptr from env")
    .into_pointer_value();
```

### Control Flow

LLVM IR has no implicit fall-through between instructions. Every basic block must end with a terminator: either a branch or a return. That means `if` and `while` are built out of explicit blocks and branch instructions.

Here is `compile_if`:

```rust
fn compile_if(&mut self, if_stmt: &IfStmt) -> anyhow::Result<()> {
    let condition = self.compile_expr(&if_stmt.condition)?;
    let cond_bool = self.emit_truthy(condition);  // calls lox_value_truthy

    let then_bb  = self.context.append_basic_block(current_fn, "then");
    let merge_bb = self.context.append_basic_block(current_fn, "merge");

    if let Some(else_branch) = &if_stmt.else_branch {
        let else_bb = self.context.append_basic_block(current_fn, "else");
        self.builder.build_conditional_branch(cond_bool, then_bb, else_bb)
            .expect("conditional branch");

        self.builder.position_at_end(then_bb);
        self.compile_stmt(&if_stmt.then_branch)?;
        self.builder.build_unconditional_branch(merge_bb).expect("...");

        self.builder.position_at_end(else_bb);
        self.compile_stmt(else_branch)?;
        self.builder.build_unconditional_branch(merge_bb).expect("...");
    } else {
        self.builder.build_conditional_branch(cond_bool, then_bb, merge_bb)
            .expect("conditional branch");
        self.builder.position_at_end(then_bb);
        self.compile_stmt(&if_stmt.then_branch)?;
        self.builder.build_unconditional_branch(merge_bb).expect("...");
    }

    self.builder.position_at_end(merge_bb);
    Ok(())
}
```

And `compile_while` adds a loop-back edge:

```rust
fn compile_while(&mut self, while_stmt: &WhileStmt) -> anyhow::Result<()> {
    let cond_bb = self.context.append_basic_block(current_fn, "while_cond");
    let body_bb = self.context.append_basic_block(current_fn, "while_body");
    let exit_bb = self.context.append_basic_block(current_fn, "while_exit");

    self.builder.build_unconditional_branch(cond_bb).expect("...");

    self.builder.position_at_end(cond_bb);
    let condition = self.compile_expr(&while_stmt.condition)?;
    let cond_bool = self.emit_truthy(condition);
    self.builder.build_conditional_branch(cond_bool, body_bb, exit_bb)
        .expect("while conditional branch");

    self.builder.position_at_end(body_bb);
    self.compile_stmt(&while_stmt.body)?;
    self.builder.build_unconditional_branch(cond_bb).expect("loop back");

    self.builder.position_at_end(exit_bb);
    Ok(())
}
```

The pattern is always the same: create the blocks, emit a branch to the first one, switch the builder's insertion point into each block, emit its code, cap the block with a branch, and leave the builder positioned at the merge/exit block so the caller can continue emitting.

### Function Calls

Calling a Lox function through a closure pointer involves several steps: extract the `i64` payload, cast it back to a `LoxClosure*`, load the function pointer and environment pointer from the struct, check arity, marshal arguments, and fire an indirect call:

```rust
fn emit_closure_call(&mut self, callee: StructValue<'ctx>, args: &[StructValue<'ctx>], line: u32)
    -> anyhow::Result<StructValue<'ctx>>
{
    // Get the closure pointer from the LoxValue payload
    let closure_ptr_int = self.lox_value.extract_payload(&self.builder, callee);
    let closure_ptr = self.builder
        .build_int_to_ptr(closure_ptr_int, ptr_type, "closure_ptr")
        .expect("int to closure ptr");

    // Load fn_ptr and env_ptr from the closure struct
    let fn_ptr  = /* build_struct_gep + build_load for field 0 */;
    let env_ptr = /* build_struct_gep + build_load for field 3 */;

    // Build the call: first arg is env, then the Lox arguments
    let mut call_args: Vec<BasicMetadataValueEnum> = vec![env_ptr.into()];
    for arg in args { call_args.push((*arg).into()); }

    let result = self.builder
        .build_indirect_call(call_fn_type, fn_ptr, &call_args, "fn_call_result")
        .expect("build indirect call")
        .try_as_basic_value()
        .unwrap_basic()
        .into_struct_value();
    Ok(result)
}
```

The `build_indirect_call` instruction is what makes higher-order functions and closures work — instead of naming a specific function, you call through a pointer loaded at runtime.

---

## Native Compilation: From IR to Executable

The `--compile` flag uses the same IR generation pipeline as `--compile-llvm`, but instead of writing a `.ll` text file it takes the in-memory `Module` all the way to a native ELF executable. The code lives in `src/codegen/native.rs`.

Step one: initialise LLVM's native target. LLVM supports many architectures, but they are not all linked in by default. `Target::initialize_native` ensures the host architecture's backend is available:

```rust
Target::initialize_native(&InitializationConfig::default())
    .map_err(|msg| anyhow::anyhow!("initialize native target: {msg}"))?;
```

Step two: create a `TargetMachine` for the host, querying CPU name and features to allow LLVM to emit micro-architecture-specific instructions if available:

```rust
let triple   = TargetMachine::get_default_triple();
let target   = Target::from_triple(&triple)
    .map_err(|msg| anyhow::anyhow!("get target from triple: {msg}"))?;
let cpu      = TargetMachine::get_host_cpu_name();
let features = TargetMachine::get_host_cpu_features();

let machine = target.create_target_machine(
    &triple,
    cpu.to_str().expect("host CPU name is valid UTF-8"),
    features.to_str().expect("host CPU features are valid UTF-8"),
    OptimizationLevel::Default,
    RelocMode::PIC,
    CodeModel::Default,
).ok_or_else(|| anyhow::anyhow!("create target machine for {}", triple))?;
```

Step three: emit an object file from the module:

```rust
module.set_triple(&triple);
module.set_data_layout(&machine.get_target_data().get_data_layout());

machine
    .write_to_file(module, FileType::Object, obj_path)
    .map_err(|msg| anyhow::anyhow!("write object file: {msg}"))
    .context("emit object file")?;
```

Step four: link. The linker is `gcc` (or `$CC` if set), invoked with the emitted `.o` file plus the pre-built `lox_runtime.o` and `-lm` for the math library:

```rust
let cc = std::env::var("CC").unwrap_or_else(|_| "gcc".to_string());
let runtime_obj = env!("LOX_RUNTIME_OBJ");  // baked in at build time

Command::new(&cc)
    .arg(obj_path)
    .arg(runtime_obj)
    .arg("-o").arg(output_path)
    .arg("-lm")
    .output()
    .with_context(|| format!("run linker `{cc}`"))?;
```

The intermediate `.o` file is deleted after linking regardless of success. What remains is a self-contained native executable with no Cargo or Rust runtime dependency.

---

## Running the Output

vibe-lox gives you three ways to run compiled Lox:

```bash
# Compile to LLVM IR text and run via lli
cargo run -- --compile-llvm hello.lox
lli --extra-object runtime/lox_runtime.o hello.ll

# Or use the convenience wrapper (compiles if .ll doesn't exist)
./run-llvm.sh hello.lox

# Compile to a native executable
cargo run -- --compile hello.lox
./hello

# Custom output path
cargo run -- --compile -o build/hello hello.lox
```

The `run-llvm.sh` script is a thin wrapper: it checks whether a `.ll` file already exists (reusing it if so), compiles with `--compile-llvm` if not, then hands off to `lli`. It is useful for tight edit-run loops without recompiling the full Rust binary.

---

## Summing Up

The LLVM backend layers several concepts on top of each other:

1. Every Lox value is a `{ i8, i64 }` tagged union. The tag drives all runtime type decisions; the payload carries data as an integer, pointer, or bit-cast float.
2. A C runtime compiled at build time handles all heap allocation, global variable storage, string operations, and class/instance bookkeeping. The IR and the runtime share the same struct layout via the `LoxValue` typedef in `lox_runtime.h`.
3. A capture-analysis pre-pass distinguishes stack-allocated locals from heap-allocated cells, enabling correct closure semantics without a garbage collector.
4. The codegen walks the AST and emits LLVM IR using inkwell's builder API: basic blocks, conditional branches, indirect calls through closure pointers.
5. `TargetMachine::write_to_file` + a `gcc` link step turns that IR into a native ELF binary.

The resulting executable has no interpreter loop, no bytecode dispatch, and no Rust runtime. It is plain C-calling-convention machine code that calls a thin C runtime for the dynamic parts of the language.

Part 7 will close out the series with a look at what is still missing, what worked well, and what the next steps would be if this were a production language rather than a learning project.
