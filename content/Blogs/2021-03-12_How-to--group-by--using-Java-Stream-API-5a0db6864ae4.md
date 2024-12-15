---
title: 
description: 
date: 
tags:
  - blog
draft: true
---

<div>

# How to "group by" using Java Stream API {#how-to-group-by-using-java-stream-api .p-name}

</div>

::: {.section .p-summary field="subtitle"}
Recently I was trying to do essentially a "map-reduce" using the Java
Stream API ... counting the number of occurrences of words in some...
:::

::: {.section .e-content field="body"}
::: {#d173 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### How to "group by" using Java Stream API {#6de6 .graf .graf--h3 .graf--leading .graf--title name="6de6"}

<figure id="3fd0" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*3NLQD0vZO62ypvRz"
class="graf-image" data-image-id="0*3NLQD0vZO62ypvRz" data-width="6000"
data-height="4000" data-unsplash-photo-id="fsc2v3jfxvk"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@karimsan?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@karimsan?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Karim Sakhibgareev</a>
on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

Recently I was trying to do essentially a "map-reduce" using the Java
Stream API ... counting the number of occurrences of words in some
input. This wasn't for some huge "big data" input set. Using Java Stream
API was sufficient. But the Stream API doesn't have a
`groupBy()`{.markup--code .markup--p-code} operation. While it does have
`map()`{.markup--code .markup--p-code} and `reduce()`{.markup--code
.markup--p-code} I couldn't add a `groupBy()`{.markup--code
.markup--p-code} ... at least not directly. Since it was not obvious I
thought I'd write a quick post on how to do it.

If you're not familiar with the Java Stream API it was added in Java 8
and provides a fluent API for performing operations on a set of data
i.e. a stream. The API is convenient way to operate on data that can fit
in memory. Typical use cases are to operate on Java Collections, say to
filter and transform them. Let's say you have a set of
`User`{.markup--code .markup--p-code}s and you want to get the surnames
of the users from France (assuming your `User`{.markup--code
.markup--p-code} class has `surname`{.markup--code .markup--p-code}
and`countryCode`{.markup--code .markup--p-code} fields), you could do
something like

``` {#d624 .graf .graf--pre .graf-after--p}
List<User> users = loadFromSomewhere();
List<String> frenchUsers = users.stream()
    .filter(user -> user.getCountryCode().equals("FRA"))
    .map(User::getSurname)
    .collect(Collectors.toList());
```

Pretty straightforward. You can create a stream in several different
ways

-   [calling the `stream()`{.markup--code .markup--li-code} method on
    any Collection class as above]{#a12c}
-   [`Stream.of()`{.markup--code .markup--li-code}]{#f77d}
-   [`Arrays.stream()`{.markup--code .markup--li-code}]{#b988}
-   [other classes have added methods to generate streams e.g. the
    `Pattern`{.markup--code .markup--li-code} class used for regular
    expression matching has a `splitAsStream()`{.markup--code
    .markup--li-code} convenience method which would be the equivalent
    of `Arrays.stream(pattern.split())`{.markup--code .markup--li-code}
    or `Stream.of(pattern.split())`{.markup--code
    .markup--li-code}.]{#bbad}

With that brief introduction let's get back to the "group by" question.
It's very common to want to do some kind of computation on sets of
related data. SQL has had `GROUP BY`{.markup--code .markup--p-code}
operation "forever" --- select data related by some identifier to
operate on the related data as a whole. It's the same thing in a
streaming application whether the Java Stream API or something more
sophisticated like Apache Kafka Streams or Spark Streaming. So how does
the Java Stream API support "group by"? It has a
`collect()`{.markup--code .markup--p-code} function for this purpose.

My original problem stated at the beginning was counting occurrences of
words. This could be addressed by first sorting the data --- after all I
did say that it can fit in memory. Depending on your use case that could
be sufficient. But you might need to do more than just do the count.
Let's expand on the example use case --- given a random set of words,
return the N most occurring words, and if multiple words have the same
occurrence count, they should be sorted lexicographically.

``` {#ce11 .graf .graf--pre .graf-after--p}
List<String> mostOccurringWords(List<String> words, int N);
```

So based on the problem statement we need to

-   [group]{#2d5b}
-   [count]{#65b8}
-   [sort]{#e924}
-   [limit to N]{#3b68}
-   [output a List]{#de1e}

Interestingly all but the first actually are part of the Stream API. But
we need to group by the words.

``` {#73a3 .graf .graf--pre .graf-after--p}
List<String> mostOccurringWords(List<String> words, int N) {
    return words.stream()
(1)     .collect(Collectors.groupingByConcurrent(word -> 
            word, Collectors.counting()))
(2)     .entrySet().stream()
        .sorted((o1, o2) -> {
            final int compareCount = 
(3)             Integer.compare(o2.getValue(), o1.getValue());
            return compareCount != 0 ? compareCount :
                o1.getKey().compareTo(o2.getKey());
        })
        .limit(N)
(4)     .map(Map.Entry::getKey)
        .collect(Collectors.toList());
}
```

\(1\) As mentioned, to do the grouping, the Stream
`collect()`{.markup--code .markup--p-code} method is used. It takes a
`Collector`{.markup--code .markup--p-code} instance. There are two
implementations provided that do
grouping --- `groupingBy()`{.markup--code .markup--p-code} and
`groupingByConcurrent()`{.markup--code .markup--p-code}. Both return a
`Map`{.markup--code .markup--p-code} implementation, it's just the
latter returns a `ConcurrentMap`{.markup--code .markup--p-code}. These
two methods take as parameters a mapping function, and, depending on
which method signature, another `Collector`{.markup--code
.markup--p-code} instance. In the example above, I pass a provided
instance of a `Collector`{.markup--code .markup--p-code} that does
counting, since that's the point in this case.

\(2\) As the output of (1) is a Map where the key is the word and the
value is the word count --- and we need both later --- I convert the
Map's entry set into a stream to further operate on the data.

\(3\) Since we need the top N most occurring words, we need to do a
descending sort. By default, the sort is ascending, so we need to
implement the `compareTo()`{.markup--code .markup--p-code} logic as
shown, providing the 2nd object count (the value of the
`Map.Entry`{.markup--code .markup--p-code}) first. If the counts are the
same, we sort by the word per the requirements.

NOTE: if we didn't need the descending sort, (3) could have been done
with a "comparator chain" comparing the value and
`thenComparing`{.markup--code .markup--p-code} the key:

``` {#23f8 .graf .graf--pre .graf-after--p}
.sorted(Comparator.comparingLong((ToLongFunction<Map.Entry<String, Long>>) Map.Entry::getValue).thenComparing(Map.Entry::getKey))
```

The rest of the Stream is pretty standard, using the
`limit()`{.markup--code .markup--p-code} function to output only the
requested number of the top occurring words, then converting (i.e.
mapping) `Map.Entry`{.markup--code .markup--p-code} to
a`String`{.markup--code .markup--p-code} which is the word in the entry
key and finally generating a List to return.

Hopefully that will be helpful to you in the future. If you know of a
better way please let me know!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [March 12, 2021](https://medium.com/p/5a0db6864ae4).

[Canonical
link](https://medium.com/@raysuliteanu/how-to-group-by-using-java-stream-api-5a0db6864ae4){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
