---
title: 
description: 
created: 
tags:
  - blog
draft: true
---

<div>

# Building cloud software? Don't forget about this ... {#building-cloud-software-dont-forget-about-this .p-name}

</div>

::: {.section .p-summary field="subtitle"}
When developers set out to architect a piece of software --- whether a
brand new green-field project or rearchitecting an existing product
---...
:::

::: {.section .e-content field="body"}
::: {#18e8 .section .section .section--body .section--first .section--last}
::: section-divider

------------------------------------------------------------------------
:::

::: section-content
::: {.section-inner .sectionLayout--insetColumn}
### Building cloud software? Don't forget about this ... {#4760 .graf .graf--h3 .graf--leading .graf--title name="4760"}

<figure id="00f5" class="graf graf--figure graf-after--h3">
<img src="https://cdn-images-1.medium.com/max/800/0*bKjodxUoX6azqniD"
class="graf-image" data-image-id="0*bKjodxUoX6azqniD" data-width="5568"
data-height="3712" data-unsplash-photo-id="v9FQR4tbIq8"
data-is-featured="true" />
<figcaption>Photo by <a
href="https://unsplash.com/@kellysikkema?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com/@kellysikkema?utm_source=medium&amp;utm_medium=referral"
rel="photo-creator noopener" target="_blank">Kelly Sikkema</a> on <a
href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
class="markup--anchor markup--figure-anchor"
data-href="https://unsplash.com?utm_source=medium&amp;utm_medium=referral"
rel="photo-source noopener" target="_blank">Unsplash</a></figcaption>
</figure>

When developers set out to architect a piece of software --- whether a
brand new green-field project or rearchitecting an existing
product --- the typical considerations are things like

-   [should I use microservices and how many]{#a805}
-   [how will these microservices communicate]{#9b38}
-   [how will data persist]{#a1fe}
-   [what guarantees must be provided for messages flowing through the
    system]{#fa8e}
-   [what's encrypted, where and when]{#0966}
-   [etc.]{#0212}

Boxes and lines start appearing on whiteboards (physical or virtual) ...
here are the N microservices, we'll use gRPC here, we'll use Kafka there
and MongoDb will save everything. We'll deploy to Kubernetes, set up
deployments with
[HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/){.markup--anchor
.markup--p-anchor
data-href="https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"
rel="noopener" target="_blank"}, have at least 3 instances so our brain
doesn't get split, and monitor with the EFK stack. Great! Let's write
some code.

Some notion of the performance requirements will be
considered --- "we'll use autoscaling" --- as will considerations of
data loss --- "Kafka won't lose anything so data will still be there if
we crash." But how often is it taken to the next level?

> Specifically, how often is capacity planning considered at this
> architecture stage?

Like a lot of things in software development, the longer you wait to
address issues, the harder it is to address them. This applies as much
to code bugs as architecture "bugs." Take a simple example: "we'll use
autoscaling" to address load. That's fine unless you find that you need
to handle 10,000 requests per second (RPS) on average and your
microservice can only do 100 RPS, so your base number of instances is
100 before "autoscaling" to meet peak demand. In and of itself, this
isn't necessarily a problem. But it could add up ... what about your
other microservices, databases, message brokers?

Consider another aspect of this. Let's say you have an API with your
clients that once they send you a message and you acknowledge receipt,
you guarantee it will be processed. Let's further assume this same
average 10,000 RPS. What happens if your service is degraded for some
reason, say one of your three zones goes down and you've lost 1/3 of
your capacity. Your other zones will hopefully get the signal to start
scaling up. But that might take a few minutes. At 10,000 RPS you'll have
1,000,000 messages piled up after 5 minutes ... *assuming your two
remaining zones are still keeping up with their own load*. What if your
data needs to be processed in some order? You'll have to be able to work
down the backlogged messages. How much extra capacity will that take,
for how long?

And what about the data on disk? Whether this is Kafka or MongoDb or
other cluster-based systems, or even non-cluster systems that replicate
data whether for availability or performance or both (say MySQL with
several read replicas), your data storage requirements is multiplied by
some factor and then multiplied again based on retention requirements.
And the same data is doing to be stored in several different systems
potentially. If requests come into your system and are placed in a Kafka
topic you're generally going to have 3 copies right there (original plus
two replicas). This will remain there for as long as the retention
policy states (default 7 days). Depending on how you have your
microservices interacting, this might be sent on to more than one other
Kafka topic for processing by other microservices. The requests are
saved in MongoDb, which will have at least two copies.

Obviously then, for each request received you're actually storing N
copies, which you need to take into account. Storage is cheap but not
free. Moving the data around the network for these replicas requires
bandwidth, and depending on the cloud provider moving data across zones
and definitely regions costs money.

Doing a lot of these calculations can be (relatively)
straightforward --- if you prescribe the format of the data. But what
if --- as with many enterprise systems --- data models are flexible. If
a customer can send you data of variable size, you now need to account
for that in your capacity planning.

So now you've done all the math and figured out the storage you need,
and the number of instances of the microservices which you've mapped to
some number of physical nodes and the RAM and the types of storage (e.g.
spinning disk, SSD) and punched that into some spreadsheet perhaps
provided by your cloud provider and voila, \$X per month or year or
whatever.

If \$X is actually reasonable to your business, good on ya. But if it
isn't --- and you have only done this calculation towards the end of the
project when the business guys are finalizing a pricing strategy, sales
materials, etc. ... well, figuring out how to fix it and then fixing it
is going to be a lot harder than if you'd thought through this as you
were architecting the solution. And it certainly will take longer to
address, while at the same time the deadline is fast approaching or
already passed.

So, in addition to thinking about things like microservices, messaging,
persistence, security and the other usual suspects, don't forget about
capacity related impacts and costs to the architecture. At the very
least, the business guys won't be surprised at the cost and everyone can
work together for the best balance.

Not like this has ever happened to me or anything!
:::
:::
:::
:::

By [Ray Suliteanu](https://medium.com/@raysuliteanu){.p-author .h-card}
on [March 22, 2021](https://medium.com/p/fc8137df2d0d).

[Canonical
link](https://medium.com/@raysuliteanu/building-cloud-software-dont-forget-about-this-fc8137df2d0d){.p-canonical}

Exported from [Medium](https://medium.com) on December 9, 2024.
