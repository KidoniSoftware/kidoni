---
title: Separating integration tests from unit tests
description:
date: 2020-12-30
tags:
  - blog
  - programming
  - testing
  - gradle
draft: true
---

One of the key aspects of agile software development --- the thing that
enables the agility of the coders --- is plentiful tests.
[Test-driven development](https://en.wikipedia.org/wiki/Test-driven_development)
is a hallmark of agile processes,
whichever one you follow. Plentiful tests provide the courage to
refactor, improving new or existing code as you work on it. As a
developer you should be able to run your tests as often as you like, and
only expect a delay of at most a few seconds, even for hundreds of
tests.

What is sometimes overlooked by people new to this practice is that
these should be **_unit_** tests. It is unfortunately all too common, no
matter how experienced a developer might be, not to understand what is
mean by "unit test". A unit test class is a very specific thing.

> A unit test class is a set of methods to validate _a_ **_single_** > _class-under-test._

A unit test class tests a single class. If that class uses other
classes, those need to be stubbed/mocked. This serves multiple purposes
including that you can write a class and test it without those other
classes being completed (or even started) yet. This is also what helps
to ensure the unit tests are fast, because possibly long chains of
dependent classes are not loaded and executed.

(There are plenty of good discussions and books about how to do mocks &
stubs. I won't get into that in this post.)

Unit tests should not do I/O either, since it's slow. This includes
reading/writing files, let alone sockets or databases or what have you.

And it certainly means that unit tests should not use frameworks like
Spring Framework, Hibernate, etc.

Tests that use I/O, databases, frameworks ... these are all tests that
are classified as integration tests. Having tests that need to
initialize something like Spring Framework/Spring Boot application
contexts or spin up an embedded database will obviously turn each test
class into one that takes something on the order of seconds --- for the
one test class itself. A single integration test class can easily take
as long as all the related unit tests combined. And often times with
tests using frameworks and databases, you need to reset much state
between each test method (since each test should be independent) adding
to the execution time.

As a developer interested in TDD and refactoring and wanting that quick
turnaround, it's desirable to segregate unit and integration (and
system) tests from each other. Setting up your build environment so that
you can run all the unit tests quickly and easily, while saving the
integration tests for perhaps when you need to get that next cup of
coffee, is a very nice thing.

At the same time, it's useful to do this segregation for the full CI/CD
pipeline because you can then also put in some constraints on execution
time so that builds don't hang and back everything up like a clogged
pipe.

What I'm going to show you here is a very quick and easy way to do this
using the [Gradle](https://gradle.org/)
[plugin](https://github.com/nebula-plugins/nebula-project-plugin),
one of many plugins in the "Nebula"
family contributed by Netflix. What this plugin will do is add a new
configuration to your Gradle build allowing you to put tests in
`src/integTest/java` rather than the standard `src/test/java`. It also adds an
`integrationTest` Gradle task.

`build.gradle`:

```groovy
plugins {
   id 'java'
   id 'nebula.integtest' version '7.0.9'
}
```

As you can see there is a new task:

```bash
$ gradle tasks
...
Verification tasks
------------------
check - Runs all checks.
integrationTest - Runs the integTest tests
test - Runs the unit tests.
```

Now just put your test classes in `src/integTest/java` (or `groovy` or
`scala` or whatever).

What I like to do as well is have a different file suffix, so that
anyone working in that integration test class knows it's an integration
test, without having to pay attention to the directory structure.
Personally I like `ITest` as the suffix.
If you leave `Test` or `Tests` on the end, you don't need to
change the configuration either, since those are the default suffixes.

Several other of the Nebula plugins I've found to be useful. Check them
all out at
[https://github.com/nebula-plugins](https://github.com/nebula-plugins).

One last thing, a shout out to a former colleague who first pointed me
at the Nebula plugins, Wladimir Schmidt. Thanks again.
