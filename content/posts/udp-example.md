---
title: Quick bytes - using UDP in Rust
description: a simple example using UDP to send and receive data with Rust
date: 2025-04-01
tags:
  - blog
  - rust
  - programming
  - udp
  - networking
  - quick-bytes
draft: false
---

{{< callout type="info" >}}
This is the first post where I'm doing "quick bytes" of simple examples with
Rust. This is both a way for me to keep track of some basic usage of various
Rust-isms, but also a way for me to share that in case it's helpful. I could
just leave these as notes in my [Obsidian](https://obsidian.md/) vault, but
why not share!
{{< /callout >}}


## UDP

The [User Datagram Protocol (UDP)](https://en.wikipedia.org/wiki/User_Datagram_Protocol)
is the lesser known sibling of the [Transmission Control Protocol (TCP)](https://en.wikipedia.org/wiki/Transmission_Control_Protocol).
The simple difference is TCP is guaranteed and UDP is not. What I mean is, UDP
is like "fire and forget" and TCP has a whole retry mechanism. There are of
course other differences, but that's what I see as key to understand. UDP is
also used for "multicast" where a packet is broadcast to multiple recipients.

## UDP in Rust

Rust implements UDP in the standard library with `std::net::UdpSocket`. You
bind the socket to an IP address and port, and then you can send and receive
data on that port at that address. If you want to send data to another UDP
socket, you bind to that address and port, then connect one to the other.

Obviously the typical usage would be for sending messages between processes. In
this simple "quick byte" example though, I will just send
a message between threads in the same process. Ignoring the threading aspects
and focusing on the UDP parts, notice that I'm using `0` as the port in the
IP address: `127.0.0.1:0`. This tells the OS to pick a random port for me (and
of course `127.0.0.1` is the localhost address). Because the port is randomly
assigned, I use the `local_addr()` method to find the port of the "server"
so I can connect the `udp_client` to the `udp_server`. Everything else should be
pretty self-explanatory ... use `recv_from(&mut buf)` to read data and use
`send_to(&buf, addr)` to send data. The receive method doesn't require an address
because it reads from the port it's bound to. However, sending data requires the
address where to send, since that can obviously be anywhere.

{{< callout type="important" >}}
For the simple example I just return errors from the `main()` method and use
the `?` shortcut to return errors. Naturally in a "real" program you would use
error handling best practices.
{{< /callout >}}


```rust
use std::{error::Error, net::UdpSocket, thread};

fn main() -> Result<(), Box<dyn Error>> {
    let udp_client = UdpSocket::bind("127.0.0.1:0")?;
    let udp_server = UdpSocket::bind("127.0.0.1:0")?;
    let addr = udp_server.local_addr()?;
    udp_client.connect(addr)?;

    println!("client: {:?}", udp_client);
    println!("server: {:?}", udp_server);

    thread::spawn(move || {
        let mut buf = [0u8; 1024];
        let (sz, addr) = udp_server
            .recv_from(&mut buf)
            .expect("error reading from client");
        println!("server: read {sz} bytes");
        udp_server.send_to(&buf[..sz], addr)
    });

    let sz = udp_client.send_to("hello, world".as_bytes(), addr)?;
    println!("client: wrote {sz} bytes");

    let mut buf = [0u8; 1024];
    let (sz, _addr) = udp_client
        .recv_from(&mut buf)
        .expect("error reading from client");
    println!("client: read {sz} bytes");

    Ok(())
}
```

And there you have it. Since this is the first "quick byte" please let me know
if you like this format.
