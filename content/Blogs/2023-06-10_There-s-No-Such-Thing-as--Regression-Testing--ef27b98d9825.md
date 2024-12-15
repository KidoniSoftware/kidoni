---
title: 
description: 
date: 
tags:
  - blog
draft: true
---

<div>

# There's No Such Thing as 'Regression Testing' {#theres-no-such-thing-as-regression-testing .p-name}

</div>

::: {.section .p-summary field="subtitle"}
How would you define "regression testing"?
:::

::: {.section .e-content field="body"}
::: {#b56d .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### There's No Such Thing as 'Regression Testing' {#38fb .graf .graf--h3 .graf--leading .graf--title name="38fb"}

<figure id="5c3c" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*MvcsOTzi4Lhudi6d"
class="graf-image" data-image-id="0*MvcsOTzi4Lhudi6d" data-width="5042"
data-height="3456" data-unsplash-photo-id="elHKkgom1VU"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@sigmund?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@sigmund?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Sigmund</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

How would you define "regression testing"? According to
[Wikipedia](https://en.m.wikipedia.org/wiki/Regression_testing){.markup--anchor
.markup--p-anchor
data-href="https://en.m.wikipedia.org/wiki/Regression_testing"
rel="noopener" target="_blank"},

> Regression testing (rarely non-regression
> testing\[[1](https://en.m.wikipedia.org/wiki/Regression_testing#cite_note-1){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://en.m.wikipedia.org/wiki/Regression_testing#cite_note-1"
> rel="noopener" target="_blank"}\]) is re-running
> [functional](https://en.m.wikipedia.org/wiki/Functional_testing){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://en.m.wikipedia.org/wiki/Functional_testing"
> rel="noopener" target="_blank"} and [non-functional
> tests](https://en.m.wikipedia.org/wiki/Non-functional_testing){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://en.m.wikipedia.org/wiki/Non-functional_testing"
> rel="noopener" target="_blank"} to ensure that previously developed
> and tested software still performs after a change.

In the modern age of test automation and continuous integration, tests
are run (or should be) automatically by the build system. Whether
testing functional or non-functional features, there really are only
three categories of tests to run:

-   [Unit tests]{#b1f3}
-   [Integration tests]{#a52c}
-   [System tests]{#22d8}

Let's discuss each in turn.

### Unit Tests {#7018 .graf .graf--h3 .graf-after--p name="7018"}

Unit tests test the smallest unit of software, which varies by language
e.g. in object-oriented languages typically the "unit" is a
[class](https://en.wikipedia.org/wiki/Class_%28computer_programming%29){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Class_(computer_programming)"
rel="noopener" target="_blank"}. (While the unit varies by language
and/or paradigm, for clarity I will just refer herein to "class" as the
unit.) Unit tests test this class **in isolation**. That is, *the unit
tests must only interact with the class under test*. There should be no
interaction with other classes you've written, should do no I/O (read
files, make network calls, etc.), should not interact with databases and
should not use third-party frameworks (e.g. no loading of the Java
[Spring Framework](https://spring.io/){.markup--anchor .markup--p-anchor
data-href="https://spring.io/" rel="noopener" target="_blank"}
`ApplicationContext`{.markup--code .markup--p-code}). *The intent is for
unit tests to be small and fast, with hundreds or thousands able to run
in a few seconds or minutes*. If the class under test calls other
classes, these should be
[mocked](https://en.wikipedia.org/wiki/Mock_object){.markup--anchor
.markup--p-anchor data-href="https://en.wikipedia.org/wiki/Mock_object"
rel="noopener" target="_blank"} using test mocking frameworks (e.g. in
Java land something like
[EasyMock](https://easymock.org/){.markup--anchor .markup--p-anchor
data-href="https://easymock.org/" rel="noopener" target="_blank"} or
[Mockito](https://site.mockito.org/){.markup--anchor .markup--p-anchor
data-href="https://site.mockito.org/" rel="noopener" target="_blank"}).

If the class under test does I/O but you can't do I/O in unit tests,
what do you do? Well, for example, in Java let's say the class under
test reads from an `InputStream`{.markup--code .markup--p-code}, with
the production behavior to read data from a file. You could mock this
`InputStream`{.markup--code .markup--p-code}, or you could provide a
`ByteArrayInputStream `{.markup--code .markup--p-code}which could be
initialized from a byte array created by calling
`String.getBytes()`{.markup--code .markup--p-code}. Other similar
approaches exist, regardless of language.

> Note one positive side effect of needing to use mocks or approaches
> like using a `ByteArrayInputStream`{.markup--code
> .markup--blockquote-code}as described is that it can improve the
> design of your code, making it more
> [SOLID](https://en.wikipedia.org/wiki/SOLID){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://en.wikipedia.org/wiki/SOLID" rel="noopener"
> target="_blank"}. Combined with [test-driven
> development](https://en.wikipedia.org/wiki/Test-driven_development){.markup--anchor
> .markup--blockquote-anchor
> data-href="https://en.wikipedia.org/wiki/Test-driven_development"
> rel="noopener" target="_blank"} (TDD) it helps developers think about
> the testability of code (design for test), something that is generally
> lacking.

### **Integration Tests** {#2ba8 .graf .graf--h3 .graf-after--blockquote name="2ba8"}

As the name implies, integration tests are for testing several classes
together. These are still relatively small and focused tests, but
integration tests can do I/O, read from databases (*though consider
using in-memory embedded databases or a containerized solution like*
[*Testcontainers*](https://testcontainers.com/){.markup--anchor
.markup--p-anchor data-href="https://testcontainers.com/" rel="noopener"
target="_blank"} *in Java*), use frameworks like Spring Framework,
[Boost](https://www.boost.org/){.markup--anchor .markup--p-anchor
data-href="https://www.boost.org/" rel="noopener" target="_blank"},
[Tokio](https://tokio.rs/){.markup--anchor .markup--p-anchor
data-href="https://tokio.rs/" rel="noopener" target="_blank"}. You may
still need to mock certain things (or again use a container solution)
because you will **not** have a fully deployed system when running
integration tests. So for example you might use Spring's
[MockMvc](https://docs.spring.io/spring-framework/reference/testing/spring-mvc-test-framework.html){.markup--anchor
.markup--p-anchor
data-href="https://docs.spring.io/spring-framework/reference/testing/spring-mvc-test-framework.html"
rel="noopener" target="_blank"} or similar test helpers. Integration
tests will obviously take longer as a result, since even
embedded/containerized databases will take time to initialize. Even so,
hundreds of integration tests should be able to run in 10--15 minutes.

Unit tests, and most or all integration tests, are considered ["white
box"
testing](https://en.m.wikipedia.org/wiki/White-box_testing){.markup--anchor
.markup--p-anchor
data-href="https://en.m.wikipedia.org/wiki/White-box_testing"
rel="noopener" target="_blank"}, where you're writing tests about with
knowledge of the internals, often using internal, non-public APIs.

### **System Tests** {#a1f1 .graf .graf--h3 .graf-after--p name="a1f1"}

System tests execute against a fully deployed service or services. These
are ["black box"
tests](https://en.m.wikipedia.org/wiki/Black-box_testing){.markup--anchor
.markup--p-anchor
data-href="https://en.m.wikipedia.org/wiki/Black-box_testing"
rel="noopener" target="_blank"}, testing the functionality that's
exposed to users (whether human or computer). System tests are written
against the APIs and UIs. These tests will take the longest to execute,
because they require a deployed set of services and their
dependencies --- the service(s) you're testing and the services they
interact with including databases, messages queues, etc. and most
importantly in the same or very similar environment as the software will
run in when in production. So if the software is deployed to AWS, then
system tests need to run against the software in AWS. Setting up and
tearing down these tests environments takes time (hopefully already
automated using
[IaC](https://en.wikipedia.org/wiki/Infrastructure_as_code){.markup--anchor
.markup--p-anchor
data-href="https://en.wikipedia.org/wiki/Infrastructure_as_code"
rel="noopener" target="_blank"} which itself can and should be
[automatically tested](https://terratest.gruntwork.io/){.markup--anchor
.markup--p-anchor data-href="https://terratest.gruntwork.io/"
rel="noopener" target="_blank"}). Depending on the tests, the full set
of system tests could take hours or even days, for stress or performance
testing for example, which is a good segue.

You may be asking, what about performance tests, or stress tests, or
smoke tests or user acceptance tests (UATs)? *Those are all just
different types of system tests*. Performance tests, stress tests, UATs,
these all go against the deployed system. (I'm obviously not including
micro-benchmark performance tests. If you have any, these are typically
unit tests or integration tests in any case, very "white box" focused
and leverage frameworks like
[JMH](https://github.com/openjdk/jmh){.markup--anchor .markup--p-anchor
data-href="https://github.com/openjdk/jmh" rel="noopener"
target="_blank"}.)

### **Test Automation** {#78b7 .graf .graf--h3 .graf-after--p name="78b7"}

All of these tests should be run automatically. The CI pipeline should
automatically run all these tests, at different points in the
development process, but automatically regardless. For example, unit
tests run on every commit, and if they all pass, integration tests run,
and if they pass, system tests could be (scheduled to) run. Or system
tests just run nightly or on some other cadence (e.g. performance tests
perhaps run weekly). And you can break up the system tests into groups
(functional, performance, load, stress) and maybe further break up tests
into API and UI subsets. Each subset can be scheduled to run at
different times based on things like execution time and point in the
lifecycle.

One thing you can also do with test automation in your CI environment is
help enforce these different classes --- unit, integration and
system --- by putting timeouts into the pipeline. For example, you can
establish a policy that all integration tests must complete within 15
minutes and kill that job if the timeout is exceeded, in case someone
mistakenly creates a test that doesn't follow the standard you've
established (or did so erroneously).

Regardless, *all these tests are running all the time*. They're running
against new or modified code **and all the existing code**. Existing
code could also be called *"previously developed"* code.

### **Regression Testing?** {#8449 .graf .graf--h3 .graf-after--p name="8449"}

Wait, didn't the definition of "regression testing" say that it was
testing to ensure that "previously developed" code has not been broken?

Yes indeed.

Hence, there is no such thing as regression testing, since all tests run
all the time against new and existing --- or previously
developed --- code, and will find both new bugs *and any regressions*.

*"Quod erat demonstrandum."* (🙂)
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [June 10, 2023](https://medium.com/p/ef27b98d9825).

[Canonical
link](https://medium.com/@raysuliteanu/theres-no-such-thing-as-regression-testing-ef27b98d9825){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
