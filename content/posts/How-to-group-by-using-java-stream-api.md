---
title: How to "group by" using Java Stream API
description: Coding a function like SQL's GROUP BY using Java Stream API
date: 2021-03-12
tags:
  - blog
  - java
  - programming
draft: false
---

Recently I was trying to do essentially a "map-reduce" using the Java
Stream API ... counting the number of occurrences of words in some
input. This wasn't for some huge "big data" input set. Using Java Stream
API was sufficient. But the Stream API doesn't have a `groupBy()` operation.
While it does have `map()` and `reduce()` I couldn't add a `groupBy()` ... at
least not directly. Since it was not obvious I thought I'd write a quick post on
how to do it.

If you're not familiar with the Java Stream API it was added in Java 8
and provides a fluent API for performing operations on a set of data
i.e. a stream. The API is convenient way to operate on data that can fit
in memory. Typical use cases are to operate on Java Collections, say to
filter and transform them. Let's say you have a set of `User`s and you want to
get the surnames of the users from France (assuming your `User` class has
`surname` and`countryCode` fields), you could do something like

```java
List<User> users = loadFromSomewhere();
List<String> frenchUsers = users.stream()
    .filter(user -> user.getCountryCode().equals("FRA"))
    .map(User::getSurname)
    .collect(Collectors.toList());
```

Pretty straightforward. You can create a stream in several different ways

- calling the `stream()` method on any Collection class as above
- `Stream.of()`
- `Arrays.stream()`
- other classes have added methods to generate streams e.g. the `Pattern` class
  used for regular expression matching has a `splitAsStream()` convenience method
  which would be the equivalent of `Arrays.stream(pattern.split())` or
  `Stream.of(pattern.split())`.

With that brief introduction let's get back to the "group by" question. It's
very common to want to do some kind of computation on sets of related data. SQL
has had `GROUP BY` operation "forever" --- select data related by some
identifier to operate on the related data as a whole. It's the same thing in a
streaming application whether the Java Stream API or something more
sophisticated like Apache Kafka Streams or Spark Streaming. So how does
the Java Stream API support "group by"? It has a `collect()` function for this
purpose.

My original problem stated at the beginning was counting occurrences of
words. This could be addressed by first sorting the data --- after all I
did say that it can fit in memory. Depending on your use case that could
be sufficient. But you might need to do more than just do the count.
Let's expand on the example use case --- given a random set of words,
return the N most occurring words, and if multiple words have the same
occurrence count, they should be sorted lexicographically.

```java
List<String> mostOccurringWords(List<String> words, int N);
```

So based on the problem statement we need to

- group
- count
- sort
- limit to N
- output a List

Interestingly all but the first actually are part of the Stream API. But
we need to group by the words.

```java
List<String> mostOccurringWords(List<String> words, int N) )
    .limit(N)
    .map(Map.Entry::getKey)
    .collect(Collectors.toList());
}
```

As mentioned, to do the grouping, the Stream `collect()` method is used. It
takes a `Collector` instance. There are two implementations provided that do
grouping --- `groupingBy()` and `groupingByConcurrent()`. Both return a `Map`
implementation, it's just the latter returns a `ConcurrentMap`. These two
methods take as parameters a mapping function, and, depending on which method
signature, another `Collector` instance. In the example above, I pass a provided
instance of a `Collector` that does counting, since that's the point in this
case.

As the output of is a Map where the key is the word and the value is the word
count --- and we need both later --- I convert the Map's entry set into a stream
to further operate on the data.

Since we need the top N most occurring words, we need to do a descending sort.
By default, the sort is ascending, so we need to implement the `compareTo()`
logic as shown, providing the 2nd object count (the value of the `Map.Entry`)
first. If the counts are the same, we sort by the word per the requirements.

{{% callout type="note" %}}
if we didn't need the descending sort, could have been done with a
"comparator chain" comparing the value and `thenComparing` the key:
{{% /callout %}}


```java
.sorted(
    Comparator.comparingLong((ToLongFunction<Map.Entry<String, Long>>) Map.Entry::getValue)
      .thenComparing(Map.Entry::getKey))
```

The rest of the Stream is pretty standard, using the `limit()` function to
output only the requested number of the top occurring words, then converting
(i.e. mapping) `Map.Entry` to a`String` which is the word in the entry key and
finally generating a List to return.

Hopefully that will be helpful to you in the future. If you know of a better way
please let me know!
