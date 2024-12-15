---
title: Bootiful ksqlDb part 2 --- creating a stream
description:
date:
tags:
  - blog
  - springboot
  - apachkafka
  - kafka
  - kafkastreams
  - java
draft: true
---

In this post I will explore the ksqlDb API for creating streams. This is
the second post about using ksqlDb with Spring Boot. Read the first post
[here](https://medium.com/everyday-programmer/bootiful-ksqldb-a4bb218d4056){.markup--anchor
.markup--p-anchor
data-href="<https://medium.com/everyday-programmer/bootiful-ksqldb-a4bb218d4056>"
target="\_blank"}.

A stream in ksqlDb is analogous to a stream in Kafka Streams. One
difference is how you create the stream. As described in the first post,
a stream in Kafka Streams is created programmatically with an API.

<figure id="443d" class="graf graf--figure graf--iframe graf-after--p">

</figure>

ksqlDb uplevels this to a more familiar SQL syntax. Here's an example
from the [ksqlDb
quickstart](https://ksqldb.io/quickstart.html){.markup--anchor
.markup--p-anchor data-href="<https://ksqldb.io/quickstart.html>"
rel="noopener" target="\_blank"}.

```{#ddb2 .graf .graf--pre .graf-after--p}
CREATE STREAM riderLocations (
    profileId VARCHAR,
    latitude DOUBLE,
    longitude DOUBLE
)
WITH (
    kafka_topic='locations',
    value_format='json',
    partitions=1
);
```

This [creates a
stream](https://docs.ksqldb.io/en/latest/developer-guide/ksqldb-reference/create-stream/){.markup--anchor
.markup--p-anchor
data-href="<https://docs.ksqldb.io/en/latest/developer-guide/ksqldb-reference/create-stream/>"
rel="noopener" target="\_blank"} processing records from the topic
`locations`{.markup--code .markup--p-code} with the records in JSON
format and three immutable fields. One important thing to note is that
this `CREATE STREAM`{.markup--code .markup--p-code} command creates the
`locations`{.markup--code .markup--p-code} topic. There is an additional
SQL command if the topic already exists,
`CREATE STREAM AS SELECT`{.markup--code .markup--p-code}.

Given this stream you can query it ...

```{#c1aa .graf .graf--pre .graf-after--p}
SELECT * FROM riderLocations EMIT CHANGES;
```

You can also apply filters (i.e. a WHERE clause) ...

```{#b8eb .graf .graf--pre .graf-after--p}
SELECT * FROM riderLocations
    WHERE GEO_DISTANCE(latitude, longitude, 37.4133, -122.1162) <= 5 EMIT CHANGES;
```

select specific columns and as shown use operations on the data.

You can execute these SQL statements via the ksqlDb CLI, but I will show
how to use the REST client API directly.

In the first post I showed a Spring WebFlux request handler class
`KsqlDbRequestHandler`{.markup--code .markup--p-code}. To implement the
`CREATE STREAM`{.markup--code .markup--p-code} I will extend that class
and add a new method `createStream()`{.markup--code .markup--p-code}. My
approach with this is to hide the details of the ksqlDb SQL syntax from
the client. The client will simply provide the required data (e.g.
stream name, topic name, columns) and the handler will construct the SQL
statement to send to the ksqlDb server.

To that end I have a class `CreateStreamRequest`{.markup--code
.markup--p-code}.

<figure id="af87" class="graf graf--figure graf--iframe graf-after--p">

</figure>

The `@Data`{.markup--code .markup--p-code} annotation is from
[Lombok](https://projectlombok.org/){.markup--anchor .markup--p-anchor
data-href="<https://projectlombok.org/>" rel="noopener" target="\_blank"},
a Java annotation processor which generates boilerplate during the build
process, allowing you to avoid the boilerplate in your code. The
`@Data`{.markup--code .markup--p-code} annotation generates the
getters/setters, toString, equals, hashCode and constructor. The
`CreateStreamRequest`{.markup--code .markup--p-code} class is relatively
basic, and doesn't expose everything that the
`CREATE STREAM`{.markup--code .markup--p-code} can support.

In the `KsqlDbRequestHandler`{.markup--code .markup--p-code} class I
added a method to process a `POST`{.markup--code .markup--p-code} with
the `CreateStreamRequest`{.markup--code .markup--p-code} as the JSON
body.

<figure id="f1bf" class="graf graf--figure graf--iframe graf-after--p">

</figure>

Using the Spring WebFlux reactive API, the
`createStream()`{.markup--code .markup--p-code} method converts the body
from the JSON to a `CreateStreamRequest`{.markup--code .markup--p-code}
class in a `Mono`{.markup--code .markup--p-code}. Then the
`CreateStreamRequest`{.markup--code .markup--p-code} is converted to SQL
in the `executeCreateStreamRequest()`{.markup--code .markup--p-code}
method. This is where the ksqlDb REST client is invoked to have the
ksqlDb server create the stream. The REST API is a generic
`makeSqlRequest(String sql)`{.markup--code .markup--p-code} for
executing any ksqlDb commands.

The return value from the ksqlDb REST invocation is
`RestResponse<KsqlEntityList>`{.markup--code .markup--p-code}. The
`RestResponse`{.markup--code .markup--p-code} class encapsulates a
request status (successful or unsuccessful), an error message an a
generic body, in this case `KsqlEntityList`{.markup--code
.markup--p-code} which is just a convenience domain specific type of
`ArrayList<KsqlEntity>`{.markup--code .markup--p-code}. The
`KsqlEntity`{.markup--code .markup--p-code} is just a holder for what
the SQL statement was and any warning messages that might have been
generated.

A simple integration test uses the WebFlux `WebTestClient`{.markup--code
.markup--p-code} class while also mocking the ksqlDb server.

<figure id="52f3" class="graf graf--figure graf--iframe graf-after--p">

</figure>

One thing to note is the setup, which shows how to configure the
`WebTestClient`{.markup--code .markup--p-code} class, in this case to
change the timeout. This was useful as noted when using the debugger
since the `WebTestClient`{.markup--code .markup--p-code} would otherwise
timeout while trying to figure out what's going on.

Rather than mocking the ksqlDb server, I could use the Testcontainers
project as described in the first post.

In future posts I will show how to process data and use "pull queries"
which I think is a really nice feature of ksqlDb.
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [December 31, 2020](https://medium.com/p/ef5d1cfa62a8).

[Canonical
link](https://medium.com/@raysuliteanu/bootiful-ksqldb-part-2-creating-a-stream-ef5d1cfa62a8){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
