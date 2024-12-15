---
title: Spring Boot Under the Hood
description:
created: 2024-11-29
tags:
  - springboot
  - java
  - programming
  - kubernetes
  - REST
  - observability
  - blog
draft: false
---

In this series of posts I will dive "under the hood" of Spring Boot by implementing an application with multiple services, deployed to the cloud in Kubernetes, with authentication and authorization, observability (logging, metrics, distributed tracing), REST APIs, data stored in [Neo4j](https://neo4j.com/) and more. The point of the series is less about the application itself, but learning how Spring and Spring Boot do what they do. There is a lot of "magic" - or seemingly so - when you build a Spring Boot-based application. I mean, think about it - you can write 8 lines of code (ignoring the package and imports)

```java
@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

and you get a full servlet container, logging, multiple levels of configuration properties, and more. After reading this series you'll know how the magic happens and even make some magic yourself!

## A (very) Brief History of Spring Boot

**_tl;dr_**; Spring Framework - unopinionated; Spring Boot - opinionated.

Spring Framework came out of a book by Rod Johnson, [J2EE Development Without EJB](https://www.amazon.com/Expert-One-One-Development-without/dp/0764558315) 20 years ago at time of writing, along with subsequent books like Professional Java Development with the Spring Framework. A set of libraries, you used them as you wished. The Spring Framework took no opinion on how to use it. Spring Boot came out about ten years later, with a different approach, having very specific opinions on the best way to structure and build your Spring Framework-based solutions. You can read this in their own words from the [Spring Boot v1 documentation](https://docs.spring.io/spring-boot/docs/1.1.1.RELEASE/reference/html/getting-started-introducing-spring-boot.html).

## Prerequisites

I will assume you know Java, are passingly familiar with Gradle, can use a terminal and shell and understand basic concepts in Spring Framework like dependency injection, beans, controllers, etc.. I will not assume much experience with Spring Boot, so if you know Boot already, you can skim this first post and/or jump around as you like.

## Environment

While I will be doing my development on Linux, nothing prohibits using your favorite operating system. Similarly, use your favorite editor, though I personally love JetBrains' IntelliJ IDEA. (Check out my blog on my [IntelliJ/Neovim](https://kidoni.dev/could-i-possibly-switch-from-jetbrains-ides-to-neovim-fec994619b6d) equivocation.)

I will be using Java 23, but I'll go over one tool you can use to (optionally) get and manage some of these development dependencies.

## Outline

Here's what we will go through in these posts.

- setting up the environment and creating a new, initial project; I'll also describe the sample application we'll build
- motivation behind Spring Boot; what are "starters"; running the application and running tests
- features in Boot supporting development and testing
- Spring Boot Actuator
- Configuring Spring Boot applications

> TODO more here

## Setting Up

There are many ways to get your basic development environment set up. Most of you probably already have a working environment. I will cover a couple of options that could help you, particularly if you work on many different projects, possibly with differing tool dependencies and versions of same.

### sdkman

The first is `sdkman`. This is an "SDK" manager though I'd say it's more of a tool manager. While most if not all of what `sdkman` can install and manage could be installed with brew or apt or whatever package manager you use, one nice thing about `sdkman` is that you can configure your project so that `sdkman` will set the correct versions for that project. First, install `sdkman` by going to your favorite terminal and

```bash
curl -s "https://get.sdkman.io" | bash
```

Sdkman can manage a bunch of different things. You can see what's available with `sdkman` list. For our purposes we'll install Java 23 and Groovy. We'll also install the Spring Boot CLI, which I'll show how to use to create a new Boot project. By default, `sdkman` will install the latest but you can install any version. The versions available are listed with `sdk list <tool>` e.g. `sdk list java`. You install tools with `sdk install`. It will ask if you want to set the version you're installing as the default. That's up to you, as I'll show how to set the version per-project later, after we create the initial Boot project.

```bash

sdk install java 23-tem
sdk install springboot
```

Assuming everything installed OK, you should see something like this when you check:

```bash
$ sdk current

Using:

java: 23-tem
springboot: 3.3.4
```

### direnv

Another nifty tool that will come in handy as you'll see is `direnv`. This allows managing environment variables per project (technically per directory). This is not something installed via `sdkman`, so you can use `brew` or your system's package manager.

> Did you know brew also works on Linux? It's not just for MacOS! You install it the same way, whether MacOS, Linux and even WSL.

```bash
brew install direnv
```

That's all you need for us to get started creating our Spring Boot app!

## Creating the Project

The recommended way to create a new Spring Boot project is using [https://start.spring.io](https://start.spring.io). But you can also use the Spring Boot CLI we just installed with `sdkman`, which by default will use `start.spring.io`. If you love the terminal, it's a great alternative. You create a new project using `spring init`. Let's create the initial project.

```bash
$ spring init -n six-degrees -x -j 23 -d \
  actuator,web,netflix-dgs,native,lombok,hateoas,devtools,dgs-codegen, \
  distributed-tracing,data-neo4j,configuration-processor,docker-compose, \
  testcontainers \
  six-degrees
Using service at https://start.spring.io
Project extracted to '/home/ray/six-degrees'
```

Let's break this down

- `-n` six-degrees - this sets the application name used by Spring Boot; it sets the property `spring.application.name=six-degrees` in the file `src/main/resources/application.properties` in our generated project.
- `-x` - normally the result of calling `spring init` (and using `start.spring.io` directly) is a zip file; `-x` tells `spring init` to immediately extract the zip rather than saving the zip file, saving an extra step.
- `-j` - indicates the Java version we want to use
- `-d[packages]` - here we provide a list of the Spring Boot and 3rd party dependencies we want to use in our project. Use `spring init --list` to view available dependencies.
- `six-degrees` - finally we give the name of our project; this is stored in the `settings.gradle` file: `rootProject.name = 'six-degrees'`.

What you should get after running `spring init` is

```bash
$ tree six-degrees
six-degrees
├── build.gradle
├── compose.yaml
├── gradle
│   └── wrapper
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── gradlew
├── gradlew.bat
├── HELP.md
├── settings.gradle
└── src
    ├── main
    │   ├── java
    │   │   └── com
    │   │       └── example
    │   │           └── six_degrees
    │   │               └── SixDegreesApplication.java
    │   └── resources
    │       ├── application.properties
    │       ├── graphql-client
    │       ├── static
    │       └── templates
    └── test
        └── java
            └── com
                └── example
                    └── six_degrees
                        ├── SixDegreesApplicationTests.java
                        ├── TestcontainersConfiguration.java
                        └── TestSixDegreesApplication.java

18 directories, 13 files
```

## Verify the Project

This is a fully functional, running project including some basic tests. You can verify that the project builds and runs.

```bash
$ cd six-degrees
$ ./gradlew build
[lots of log output]
BUILD SUCCESSFUL in 21s
15 actionable tasks: 15 executed

$ ./gradlew bootRun
```

The `bootRun` command launches the Spring Boot application, which at this point is just the autogenerated shell created via `spring init`. Still, it is a fully functional application. You should see log output to the console, ending with something like

```bash
2024-12-01T12:57:29.109-08:00  INFO 680736 --- [six-degrees] [  restartedMain] [                                                 ] c.e.six_degrees.SixDegreesApplication    : Started SixDegreesApplication in 10.099 seconds (process running for 10.312)
<===========--> 90% EXECUTING [2m 29s]
> :bootRun
```

There are several ways you can verify the startup was successful, besides the above log message. One of the dependencies we included with `spring init` was the Spring Boot Actuator. This provides various management REST APIs, including a health endpoint. To query that, you can use your browser or simply

```bash
$ curl localhost:8080/actuator/health
HTTP/1.1 200
Content-Type: application/json
Transfer-Encoding: chunked
Date: Sun, 01 Dec 2024 21:00:56 GMT

{
    "status": "UP"
}
```

We will go over the Actuator APIs in future posts.

Let's go over each of the files that `spring init` generated for us, to lay the foundation upon which we'll build our application. We'll go into much more detail in subsequent blogs, since there's already a lot of Spring Boot magic going on!

## The Initial Project Contents

### Gradle

The default build system is Gradle, which is why `spring init` created the `*.gradle` and `gradle` wrapper files. By default it's also using Groovy syntax. You can pick Kotlin if you prefer, via `spring init` options.

### Docker Compose

The `docker-compose` dependency selected in `spring init` creates a `compose.yml` file for use during development. Because we also selected Spring Data Neo4j the `compose.yml` file has a Neo4j database configured. The `build.gradle` file as a development-only dependency.

```bash
developmentOnly 'org.springframework.boot:spring-boot-docker-compose'
```

which causes Spring Boot to look for the `compose.yml` file and do a `docker compose up` with it, so that Neo4J is started and a connection to it is created.

### Sources

A default main application is generated called along with an initial configuration file.

```bash
main
├── java
│ └── com
  │ └── example
    │ └── six_degrees
      │ └── DemoApplication.java
└── resources
  └─── application.properties
```

We will cover these in detail in the next post.

### Test Sources and Testcontainers

Regardless of other options provided to `spring init`, a default test class is created with a single test method which verifies that the application can start as configured. This is the file `DemoApplicationTests.java`. But since we have a dependency on Spring Data Neo4j which needs a Neo4j database, the application won't start properly without a Neo4j database available. This is where the `Testcontainers` support comes in. We added that to our `spring init` dependencies, so that `Testcontainers` can automatically create a Neo4j instance in a container for use by the test code.

We'll get to it and testing Spring Boot apps in a subsequent post.

## Next Steps

In the next post in the series, I will dig in to the `main()` method defined in `com.example.six_degrees.DemoApplication.java` since that simple `main()` method, as shown at the very beginning of this blog post, contains only one line but so much magic happens because of one "simple" annotation

```java
@SpringBootApplication
```

We'll dive into what this annotation means for Spring Boot. This will lead us down the magic rabbit hole, touching on what "autoconfiguration" is and "starter" modules, how dependency injection works and more.

I hope you find this interesting and worth the time!

## Resources

All of the code for this blog series can be found [here](https::/github.com/raysuliteanu/six-degrees-backend). There are tags for each post along the way, if you want to look at just what's covered at each step. The main branch will have the final code, if you just want to see the finished application.

The Spring Boot documentation is very good, as are the examples.
