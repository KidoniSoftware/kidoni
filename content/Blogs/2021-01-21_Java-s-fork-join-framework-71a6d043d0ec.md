---
title: 
description: 
date: 
tags:
  - blog
draft: true
---

<div>

# Java's fork-join framework {#javas-fork-join-framework .p-name}

</div>

::: {.section .p-summary field="subtitle"}
Since Java 8 includes set of classes implementing a fork-join pattern.
This is an approach to decomposing work into multiple tasks that...
:::

::: {.section .e-content field="body"}
::: {#a5cf .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Java's fork-join framework {#871a .graf .graf--h3 .graf--leading .graf--title name="871a"}

<figure id="1f33" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*iHt7BmXvIWr_4Aqc"
class="graf-image" data-image-id="0*iHt7BmXvIWr_4Aqc" data-width="4000"
data-height="2666" data-unsplash-photo-id="Yvaej69Nuyw"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@drmakete?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@drmakete?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">drmakete lab</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

Since Java 7, the JDK includes a set of classes implementing a fork-join
pattern. This is an approach decomposing work into multiple tasks that
can be executed in parallel. Java provides `ForkJoinPool`{.markup--code
.markup--p-code} and `ForkJoinTask`{.markup--code .markup--p-code} as
the two primary classes implementing the approach. This post will cover
an example of using these, by converting a Mergesort implementation from
a recursive implementation to one using fork-join.

Mergesort is a classic divide-and-conquer approach to sorting. The data
to be sorted are split into two halves, and those halves each are split
into two until the data can no longer be split. Then the resulting
arrays are merged and sorted.

This can be visualized using this diagram from [Wikipedia's Mergesort
page](https://en.wikipedia.org/wiki/Merge_sort){.markup--anchor
.markup--p-anchor data-href="https://en.wikipedia.org/wiki/Merge_sort"
rel="noopener" target="_blank"}.

::: {#d328 .graf .graf--mixtapeEmbed .graf-after--p}
[**File:Merge sort algorithm diagram.svg**\
*From Wikimedia Commons, the free media
repository*commons.wikimedia.org](https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg#/media/File:Merge_sort_algorithm_diagram.svg "https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg#/media/File:Merge_sort_algorithm_diagram.svg"){.markup--anchor
.markup--mixtapeEmbed-anchor
data-href="https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg#/media/File:Merge_sort_algorithm_diagram.svg"}[](https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg#/media/File:Merge_sort_algorithm_diagram.svg){.js-mixtapeImage
.mixtapeImage .u-ignoreBlock media-id="0d0208cb80c6b6e6ec766dee0391846e"
thumbnail-img-id="0*Fl2KC33xoFM7bY8T"
style="background-image: url(https://cdn-images-1.medium.com/fit/c/160/160/0*Fl2KC33xoFM7bY8T);"}
:::

A simple recursive implementation in Java is

<figure id="8bcd" class="graf graf--figure graf--iframe graf-after--p">

</figure>

As you can see the input `array`{.markup--code .markup--p-code} is split
in half, with each half (`left`{.markup--code .markup--p-code} and
`right`{.markup--code .markup--p-code} ) then recursively mergesorted.
The recursion stops when the array size is 1, and the left and right
parts are merged into the original array in sorted order. The
`merge()`{.markup--code .markup--p-code} is implemented like this

<figure id="bdf0" class="graf graf--figure graf--iframe graf-after--p">

</figure>

> Disclaimer: I do not in any way claim that this is the best way to
> implement the Mergesort or the merge part of the algorithm! But it is
> functionally correct.

So there you have an example of a divide-and-conquer recursive approach
to implementing Mergesort. From this it should be fairly obvious where
we'd plug in the fork-join ... just use it instead of recursion.

### Java ForkJoinPool and ForkJoinTask {#918e .graf .graf--h3 .graf-after--p name="918e"}

You can take a look at the generic tutorial from Oracle
[here](https://docs.oracle.com/javase/tutorial/essential/concurrency/forkjoin.html){.markup--anchor
.markup--p-anchor
data-href="https://docs.oracle.com/javase/tutorial/essential/concurrency/forkjoin.html"
rel="noopener" target="_blank"}.

The general recommended approach when using the fork-join framework is
to apply it to a problem only after some threshold, since the overhead
of the fork-join framework would be too costly for simpler cases. For
example, with the Mergesort, sorting smaller arrays would be faster just
doing a direct implementation as shown above. So in this example I have
(arbitrarily) set the cutoff at an array size of 1000.

<figure id="3192" class="graf graf--figure graf--iframe graf-after--p">

</figure>

If the array size is smaller than 1000 then just use the recursive
implementation. Otherwise, use the fork-join framework.

The `ForkJoinPool`{.markup--code .markup--p-code} is similar to other
thread pools in Java. You can create your own pools, or you can use a
shared common pool, via the convenience method
`ForkJoinPool.commonPool()`{.markup--code .markup--p-code}.
`ForkJoinPool`{.markup--code .markup--p-code} has several different ways
to submit tasks. You can review the
[Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ForkJoinPool.html){.markup--anchor
.markup--p-anchor
data-href="https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ForkJoinPool.html"
rel="noopener" target="_blank"}. The basic approach is to call
`invoke()`{.markup--code .markup--p-code} passing an implementation of
`ForkJoinTask`{.markup--code .markup--p-code}. You could directly extend
`ForkJoinTask`{.markup--code .markup--p-code}, but the JDK provides two
implementations that should suffice for many use cases. These are
`RecursiveTask`{.markup--code .markup--p-code} and
`RecursiveAction`{.markup--code .markup--p-code}, which return a result
or not, respectively --- essentially `ForkJoinTask<V>`{.markup--code
.markup--p-code} and `ForkJoinTask<Void>`{.markup--code
.markup--p-code}.

Since the Mergesort is an "in-place" sort there is no return value, so
here we use `RecursiveAction`{.markup--code .markup--p-code} in the
implementation. I have created a class called
`ForkJoinMerge`{.markup--code .markup--p-code} that extends
`RecursiveAction`{.markup--code .markup--p-code}.

<figure id="0345" class="graf graf--figure graf--iframe graf-after--p">

</figure>

With the `ForkJoinTask`{.markup--code .markup--p-code} you implement the
`compute()`{.markup--code .markup--p-code} method to do your work,
similar how with regular threading you implement
`Runnable.run()`{.markup--code .markup--p-code} or
`Callable.call()`{.markup--code .markup--p-code}.

The `compute()`{.markup--code .markup--p-code} method of my
`ForkJoinMerge`{.markup--code .markup--p-code} does exactly the same
thing as the recursive Mergesort but creates new instances of
`ForkJoinMerge`{.markup--code .markup--p-code} for the left and right
halves. Then it uses the same `merge()`{.markup--code .markup--p-code}
implementation shown earlier.

<figure id="0a21" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Once the new `ForkJoinMerge`{.markup--code .markup--p-code} instances
have been created, their `fork()`{.markup--code .markup--p-code} method
is called. This causes the tasks to run in the same
`ForkJoinPool`{.markup--code .markup--p-code} as the current task. As
with typical thread execution, to await the completion of the thread,
you call `join()`{.markup--code .markup--p-code}. Finally, as with the
original algorithm, you take the left and right arrays and merge them.

Hopefully this gives a good basic introduction to the Java fork-join
framework. You can look at more detailed and perhaps useful uses of it
by looking at the JDK itself --- `ForkJoinTask`{.markup--code
.markup--p-code} is used in the Java stream operator implementations for
example. Or check out the `Sorter`{.markup--code .markup--p-code} class
in `DualPivotQuicksort`{.markup--code .markup--p-code}. The
`Sorter`{.markup--code .markup--p-code} class is a
`ForkJoinTask`{.markup--code .markup--p-code} and
`DualPivotQuicksort`{.markup--code .markup--p-code} is used if you call
`Arrays.parallelSort()`{.markup--code .markup--p-code}.
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [January 21, 2021](https://medium.com/p/71a6d043d0ec).

[Canonical
link](https://medium.com/@raysuliteanu/javas-fork-join-framework-71a6d043d0ec){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
