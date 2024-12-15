---
title: Bootiful ksqlDb
description:
created: 2020-11-25
tags:
  - blog
  - springboot
  - apachkafka
  - kafka
  - kafkastreams
  - java
draft: true
---

In this post I will show how to use the [ksqlDb](https://docs.ksqldb.io/en/latest/)
Java REST client to interact with the ksqlDb server using a Spring Boot
application as a foundation. The Boot app will also use
[Spring Webflux](https://docs.spring.io/spring-framework/docs/current/reference/html/web-reactive.html)
to help expand the use of reactive programming. I will also show the use of the
[Testcontainers](https://testcontainers.org) framework for integrating
deployment of Docker containers as part of integration testing, in this case
with JUnit 5.

What this will not cover is details of [Apache Kafka](http://kafka.apache.org) or
[Spring Boot](https://docs.spring.io/spring-boot/docs/current/reference/html/index.html),
or even ksqlDb and streaming systems,
except to provide background to understand the code. There are plenty of
other examples and posts that cover those details.

The code covered in this post is available on GitHub
[here](https://github.com/raysuliteanu/ksqldb-demo). This is the first of
several posts that will expand on
the use of ksqlDb and Spring Boot microservices.

## What is ksqlDb?

To understand ksqlDb you need to understand where it comes from. First
there is Apache Kafka, one of the most popular messaging systems in use
today. Apache Kafka is an open-source project that originated at
LinkedIn, and the founders subsequently formed [Confluent
Inc](https://www.confluent.io/).
Then there is Kafka Streams, which adds streaming metaphors as a library
leveraging Kafka.

## Kafka

At the heart of Kafka, and what distinguishes it from other messaging
systems, is the notion of a "log." We're not talking here about logging
systems most developers use daily to write errors or debug messages. A
log in the Kafka context is the same as used by database systems. An
excellent discussion can be found
[here](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
on the LinkedIn engineering blog,
written by the co-founder of Confluent.

Suffice to say for the purposes of this post that a log is an
append-only file of immutable records. In Kafka, logs are used to store
messages written to 'topics.' A topic is the fundamental interconnect
between 'producers' that write to topics, and 'consumers' that read from
topics. Producers and consumers are independent. Through the use of
logs, producers and consumers can operate at different speeds, in
different locations and have guarantees that records aren't lost. Kafka
can support 'exactly once' message delivery, unlike most messaging
systems.

## Kafka Streams

On top of this foundation, Kafka Streams is a library that enables
streaming operations applied to data consumed from topics. For example,
you can apply a 'filter' operation followed by an 'aggregation'
operation (e.g. sum, count, min, max, average) followed by a 'transform'
operation, on records read from a topic. You can also apply a 'group'
operation, so that operations are applied on records related to each
other. For example, you might be processing orders and have an
'order-id' or payments that have an 'account-number'. The series of
operations form a graph or 'topology' as it is called in Kafka Streams.

For additional details on Kafka Streams please read the documentation,
in particular the architecture described
[here](http://kafka.apache.org/26/documentation/streams/architecture).

## ksqlDb

Both Kafka and Kafka Streams are sophisticated technologies, with a lot
of options in how to use, deploy and scale. And the Kafka Streams
library is just that --- a library. Developers must learn the API and
build their own topologies in a microservice that they build, deploy and
manage. This is non-trivial (as I know first hand).

If you consider the example operations I described above --- filter,
sum, group and the rest --- it may come to mind that this somewhat maps
to a SQL query on some data in a database table. Let's say you wanted to
get list by customer of the total amount they spent on orders of
electronics. In SQL it would be something like

```sql
SELECT CUST_ID, SUM(ORDER_AMT)
    WHERE ORDER_CAT = ‘ELECTRONICS’
    GROUP BY ORDER_ID
```

You can also express that using the Kafka Streams API:

TODO: missing gist, replace with inline

As you can see, it's somewhat more complicated than the SQL. You have to
create the stream using the builder (line 1), define your operations
(lines 4--6) convert to a Topology (line 9) which is then provided to
the `KafkaStream` manager that handles
the lifecycle (line 10), which I've limited to showing the call to the
`start()` method (line 11). You also must
manage the source and sink topics yourself, called "orders" and "output"
in the example, ensuring they exist.

This is a relatively simple topology. You could have several or
hundreds, each with a much larger set of operations. Each topology is
independent with its own lifecycle.

The folks at Confluent must have realized this, perhaps from customer
and community feedback (I'm not affiliated with Confluent so I don't
know within whose head the lightbulb went off). To simplify the use of
Kafka Streams and broaden its appeal, they came up with ksqlDb.

ksqlDb abstracts the details of the Streams API, the topology building
and management, deployment, scaling and all that fun stuff. It lets
users leverage a familiar API --- SQL --- to build streaming
applications. Check out the ksqlDb quickstart
[here](https://ksqldb.io/quickstart.html), to get a sense of the usage from a user
point of view.

## Spring Boot and ksqlDb client

The Boot application described here acts as a client to the ksqlDb
server. The Boot application will expose its own REST API, as a proxy
for the actual ksqlDb REST API. The ksqlDb server itself requires Kafka,
which requires Zookeeper. The easiest way to run all of this on your
laptop is with Docker and docker-compose. The ksqlDb quickstart provides
a docker-compose file, which I leverage pretty much [as
is](https://github.com/raysuliteanu/ksqldb-demo/blob/master/docker-compose.yml).

As such, Docker is a prerequisite for running this Boot app.

TODO: missing gist, replace with inline

With Spring Webflux you need two things, a router configuration that
maps REST endpoints to handler functions, and the handler functions. For
the purposes of this example (to be expanded on in future posts) I will
proxy the ksqlDb REST client "server info" method that queries the
ksqlDb server for some metadata. So the Webflux router exposes a "/info"
endpoint and routes to a handler.

TODO: missing gist, replace with inline

The `infoRouterFunction()` uses the
injected handler bean and associates "/info" with the
`KsqlDbRequestHandler.info)`method. The
`KsqlDbRequestHandler` itself is injected
with the `KsqlRestClient`. For now, it
assumes that the ksqlDb server deployed via Docker has its port mapped
to 8088 on the local machine, so that the Boot application doesn't
itself have to be deployed within the Docker cluster. The server address
for the ksqlDb server should be configurable of course, and I will
enhance the application to use the Boot externalized configuration
support.

The handler class shown next is similarly relatively straightforward.

TODO: missing gist, replace with inline

The ksqlDb REST client has a `serverInfo()` method as mentioned. The handler's
`info()` method simply executes the
method and handles the response. If successful, it formats the output
nicely and returns it. Otherwise it formats an error response. The
Webflux `ServerResponse`provides a nice
fluent API to form the response message. In Webflux there are two basic
types, `Mono` which returns a single
value, and `Flux` which returns a stream
of responses. In this case the server info is just a single string, so
the handler returns a `Mono<ServerResponse>`.

That's all there is to it, for a basic example. You could run this now
manually, by starting the ksqlDb server and dependent services via
docker-compose followed by running the Boot app --- either via the
Maven/Gradle Boot plugins or from the command line.

But as good developers we write tests right. How would you test this
Boot application? It requires the deployment of three services for a
full test without mocks (you could mock the ksqlDb server by mocking the
`KsqlRestClient`). But let's say we want
to test the real thing.

There's a convenient open source project called Testcontainers. You can
deploy specific containers that it's created integrations with directly,
everything from Kafka to Cassandra to Elasticsearch. But it also
supports running a docker-compose file, for more complicated scenarios
and orchestration.

Testcontainers also integrates easily with JUnit 5. Simply use the
`@Container` annotation.

TODO: missing gist, replace with inline

For testing, I created a stripped down and slightly modified
docker-compose YAML file and put it in the test resources folder. As you
can see it exposes port `8088` as our
REST client configuration expects. Before the tests run, Testcontainers
will ensure the services are up, verified by pinging the ksqlDb server
container's healthcheck endpoint as defined in the compose-test.yml
file.

Now to test the Boot application's /info endpoint that we've created.
With Webflux there's a test class called `WebTestClient`. Using this class
the test will execute a call to the
Boot application and check the response.

TODO: missing gist, replace with inline

Line 1 enables the Testcontainers integration and line 2 ensures that a
`WebTestClient` is created and available
for autowiring (line 14). Then we have our actual test method, standard
JUnit 5. Line 18 specifies the REST method, line 19 defines the endpoint
to invoke, line 20 performs the execution and the remaining lines
specify the expected response, the response type and the expected
content.

## Summary

Hopefully you now have a basic understanding of ksqlDb's purpose and how
to integrate with it via its REST API. Also, how to test containers in
combination with Spring Boot and Spring Webflux.

Subsequent posts will expand on this post to get to the point of
dynamically creating ksqlDb streams, tables and materialized views, and
enabling a REST-based API for doing so, including streaming the results
of the queries.
