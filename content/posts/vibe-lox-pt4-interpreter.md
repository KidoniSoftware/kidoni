---
title: "Vibe Coding a Lox Compiler, Part 4: The Tree-Walk Interpreter"
description: How vibe-lox executes Lox programs by walking the AST — including the resolver, scoped environments, closures, and OOP.
date: 2026-02-20
tags:
  - blog
  - rust
  - programming
  - compiler
  - lox
  - interpreter
  - closures
  - oop
draft: false
---

{{% callout type="note" title="Written with AI" %}}
This post — and all the code behind it — was built with [Claude Code](https://claude.ai/claude-code). Read [Part 0](vibe-lox-pt0-preamble) for the full story of how this AI-assisted project came together.
{{% /callout %}}


Previously in this series we built the tokenizer ([Part 2](vibe-lox-pt2-tokenization)) and the recursive descent parser ([Part 3](vibe-lox-pt3-parsing)), turning raw source text into a typed AST. [Part 1](vibe-lox-pt1-introduction) gave the bird's-eye view of the whole pipeline. At this point, `vibe-lox` can take a `.lox` file, scan it into tokens, and parse those tokens into a tree of strongly-typed Rust structs — every node stamped with a unique `ExprId` for later use. Now we need to actually run the thing. This post covers the first execution backend: the tree-walk interpreter.

---

## Tree-Walk Interpretation

The simplest possible execution strategy is to walk the AST recursively and evaluate each node as you visit it. No compilation, no intermediate representation, no bytecode. Just a big `match` expression that dispatches on the node type.

A `BinaryExpr` evaluates its left operand, evaluates its right operand, and applies the operator. An `IfStmt` evaluates the condition and delegates to the appropriate branch. A `WhileStmt` loops until the condition is falsy. That's it. The interpreter's core `evaluate_expr` method in `src/interpreter/mod.rs` is exactly this:

```rust
fn evaluate_expr(&mut self, expr: &Expr) -> Result<Value, RuntimeError> {
    match expr {
        Expr::Literal(l) => Ok(match &l.value {
            LiteralValue::Number(n) => Value::Number(*n),
            LiteralValue::String(s) => Value::Str(s.clone()),
            LiteralValue::Bool(b) => Value::Bool(*b),
            LiteralValue::Nil => Value::Nil,
        }),
        Expr::Grouping(g) => self.evaluate_expr(&g.expression),
        Expr::Unary(u) => { /* ... */ }
        Expr::Binary(b) => self.evaluate_binary(b),
        Expr::Variable(v) => self.look_up_variable(&v.name, v.id, v.span),
        // ... and so on for every node type
    }
}
```

And `execute_stmt` mirrors it for statements:

```rust
Stmt::If(i) => {
    let condition = self.evaluate_expr(&i.condition)?;
    if condition.is_truthy() {
        self.execute_stmt(&i.then_branch)
    } else if let Some(ref else_branch) = i.else_branch {
        self.execute_stmt(else_branch)
    } else {
        Ok(())
    }
}
```

The code reads almost like a specification. Every branch of the grammar has a corresponding branch in the interpreter.

The appeal of this approach for a first backend is obvious: it is easy to understand and easy to debug. When something goes wrong you can set a breakpoint in the relevant arm of the `match` and inspect exactly what the interpreter sees. The downside is performance: you are re-traversing the tree on every execution, and Rust's enum dispatch adds overhead compared to a tightly-packed bytecode loop. But for correctness and clarity it is hard to beat. vibe-lox also has a bytecode VM backend (Part 5) and an LLVM native compiler (Part 6) for when performance matters.

---

## The Resolver: Static Analysis Before Runtime

Before the interpreter runs a single statement, vibe-lox runs a separate *resolver* pass over the AST. The resolver is a form of lightweight static analysis — think of it as a stripped-down type checker that only cares about variable scoping.

The key insight is that Lox uses *lexical scoping*: a variable reference always refers to the binding that was in scope at the point in the source where the reference appears, regardless of what happens at runtime. That means the scope depth of every variable reference can be calculated statically, before execution. The resolver does exactly that.

The `Resolver` struct in `src/interpreter/resolver.rs` maintains a stack of scopes — one `HashMap<String, bool>` per active block — and a `locals` map keyed by `ExprId`:

```rust
pub struct Resolver {
    scopes: Vec<HashMap<String, bool>>,
    locals: HashMap<ExprId, usize>,
    current_function: FunctionType,
    current_class: ClassType,
    errors: Vec<CompileError>,
}
```

The `bool` in each scope map is the "defined" flag. A variable is first *declared* (inserted as `false`) and then *defined* (flipped to `true`) after its initializer is evaluated. That two-phase dance is what lets the resolver catch `var x = x;` at "compile time":

```rust
fn declare(&mut self, name: &str, span: Span) {
    if let Some(scope) = self.scopes.last_mut() {
        scope.insert(name.to_string(), false); // declared, not yet defined
    }
}

fn define(&mut self, name: &str) {
    if let Some(scope) = self.scopes.last_mut() {
        scope.insert(name.to_string(), true); // now safe to read
    }
}
```

And in `resolve_expr`, a variable access while the variable is still `false` is an error:

```rust
Expr::Variable(v) => {
    if let Some(scope) = self.scopes.last()
        && scope.get(&v.name) == Some(&false)
    {
        self.errors.push(CompileError::resolve(
            "can't read local variable in its own initializer",
            v.span.offset, v.span.len,
        ));
    }
    self.resolve_local(v.id, &v.name);
}
```

The `resolve_local` method walks the scope stack from innermost to outermost and records how many levels up the binding lives:

```rust
fn resolve_local(&mut self, id: ExprId, name: &str) {
    for (i, scope) in self.scopes.iter().rev().enumerate() {
        if scope.contains_key(name) {
            self.locals.insert(id, i);
            return;
        }
    }
    // Not found in any local scope: assume global
}
```

The resolver also catches other semantic errors that belong logically at "compile time": `return` outside a function, `this` outside a class, `super` in a class with no superclass, duplicate variable declarations in the same block, and a class trying to inherit from itself. All of these are caught before the interpreter runs a single line.

When the resolver finishes it returns the `locals` map — a `HashMap<ExprId, usize>` that maps every local variable reference to its scope depth. The interpreter receives this map and uses it to look up variables in O(1) during execution.

---

## The Environment

Variables live in an `Environment`. The struct is deliberately simple:

```rust
pub struct Environment {
    values: HashMap<String, Value>,
    enclosing: Option<Rc<RefCell<Environment>>>,
}
```

Each environment holds a map of names to values and an optional pointer to an enclosing environment. The chain of enclosing environments forms the scope chain: local → enclosing function → … → global.

The resolver pre-computed how many links up each variable lives. At runtime, `get_at` simply hops that many times and looks up the name:

```rust
pub fn get_at(&self, distance: usize, name: &str) -> Option<Value> {
    if distance == 0 {
        self.values.get(name).cloned()
    } else {
        self.enclosing
            .as_ref()
            .expect("resolver guarantees valid distance")
            .borrow()
            .get_at(distance - 1, name)
    }
}
```

The `expect` here is intentional — if the resolver did its job, this can never be `None`. Same story for `assign_at`:

```rust
pub fn assign_at(&mut self, distance: usize, name: &str, value: Value) {
    if distance == 0 {
        self.values.insert(name.to_string(), value);
    } else {
        self.enclosing
            .as_ref()
            .expect("resolver guarantees valid distance")
            .borrow_mut()
            .assign_at(distance - 1, name, value);
    }
}
```

The `Rc<RefCell<Environment>>` wrapping deserves a word. `Rc` gives shared ownership — multiple places can hold a reference to the same environment. `RefCell` gives interior mutability — you can mutate through a shared reference, checked at runtime instead of compile time. Together they let multiple closures close over the same variables and share mutations. Without this, closures simply could not work. We will see exactly why in the closures section.

---

## Values

Everything in Lox is a value. The `Value` enum in `src/interpreter/value.rs` covers the complete set:

```rust
#[derive(Clone, Debug)]
pub enum Value {
    Number(f64),
    Str(String),
    Bool(bool),
    Nil,
    Function(Callable),
    Class(Rc<LoxClass>),
    Instance(Rc<RefCell<LoxInstance>>),
}
```

A few things worth noting. All Lox numbers are `f64` — there is no integer type. Classes are wrapped in `Rc<LoxClass>` (shared ownership, no mutation needed after construction). Instances are `Rc<RefCell<LoxInstance>>` because they need both shared ownership (multiple variables can reference the same object) and mutability (fields can be set after creation).

Lox's truthiness rules are simple and intentional: `nil` and `false` are falsy; everything else — including `0` and the empty string — is truthy:

```rust
pub fn is_truthy(&self) -> bool {
    match self {
        Self::Nil => false,
        Self::Bool(b) => *b,
        _ => true,
    }
}
```

Display formatting has one interesting quirk to match the Lox spec: numbers that happen to be exact integers print without a decimal point:

```rust
Self::Number(n) => {
    if n.fract() == 0.0 {
        write!(f, "{}", *n as i64)
    } else {
        write!(f, "{n}")
    }
}
```

So `print 42.0;` outputs `42`, not `42`. This is a deliberate Lox behaviour that the test suite enforces.

---

## Closures

This is where things get interesting. A closure is a function that captures its lexical environment — the variables that were in scope where the function was *defined*, not where it is *called*. Getting closures right is what separates a toy interpreter from a real one.

`LoxFunction` in `src/interpreter/callable.rs` captures its definition environment explicitly:

```rust
#[derive(Debug, Clone)]
pub struct LoxFunction {
    pub declaration: Function,
    pub closure: Rc<RefCell<Environment>>,
    pub is_initializer: bool,
}
```

When a function is declared, `Rc::clone(&self.environment)` snapshots a shared pointer to the current environment at the point of declaration. When the function is *called*, the interpreter creates a new child environment whose parent is that captured closure — not the caller's environment:

```rust
let env = Rc::new(RefCell::new(Environment::with_enclosing(
    Rc::clone(&user_fn.closure), // parent is the closure, not the call site
)));
for (param, arg) in user_fn.declaration.params.iter().zip(args) {
    env.borrow_mut().define(param.clone(), arg);
}
let result = self.execute_block(&user_fn.declaration.body, env);
```

Here is why that matters. Consider this Lox program:

```lox
fun makeCounter() {
  var count = 0;
  fun increment() {
    count = count + 1;
    return count;
  }
  return increment;
}
var counter = makeCounter();
print counter(); // 1
print counter(); // 2
```

Let us trace through it:

1. `makeCounter()` is called. A new environment `E1` is created. `count` is defined in `E1` as `0`.
2. `increment` is declared. It captures `E1` as its closure.
3. `makeCounter` returns `increment`. At this point `makeCounter`'s activation frame is gone, but `E1` is *still alive* because `increment`'s `closure` field holds an `Rc` pointing to it.
4. The first `counter()` call creates a new environment `E2` whose parent is `E1`. When `count = count + 1` executes, the resolver says `count` is one scope level up, so `assign_at(1, "count", ...)` walks up to `E1` and updates it to `1`. Return value: `1`.
5. The second `counter()` call creates yet another `E3`, again parented to `E1`. The same `count` in `E1` is now `1`, and gets bumped to `2`. Return value: `2`.

Each call gets its own fresh local environment, but they all share the *same* `E1` through the `Rc`. That shared mutable state — impossible to express in Rust without `Rc<RefCell<_>>` — is precisely what gives closures their power.

---

## OOP: Classes, this, super

`LoxClass` holds a name, an optional superclass, and a map of methods:

```rust
pub struct LoxClass {
    pub name: String,
    pub superclass: Option<Rc<LoxClass>>,
    pub methods: HashMap<String, Callable>,
}
```

`LoxInstance` holds a reference to its class and a field map:

```rust
pub struct LoxInstance {
    pub class: Rc<LoxClass>,
    pub fields: HashMap<String, Value>,
}
```

Fields in Lox need no declaration — they spring into existence on first assignment. Method lookup checks fields first (a field can shadow a method), then walks up the class hierarchy:

```rust
pub fn find_method(&self, name: &str) -> Option<Callable> {
    self.methods
        .get(name)
        .cloned()
        .or_else(|| self.superclass.as_ref().and_then(|sc| sc.find_method(name)))
}
```

`this` is handled by `bind`. When a method is retrieved through an instance, `bind` creates a small synthetic environment whose parent is the method's closure, with `"this"` bound to the current instance:

```rust
pub fn bind(&self, instance: Rc<RefCell<LoxInstance>>) -> Self {
    match self {
        Self::User(u) => {
            let env = Rc::new(RefCell::new(
                Environment::with_enclosing(Rc::clone(&u.closure))
            ));
            env.borrow_mut()
                .define("this".to_string(), Value::Instance(instance));
            Self::User(LoxFunction {
                declaration: u.declaration.clone(),
                closure: env,
                is_initializer: u.is_initializer,
            })
        }
        // ...
    }
}
```

When `this` appears inside the method body, the resolver pre-computed its depth. `get_at` walks up that many links and finds the bound instance.

`super.method()` is similar but one step more indirect. The resolver lays out the environment chain so that `"super"` lives exactly one scope level above `"this"`. At runtime, the interpreter retrieves the superclass at the pre-computed depth, looks up the method by name, and calls `bind` to attach the current `this` — so even though the method body comes from the superclass, `this` still refers to the concrete instance.

```rust
Expr::Super(s) => {
    let distance = *self.locals.get(&s.id)
        .expect("resolver should have resolved 'super'");
    let superclass = self.environment.borrow()
        .get_at(distance, "super")
        .expect("resolver guarantees 'super' exists");
    let object = self.environment.borrow()
        .get_at(distance - 1, "this")
        .expect("resolver guarantees 'this' exists");

    if let (Value::Class(sc), Value::Instance(inst)) = (superclass, object) {
        let method = sc.find_method(&s.method).ok_or_else(|| { /* ... */ })?;
        Ok(Value::Function(method.bind(inst)))
    } else { /* ... */ }
}
```

The interplay of `Rc`, `RefCell`, and pre-computed resolver depths makes the OOP machinery surprisingly lean — there is no dynamic dispatch table and no vtable pointer on instances.

---

## Return as a Result

A `return` statement in Lox needs to unwind the entire call stack and deliver a value back to the call site. The obvious approach — threading a `(bool, Value)` return flag through every stack frame — is tedious and error-prone.

vibe-lox does something more idiomatic: it raises a special `Err` variant.

```rust
#[derive(Error, Debug)]
pub enum RuntimeError {
    #[error("Error: {message}")]
    Error { message: String, span: Option<Span>, backtrace: Vec<StackFrame> },

    #[error("return")]
    Return { value: Value },
}
```

When `execute_stmt` hits a `Stmt::Return`, it evaluates the expression and immediately propagates it as an error:

```rust
Stmt::Return(r) => {
    let value = match &r.value {
        Some(val) => self.evaluate_expr(val)?,
        None => Value::Nil,
    };
    Err(RuntimeError::Return { value })
}
```

This `Err` propagates up through `?` in every method between the `return` statement and the function call site. The `call_function` method catches it:

```rust
Err(RuntimeError::Return { value }) => {
    self.call_stack.pop();
    Ok(value) // convert the "error" into a normal return value
}
```

Everything else is a genuine error and propagates further. The `is_return()` helper on `RuntimeError` lets the REPL distinguish between a propagated return value and an actual runtime error, so a top-level `return` does not print a spurious error message.

Using `Result` for control flow feels unconventional, but it is exactly the right tool here: early exit from an arbitrary depth of recursive calls, carrying a payload, with zero boilerplate at the intermediate layers. Rust's `?` operator does all the heavy lifting.

---

## Putting It Together

The full execution pipeline for a `.lox` file is:

1. **Scan** — `scanner::scan(source)` produces a `Vec<Token>`
2. **Parse** — `Parser::new(tokens).parse()` produces a `Program` (typed AST)
3. **Resolve** — `Resolver::new().resolve(&program)` produces a `HashMap<ExprId, usize>`
4. **Interpret** — `interpreter.interpret(&program, locals)` executes the program

The resolver's output is a compact side-table that augments the AST without mutating it. The interpreter carries this table in `self.locals` and consults it for every variable access and assignment, dispatching to `get_at` or `assign_at` with the pre-computed depth.

The tree-walk interpreter is not the fastest execution strategy — that title goes to the bytecode VM in Part 5 and the LLVM native backend in Part 6. But it is the clearest: every language feature maps directly to a handful of lines of Rust, and the entire execution model fits in your head. That clarity is what makes it the right place to start.

Next up: we compile Lox to bytecode and build a register-free stack VM to run it.
