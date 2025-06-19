---
title: What Most Get Wrong About Software Quality Assurance
description: Most SQA teams are not actually doing quality assurance.
date: 2025-06-12
tags:
  - blog
  - software
  - programming
  - testing
  - quality-assurance
draft: true
---

Those of us of a certain age who grew up in a certain place might remember
watching cartoons as a kid on the weekends -- the Looney Tunes. It was a ritual
for my sister and me, first thing Saturday morning, going to the family room,
turning on the TV -- by hand -- and changing the channel -- by hand -- using a
dial -- yes an analog round nob with only a dozen channels or so. For some
reason, one of the cartoons that stuck with me had a [scene](https://www.youtube.com/watch?v=lJKcdlj-Uiw)
where the "waskaly wabbit" as one character used to call him, was stuck on an
assembly line. His job was to check whether bombs were duds or not, by smacking
each bomb as it passed with a hammer. Obviously not the most effective method.

I mention this because what was he doing, testing those bombs? He was doing
"quality _control_". Wikipedia [defines](https://en.wikipedia.org/wiki/Quality_control)
quality control as:

> Quality control (QC) is a process by which entities review the quality of all
> factors involved in production. ISO 9000 defines quality control as "a part of
> quality management focused on fulfilling quality requirements"

A "control" is essentially a metric, some (hopefully quantitative) measure that
can be compared to whatever quality standards have been defined (again, hopefully).
It is a test of an _output_ or outputs. In terms of building software products,
this is often defined as some number of allowed defects. Perhaps a team or
organization might have a control such as

| Severity | Count |
| -------- | ----- |
| Critical | 0     |
| High     | 0     |
| Medium   | <10   |
| Low      | <50   |

Decisions about whether to release the software to customers is based on whether
the defect count by severity meets this quality control. But this is an output.
And it is validated when release decisions are made. Old school waterfall software
development methods would have this after months or even years of work. More
recent agile methods might have this in days or weeks. Some Software-as-a-Service
and Web products do away with this completely as they release multiple times a day.

Metrics based on outputs are also subject to "gaming" and manipulation. For example,
as the release criteria are reviewed, it's easy to ask "Is this 'high' defect
_really_ 'high'?" Just making it a 'Medium' could result in meeting the release
criteria.

The bottom line is, the "QA" team(s) are really doing quality control, not quality
assurance. Quality control is a reactive process. Checking outputs is reactive.
Quality Assurance (QA) on the other hand is about inputs. And it's about inputs
at all levels and stages of product development.

## Quality Assurance

Assuring product quality starts at the very beginning of any project. Should the
project even be "green lit"? Is there a business case? Who are the competitors?
How does the product stand out? Yada.

Clear business requirements need to be defined.
