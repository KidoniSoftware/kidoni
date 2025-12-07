---
title: Level Up Your Rust Testing With testcontainers and rstest
description: Leverage the `testcontainers` and `rstest` crates for testing with Rust
date: 2025-12-07
tags:
  - blog
  - rust
  - testing
  - integration-testing
  - containers
  - docker
draft: false
---

Writing software tests is hard. Whether you're writing unit tests or integration
tests or system tests, each presents unique challenges that generally only get
harder as you go from unit to integration to system testing.

> [!NOTE]
> To see how I differentiate these types of tests, see my [post here](there-is-no-such-thing-as-regression-testing).

Writing unit tests in Rust is relatively straightforward, with built in support
via `#[test]` annotations and test configuration support. The `cargo new` command
even generates an initial test module and test for you:

```rust
pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
```

Most real testing scenarios however are not as simple, and setting up your tests
can take some coding. This test setup code is called test 'fixtures'. The Rust
ecosystem has some good options for this. One option that is relatively well
known is the `proptest` crate, which will generate various inputs including edge
cases. You can [check it out](https://proptest-rs.github.io/proptest/intro.html)
for yourself; it's a great tool for your arsenal.

However, here I'm going to show you how to use a crate for when you may need more
handcrafted test fixtures. This crate is called [rstest](https://docs.rs/rstest/latest/rstest/index.html).

## Test Fixtures With rstest

Let's imagine you have a `User` type.

```rust
struct User {
    user_name: String,
    full_name: String,
}
```

and for the sake of discussion let's imagine you have a user cache (though to
keep this focused on the testing I'll just make it a HashMap)

```rust
type UserCache = HashMap<String, User>;
```

Now you want to test your cache, and to do that you need some `User`s. You could
do something like:

```rust
#[test]
fn cache_contains_user() {
    let users = vec![
        (
            "user1".to_string(),
            User::new("user1".to_string(), "User One".to_string()),
        ),
        (
            "user2".to_string(),
            User::new("user2".to_string(), "User Two".to_string()),
        ),
        (
            "user3".to_string(),
            User::new("user3".to_string(), "User Three".to_string()),
        ),
        (
            "user4".to_string(),
            User::new("user4".to_string(), "User Four".to_string()),
        ),
    ];
    let cache = UserCache::from_iter(users);
    assert!(cache.contains_key("user3"));
    assert!(!cache.contains_key("user5"));
}
```

Now maybe you want to test removing a user, or adding a new user, etc. etc.. If
you keep copying the `vec![]` code that's pretty ugly. You could extract it into
a helper function and then call that.

```rust
fn create_users() -> Vec<(String, User)> {
    vec![
        (
            "user1".to_string(),
            User::new("user1".to_string(), "User One".to_string()),
        ),
        // same as before ...
    ]
}

#[test]
fn cache_contains_user() {
    let users = create_users()
    // ...
```

You're on the right path with that. This `create_users()` method is a test fixture.
What the `rstest` crate lets you do is declare the method as such, and then you
declare your test as needing that test fixture as input:

```rust
#[cfg(test)]
mod tests {
    use rstest::{fixture, rstest};

    use super::*;

    #[fixture]
    fn users() -> Vec<(String, User)> {
        vec![
            (
                "user1".to_string(),
                User::new("user1".to_string(), "User One".to_string()),
            ),
            // same as before ...
        ]
    }

    #[rstest]
    fn cache_contains_user(users: Vec<(String, User)>) {
        let cache = UserCache::from_iter(users);
        assert!(cache.contains_key("user3"));
        assert!(!cache.contains_key("user5"));
    }
}
```

This test declares the test method as an `#[rstest]` rather than a `#[test]` and
takes a parameter whose name must match the name of a function declared with
`#[fixture]`. The fixture method generates the test data to be used and `rstest`
generates the code that will call the `users()` method and pass the result as the
input to the test method. You might argue that if that's all there was to it, the
addition of `rstest` doesn't buy you much, and that might be true.

But you can also compose fixtures! In other words a fixture can be input to
another fixture. You could change this test to focus on the user cache by
having a fixture that produces a populated cache, populating the cache with the
users from the user fixture. And on top of that, a test can take multiple fixtures
as input, as shown in the following example.

```rust
#[fixture]
fn users() -> Vec<(String, User)> {
    vec![
        (
            "user1".to_string(),
            User::new("user1".to_string(), "User One".to_string()),
        ),
        // same as before ...
    ]
}

#[fixture]
fn user_cache(users: Vec<(String, User)>) -> UserCache {
    UserCache::from_iter(users)
}

#[rstest]
fn cache_contains_user(user_cache: UserCache) {
    assert!(user_cache.contains_key("user3"));
    assert!(!user_cache.contains_key("user5"));
}

#[rstest]
fn remove_all(mut user_cache: UserCache, users: Vec<(String, User)>) {
    let keys_set: HashSet<_> = users.into_iter()
        .take(2)
        .map(|(k, _v)| k)
        .collect();

    let orig_size = user_cache.keys().len();
    user_cache.retain(|k, _v| !keys_set.contains(k));
    let new_size = user_cache.keys().len();
    assert_eq!(orig_size, new_size + keys_set.len());
}
```

In the above example, we have two fixture methods, one of which takes another
fixture as input to create a populated cache. In the `remove_all()` test, we
see it take two fixtures as input.

The `rstest` crate has a few other goodies. One thing `rstest` can do is
declare a test as taking several values as test input. It will then repeatedly
call the test method, invoking it with the specified test cases. This is done
via the `#[case]` attribute:

```rust
#[rstest]
#[case("jdoe", "John Doe", "Jane Doe")]
#[case("bob", "Bob Smith", "Bob Doe")]
#[case("claire", "Claire Smith", "Clair Doe")]
fn update_user(
    #[case] user_name: String,
    #[case] original_name: String,
    #[case] new_name: String,
) {
    let mut user = User::new(user_name, original_name);
    assert!(user.updated_dt.is_none());
    user.update_name(&new_name);
    assert!(user.updated_dt.is_some());
}
```

Specify the different test cases and annotate the test method parameters to
indicate the parameters take the test case values as input. The test parameter
names don't need to have any special name, just be annotated with `#[case]` and
the test values are inserted positionally by how they are defined in the test
method's `#[case]` annotations.

The final ability of `rstest` I'll mention is how it can test combinations of
input. You can specify multiple sets of possible input values and it will call
your test method with all the combinations. Perhaps you have a program that takes
various command-line options (maybe using the [`clap` crate](https://crates.io/crates/clap))
and you want to verify the way global command options and subcommand options
interact. You might do something like:

```rust
#[rstest]
fn check_commands(
    #[values(Command::Init, Command::New, Command::Run)] command: Command,
    #[values(CmdOption::Verbose, CmdOption::Quiet, CmdOption::DryRun)] option: CmdOption,
) {
    match command {
        // ...
    }
}
```

Use the `#[values]` attribute on test method parameters to specify the various
combinations, and the test will be executed with all the variations.

## Integration Testing

Integration testing is a bit more challenging in general than unit testing, since
you may now start adding external dependencies into the mix. Maybe this is a
messaging system like Apache Kafka, a streaming system like Apache Flink or a
database whether RDBMS like Postgres or NoSQL like MongoDb or myriad others.

Integration tests must still be automated. So how do you ensure your dependencies
are available when you tests run, do not conflict with other running services or
with each other and, like with the unit tests, are set up with appropriate data
for your test? On your local development system you can just install the dependencies
and have them always running. This is common, particularly if the dependency is a
database - we often have something like Postgres or MySQL installed. But as the
dependencies grow to include multiple services for your various integration tests,
having, say, Postgres, Kafka and Flink all installed and available can become an
issue of space can bog down your system.

Maybe you have these installed but not running continuously. Then how do you
ensure they are started before your tests and shut down afterwards? Maybe these
dependencies are Docker images, so you have containers you created. Then you
could perhaps script the container startup and shutdown via the Docker CLI. But
you still have the test fixture to set up.

One way you can address this issue of integration test dependencies is to use
a project that was initially created in the Java community but has since been
expanded to other languages - [Testcontainers](https://testcontainers.com/).

### Testcontainers

Testcontainers provides an API allowing a developer to start one or more
containers from some Docker image. This can be a pre-existing image or it can
be one you build programmatically via the `testcontainers` API. There are many
community-maintained `testcontainers` integrations for many common persistence
and messaging systems in the [testcontainers-modules](https://docs.rs/testcontainers-modules/0.13.0/testcontainers_modules/)
crate, including what we'll use in these examples, Postgres.

Using an API, in your integration tests you can start a Postgres container,
get a connection, run your tests and, using Rust drop semantics, have the
container automatically stop.

### Installing Testcontainers with Postgres

All you need to do is install `testcontainers-modules` with the `postgres` feature,
as `testcontainers-modules` re-exports the `testcontainers` modules.

`cargo add testcontainers-modules --features postgres`

### Creating A Test Database

Our production code needs a connection to the database. In our production code
we may manage this connection in some type we create that's abstracting our database
so our domain code is blissfully unaware of the database details. One method we
might have is the code to create the database connection, like so (my example
uses the [`diesel` crate](https://crates.io/crates/diesel), hence the `r2d2`
connection pooling):

```rust
pub fn establish_connection_pool() -> DbPool {
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let manager = ConnectionManager::<PgConnection>::new(database_url);

    r2d2::Pool::builder()
        .build(manager)
        .expect("Failed to create database connection pool")
}
```

But we can't use this same code because our `testcontainer` Postgres has its
own URL that we want and need to use so as not to interfere with non-test
dependencies.
So, we create a `TestDb` type for our integration tests, abstracting the setup
of the specific Postgres image.

> [!NOTE]
> One choice you have to make at this point is if you want to have your tests be
> async or not. `Testcontainers` supports either. If you do decide to use async
> then you will also need something like Tokio, and annotate your tests with
> `#[tokio::test]`. My test project is using async.

```rust
/// A struct that manages a temporary PostgreSQL container and its connection URL.
pub struct TestDb {
    pub database_url: String,
    // The container handle must be held for the database to stay alive
    #[expect(dead_code)]
    container: ContainerAsync<Postgres>,
}
```

Something else we need to consider now is how to create the database schema. I
show how to do this using `diesel`. I won't be going into details on `diesel`
(that's a whole blog in itself), so check the `diesel` docs. With `diesel` you
define your database schema and it can ensure that the schema is both created
and updated/managed over time. So for our `TestDb` we can do this when we create
the `TestDb`:

```rust
impl TestDb {
    pub async fn new() -> Self {
        // Have `testcontainers` start the Postgres database container
        let container = Postgres::default().start().await.unwrap();

        // Each container will have a distinct host:port combo, which we
        // can get from the container instance:
        let host = container.get_host().await.unwrap();
        let host_port = container.get_host_port_ipv4(5432).await.unwrap();

        // build the connection URL from the extract host and port
        let database_url = format!(
            "postgres://postgres:postgres@{}:{}/postgres",
            host, host_port
        );

        // Use `diesel` to create the database schema; this uses the production
        // database schema files (as it should, that's what we're testing!)
        TestDb::run_migrations(&database_url)
            .expect("Failed to run migrations on test DB");

        Self {
            database_url,
            container,
        }
    }

    /// Connects to the DB and applies all pending migrations.
    fn run_migrations(url: &str) -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>> {
        use diesel_migrations::{MigrationHarness, embed_migrations};

        // You must have a `migrations` directory in your project root
        const MIGRATIONS: diesel_migrations::EmbeddedMigrations = embed_migrations!();

        let mut connection = PgConnection::establish(url)?;
        connection.run_pending_migrations(MIGRATIONS)?;

        Ok(())
    }
}
```

Now that we have our database container running, we can use it in our tests. But,
we still need test data right? Using our `User` example from earlier, perhaps we
want to test the persistence of these users, rather than some simple in-memory
cache.

How can we do that? Hmmmmm....

### Testcontainers + Rstest

Why don't we use `rstest`?

How can we incorporate `rstest` here? Well, one thing we can do is to use it to
inject our `TestDb` instance into our test methods. One way you could do it is
as follows:

```rust
pub(crate) mod fixtures {
    use crate::common::TestDb;
    use rstest::fixture;

    #[fixture]
    pub async fn test_db() -> TestDb {
        TestDb::new().await
    }
}
```

I created a little module where I define my test fixture that will create my
`TestDb` so `rstest` can inject it where it's needed.

```rust
#[rstest]
#[tokio::test]
async fn test_create_session(#[future] test_db: TestDb) {
    let db = test_db.await;

    let mut conn = db.get_connection().expect("Failed to get db connection");
    let new_user = NewUser {
        email: "test@test.com".to_string(),
        username: "test".to_string(),
        password_hash: "1234".to_string(),
    };

    let user = diesel::insert_into(users::table)
        .values(&new_user)
        .get_result::<User>(&mut conn)
        .expect("Failed to create test user");

    // test production code that expects a user to be in the db
}
```

Some key things to note. As earlier, we annotate our test with `#[rstest]` but
as we're using async, we also use `#[tokio::test]`. We also need to annotate
our test parameter with `#[future]` since if you noticed, our test fixture
creating the test database was async. By annotating the test parameter with
`#[future]`, `rstest` is able to appropriately determine the type of the parameter
so that we can then call `test_db.await`. Without the annotation, the type of
`test_db` is Future but we want it's type to be `TestDb`, and so the code won't
compile without the annotation.

Also, in this current approach, a test Postgres container is created for each test.
`rstest` calls the fixture method to inject the fixture separately for each test
method. This has benefits as each test is completely isolated and there is no
cross-contamination with respect to test fixture setup. This will be a little
slower, but the testing will be safer and cleaner. If you need one container to
exist across all test methods, you can do something like:

```rust
static SHARED_TEST_DB: LazyLock<Arc<TestDb>> = LazyLock::new(|| {
    let rt = tokio::runtime::Runtime::new().unwrap();
    Arc::new(rt.block_on(TestDb::new()))
});

pub(crate) mod fixtures {
    use super::*;
    use rstest::fixture;

    #[fixture]
    pub async fn test_db() -> TestDb {
        TestDb::new().await
    }

    #[fixture]
    pub fn shared_test_db() -> Arc<TestDb> {
        Arc::clone(&SHARED_TEST_DB)
    }
}
```

and inject whichever fixture you want.

### Production vs Test Database Connections

As I showed earlier, production code may/should use connection pooling. Test code
doesn't need to. However, production code may be expecting a connection from a
connection pool. How can we structure our code so that in we have our cake and
eat it too? As they say, nothing can't be solved without another layer of
abstraction.

Originally, the production code might have called `pool.get_connection()`
explicitly using a connection pool. In our test code, we just called
`db.get_connection()`. So ... abstract the `get_connection()`.

```rust
pub trait DbConnectionProvider {
    type Connection;
    type Error;

    fn get_connection(&self) -> Result<Self::Connection, Self::Error>;
}

// production code:
pub type DbPool = Pool<ConnectionManager<PgConnection>>;

impl DbConnectionProvider for DbPool {
    type Connection = PooledConnection<ConnectionManager<PgConnection>>;
    type Error = r2d2::PoolError;

    fn get_connection(&self) -> Result<Self::Connection, Self::Error> {
        self.get()
    }
}

// test code:
impl app::utils::DbConnectionProvider for TestDb {
    type Connection = PgConnection;
    type Error = diesel::ConnectionError;

    fn get_connection(&self) -> Result<Self::Connection, Self::Error> {
        PgConnection::establish(&self.database_url)
    }
}
```

Now when we pass `TestDb` to our production code that's expecting a connection
provider, it will provide a connection directly from the database, while in
production, the implementation provides one from our connection pool provider
(`r2d2` from `diesel` in my example).

## Conclusion

Testing is hard. Test code benefits from the same thought, detail and rigor you
put into write production code. And just as there are crates to help you write
good production code, knowing and utilizing the crates available for your test
code will make the experience much better. The main thing though is to write those
tests, at all levels.

Happy testing!
