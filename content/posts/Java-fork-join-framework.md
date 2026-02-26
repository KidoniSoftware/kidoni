---
title: Java's fork-join framework
description:
date: 2021-01-21
tags:
  - blog
  - java
  - programming
  - multithreading
  - mergesort
draft: false
---

Since Java 7, the JDK includes a set of classes implementing a fork-join
pattern. This is an approach decomposing work into multiple tasks that
can be executed in parallel. Java provides `ForkJoinPool` and `ForkJoinTask` as
the two primary classes implementing the approach. This post will cover
an example of using these, by converting a Mergesort implementation from
a recursive implementation to one using fork-join.

Mergesort is a classic divide-and-conquer approach to sorting. The data
to be sorted are split into two halves, and those halves each are split
into two until the data can no longer be split. Then the resulting
arrays are merged and sorted.

This can be visualized using this diagram from [Wikipedia's Mergesort
page](https://en.wikipedia.org/wiki/Merge_sort).

A simple recursive implementation in Java is

```java
    public static void mergeSort(int[] array, int size) {
        if (size > 1) {
            int mid = size / 2;
            int[] left = new int[mid];
            int[] right = new int[array.length - mid];

            arraycopy(array, 0, left, 0, left.length);
            arraycopy(array, mid, right, 0, array.length - mid);

            mergeSort(left, left.length);
            mergeSort(right, right.length);

            merge(array, left, right);
        }
    }
```

As you can see the input `array` is split in half, with each half (`left` and
`right` ) then recursively mergesorted. The recursion stops when the array size
is 1, and the left and right parts are merged into the original array in sorted
order. The `merge()` is implemented like this

```java
    private static void merge(final int[] dest, final int[] left, final int[] right) {
        int destIdx = 0, leftIdx = 0, rightIdx = 0;
        while (leftIdx < left.length && rightIdx < right.length) {
            if (left[leftIdx] < right[rightIdx]) {
                dest[destIdx++] = left[leftIdx++];
            }
            else {
                dest[destIdx++] = right[rightIdx++];
            }
        }

        for (int i = leftIdx; i < left.length; i++) {
            dest[destIdx++] = left[i];
        }

        for (int i = rightIdx; i < right.length; i++) {
            dest[destIdx++] = right[i];
        }
    }
```

> Disclaimer: I do not in any way claim that this is the best way to
> implement the Mergesort or the merge part of the algorithm! But it is
> functionally correct.

So there you have an example of a divide-and-conquer recursive approach
to implementing Mergesort. From this it should be fairly obvious where
we'd plug in the fork-join ... just use it instead of recursion.

## Java ForkJoinPool and ForkJoinTask

You can take a look at the generic tutorial from Oracle
[here](https://docs.oracle.com/javase/tutorial/essential/concurrency/forkjoin.html).

The general recommended approach when using the fork-join framework is
to apply it to a problem only after some threshold, since the overhead
of the fork-join framework would be too costly for simpler cases. For
example, with the Mergesort, sorting smaller arrays would be faster just
doing a direct implementation as shown above. So in this example I have
(arbitrarily) set the cutoff at an array size of 1000.

```java
    public static void forkJoinMergesort(int[] array, int size) {
        if (size < 1000) {
            mergeSort(array, size);
        }
        else {
            ForkJoinPool.commonPool().invoke(new ForkJoinMerge(array, size));
        }

    }
```

If the array size is smaller than 1000 then just use the recursive
implementation. Otherwise, use the fork-join framework.

The `ForkJoinPool` is similar to other thread pools in Java. You can create your
own pools, or you can use a shared common pool, via the convenience method
`ForkJoinPool.commonPool()`. `ForkJoinPool` has several different ways
to submit tasks. You can review the [Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ForkJoinPool.html).
The basic approach is to call `invoke()` passing an implementation of
`ForkJoinTask`. You could directly extend `ForkJoinTask`, but the JDK provides
two implementations that should suffice for many use cases. These are
`RecursiveTask` and `RecursiveAction`, which return a result or not,
respectively --- essentially `ForkJoinTask<V>` and `ForkJoinTask<Void>`.

Since the Mergesort is an "in-place" sort there is no return value, so
here we use `RecursiveAction` in the implementation. I have created a class
called `ForkJoinMerge` that extends `RecursiveAction`.

```java
    private static class ForkJoinMerge extends RecursiveAction {

        private final int[] array;
        private final int size;

        public ForkJoinMerge(final int[] array, final int size) {
            this.array = array;
            this.size = size;
        }
```

With the `ForkJoinTask` you implement the `compute()` method to do your work,
similar how with regular threading you implement `Runnable.run()` or
`Callable.call()`.

The `compute()` method of my `ForkJoinMerge` does exactly the same thing as the
recursive Mergesort but creates new instances of `ForkJoinMerge` for the left
and right halves. Then it uses the same `merge()` implementation shown earlier.

```java
        @Override
        protected void compute() {
            if (size > 1) {
                int mid = size / 2;
                int[] left = new int[mid];
                int[] right = new int[array.length - mid];

                arraycopy(array, 0, left, 0, left.length);
                arraycopy(array, mid, right, 0, array.length - mid);

                var leftFork = new ForkJoinMerge(left, left.length);
                var rightFork = new ForkJoinMerge(right, right.length);

                leftFork.fork();
                rightFork.fork();

                leftFork.join();
                rightFork.join();

                merge(array, left, right);
            }
        }
```

Once the new `ForkJoinMerge` instances have been created, their `fork()` method
is called. This causes the tasks to run in the same `ForkJoinPool` as the
current task. As with typical thread execution, to await the completion of the
thread, you call `join()`. Finally, as with the original algorithm, you take the
left and right arrays and merge them.

Hopefully this gives a good basic introduction to the Java fork-join framework.
You can look at more detailed and perhaps useful uses of it by looking at the
JDK itself --- `ForkJoinTask` is used in the Java stream operator
implementations for example. Or check out the `Sorter` class
in `DualPivotQuicksort`. The `Sorter` class is a `ForkJoinTask` and
`DualPivotQuicksort` is used if you call `Arrays.parallelSort()`.
