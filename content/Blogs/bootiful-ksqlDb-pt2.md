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
draft: false
---

In this post I will explore the ksqlDb API for creating streams. This is
the second post about using ksqlDb with Spring Boot. Read the first post
[here](https://medium.com/everyday-programmer/bootiful-ksqldb-a4bb218d4056).

A stream in ksqlDb is analogous to a stream in Kafka Streams. One
difference is how you create the stream. As described in the first post,
a stream in Kafka Streams is created programmatically with an API.

```java
StreamsBuilder streamsBuilder = new StreamsBuilder();
KStream<Integer, Order> ordersStream = streamsBuilder.stream("orders");
ordersStream
    .filter((key, value) -> value.orderType == Electronics)
    .groupByKey()
    .aggregate(() -> 0.0f, (key, value, sum) -> sum += value.orderAmount)
    .toStream()
    .to("output");
Topology topology = streamsBuilder.build();
KafkaStreams kafkaStreams = new KafkaStreams(topology, new Properties());
kafkaStreams.start();
```

ksqlDb uplevels this to a more familiar SQL syntax. Here's an example
from the [ksqlDb quickstart](https://ksqldb.io/quickstart.html).

```sql
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

This [creates a stream](https://docs.ksqldb.io/en/latest/developer-guide/ksqldb-reference/create-stream/)
processing records from the topic `locations` with the records in JSON
format and three immutable fields. One important thing to note is that
this `CREATE STREAM` command creates the `locations` topic. There is an additional
SQL command if the topic already exists, `CREATE STREAM AS SELECT`.

Given this stream you can query it ...

```sql
SELECT * FROM riderLocations EMIT CHANGES;
```

You can also apply filters (i.e. a WHERE clause) ...

```sql
SELECT * FROM riderLocations
    WHERE GEO_DISTANCE(latitude, longitude, 37.4133, -122.1162) <= 5 EMIT CHANGES;
```

select specific columns and as shown use operations on the data.

You can execute these SQL statements via the ksqlDb CLI, but I will show
how to use the REST client API directly.

In the first post I showed a Spring WebFlux request handler class
`KsqlDbRequestHandler`. To implement the `CREATE STREAM` I will extend that class
and add a new method `createStream()`. My
approach with this is to hide the details of the ksqlDb SQL syntax from
the client. The client will simply provide the required data (e.g.
stream name, topic name, columns) and the handler will construct the SQL
statement to send to the ksqlDb server.

To that end I have a class `CreateStreamRequest`.

```java
@Data
public class CreateStreamRequest {
    String streamName;
    Map<String, String> columns;
    String sourceTopicName;
    boolean createTopic;
    int partitions;
    short replicas;
    String keyColumn;
    String valueFormat;
}
```

The `@Data` annotation is from [Lombok](https://projectlombok.org/),
a Java annotation processor which generates boilerplate during the build
process, allowing you to avoid the boilerplate in your code. The
`@Data` annotation generates the getters/setters, toString, equals, hashCode and
constructor. The `CreateStreamRequest` class is relatively
basic, and doesn't expose everything that the `CREATE STREAM` can support.

In the `KsqlDbRequestHandler` class I added a method to process a `POST` with
the `CreateStreamRequest` as the JSON body.

```java
public Mono<ServerResponse> createStream(ServerRequest serverRequest) {
    Mono<RequestStatus> result = serverRequest
        .bodyToMono(CreateStreamRequest.class)
        .map(this::executeCreateStreamRequest)
        .map(this::buildRequestStatus);

        return ServerResponse.ok().body(result, RequestStatus.class);
}

RestResponse<KsqlEntityList> executeCreateStreamRequest(CreateStreamRequest createStreamRequest) {
    String ksql = formatRequest(createStreamRequest);
    return ksqlRestClient.makeKsqlRequest(ksql);
}
```

Using the Spring WebFlux reactive API, the `createStream()` method converts the body
from the JSON to a `CreateStreamRequest` class in a `Mono`. Then the
`CreateStreamRequest` is converted to SQL in the `executeCreateStreamRequest()`
method. This is where the ksqlDb REST client is invoked to have the
ksqlDb server create the stream. The REST API is a generic
`makeSqlRequest(String sql)` for executing any ksqlDb commands.

The return value from the ksqlDb REST invocation is
`RestResponse<KsqlEntityList>`. The `RestResponse` class encapsulates a request
status (successful or unsuccessful), an error message an a
generic body, in this case `KsqlEntityList` which is just a convenience domain
specific type of `ArrayList<KsqlEntity>`. The `KsqlEntity` is just a holder for
what the SQL statement was and any warning messages that might have been
generated.

A simple integration test uses the WebFlux `WebTestClient` class while also
mocking the ksqlDb server.

```java
@WebFluxTest
@Import(WebfluxRouterConfiguration.class)
class KsqlDbRequestHandlerTest {

    @Autowired
    private RouterFunction<ServerResponse> routerFunction;

    @MockBean
    private KsqlRestClient ksqlRestClient;

    private WebTestClient webTestClient;

    @BeforeEach
    private void setup() {
        webTestClient = bindToRouterFunction(routerFunction)
            .configureClient()
            // need some time if using a debugger ...
            .responseTimeout(Duration.ofMinutes(10))
            .build();
    }

    @Test
    void createStreamRequest() {
        KsqlEntityList ksqlEntities = new KsqlEntityList(emptyList());
        RestResponse<KsqlEntityList> restResponse = successful(OK.value(), ksqlEntities);

        String expectedSql =
            "CREATE STREAM test (first int,second string) WITH (kafka_topic = 'input', partitions = 1, value_format = 'json');";
        given(ksqlRestClient.makeKsqlRequest(eq(expectedSql))).willReturn(restResponse);

        CreateStreamRequest createStreamRequest = new CreateStreamRequest();
        createStreamRequest.setCreateTopic(true);
        createStreamRequest.setStreamName("test");
        createStreamRequest.setSourceTopicName("input");
        createStreamRequest.setPartitions(1);
        createStreamRequest.setValueFormat("json");
        Map<String, String> columns = new HashMap<>();
        columns.put("first", "int");
        columns.put("second", "string");
        createStreamRequest.setColumns(columns);

        webTestClient.post()
            .uri("/stream")
            .bodyValue(createStreamRequest)
            .exchange()
            .expectStatus().isOk()
            .expectBody(RequestStatus.class)
            .value(equalTo(new RequestStatus(KsqlDbRequestHandler.REQUEST_SUCCESS_MESSAGE, ksqlEntities)));
    }
}
```

One thing to note is the setup, which shows how to configure the `WebTestClient`
class, in this case to change the timeout. This was useful as noted when using
the debugger since the `WebTestClient` would otherwise
timeout while trying to figure out what's going on.

Rather than mocking the ksqlDb server, I could use the Testcontainers
project as described in the first post.

In future posts I will show how to process data and use "pull queries"
which I think is a really nice feature of ksqlDb.
