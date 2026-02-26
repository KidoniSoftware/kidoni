---
title: Using chezmoi part 2 - Templates
description: chezmoi has a robust templating system; let's see how to use it
date: 2025-04-07
tags:
  - blog
  - chezmoi
  - dotfiles
draft: false
---

In my previous post on [chezmoi](using-chezmoi.md) I gave an introduction on the
basic setup and usage. There is a lot more you can do with `chezmoi`, particularly
if you're using it across different computers you use. For example, maybe you
have separate computers for work and at home, or maybe you have one computer
that's a Windows machine and one that's MacOS and another one that's Linux.
Perhaps you have multiple Linux machines but you want the config to be slightly
different. `chezmoi`has you covered.

The full documentation for `chezmoi` templates is [here](https://www.chezmoi.io/user-guide/templating/).

## Template Basics

`chezmoi` keeps templates in a directory `.chezmoitemplates` or as files with a
.tmpl extension. In practice, I'd say the former is for pieces of templates you
want to include in other templates (I'll show that later) whereas the latter is
used for the "final" file that's your actual config file e.g. `.zshrc.tmpl`
(or really `dot_zshrc.tmpl` as it's managed by `chezmoi` in it's source
directory.

Templates in chezmoi use the `Go` language template syntax. `chezmoi` also has
custom functions it's created as well as using functions from [sprig](https://masterminds.github.io/sprig/).
You can use branching logic with if/else and there are various boolean logic
comparisons like 'not equal', 'greater than', etc.

## Creating A Template

There are a few ways to create a template.

### Empty Template

If you want to create a new empty template just do so manually in the
`.chezmoitemplates` directory:

```sh
$ chezmoi cd
# if needed, `mkdir .chezmoitemplates`
$ cd .chezmoitemplates
$ vi mytemplate
```

Template files in `.chezmoitemplates` do not need any special extension.

### Adding A New File To Manage

If you're adding a new file for `chezmoi` to manage, pass `--template` when
adding the file:

```sh
chezmoi add --template ~/.gitconfig
```

This will create a file `dot_gitconfig.tmpl` in the `chezmoi` source directory.

### Turning An Existing File Into A Template

If you want to make a file that is already managed by `chezmoi` into a template,
you use the `chezmoi chattr` command:

```sh
chezmoi chattr +template ~/.zshrc
```

This will change `dot_zshrc` into `dot_zshrc.tmpl`.

## Using Template Data And Syntax

Now that we have a template file, let's see some examples of leveraging the
template language and available data and functions to customize our configuration.

### Template Data

`chezmoi` exposes many data attributes from your system. For a full list, use
the `chezmoi data` command:

```sh
chezmoi data
```

This will output a lot of content in JSON format. Among it all, things like the
host name, operating system, properties of the operating system (name, version, etc)
are probably the most useful, but use cases vary. To access any of these data
values, you use a path-like syntax, similar to what you might use with `jq`.

```text
{{ .chezmoi.hostname }} {{ .chezmoi.os }}
```

{{% callout type="tip" %}}
A quick and easy way to test your template expressions with with the
`chezmoi execute-template` command.
{{% /callout %}}


```sh
$ chezmoi execute-template "host: {{ .chezmoi.hostname }} os: {{ .chezmoi.os }}"
host: kidoni os: linux
```

#### Custom (user-defined) Data

You can also create your own data values to use in your templates. You place
these in your `chezmoi` configuration file e.g. `~/.config/chezmoi/chezmoi.toml`.
Place any custom data attributes you want in a `[data]` section in `chezmoi.toml`.
You then access them in the template with the same dot syntax.

```toml
[data]
myvar = "foo"
mycnt = 10
```

```sh
$ chezmoi execute-template "var: {{ .myvar }}  cnt: {{ .mycnt }}"
var: foo  cnt: 10
```

You can also "nest" your custom data fields:

```toml
[data.foo]
cnt = 10
[data.bar]
name = "ray"
```

```sh
$ chezmoi execute-template "cnt: {{ .foo.cnt }}  name: {{ .bar.name }}"
cnt: 10  name: ray
```

## Template Logic And Functions

We can create our templates and we can access data, so now let's put in some logic
to control what we configure based on the various data available.

First, I'm going to configure my `~/.gitconfig` global Git configuration so that
on Windows I sign my commits using SSH while on my MacOS and Linux systems I use
PGP.

```sh
chezmoi chattr +template ~/.gitconfig
chezmoi edit ~/.gitconfig
```

{{% callout type="note" %}}
Obviously leave off the `chattr` if you've already made the file into a template
{{% /callout %}}


In the `.gitconfig` edit the `[user]` section:

```text
[user]
{{ if eq .chezmoi.os "windows" }}
    signingkey = ssh-ed25519 xxx
{{ else if eq .chezmoi.os "linux" "darwin" }}
    signingkey = 25Bxxxxxxxxxxxx
{{ end }}
```

The branching is done using `if/else if` and if needed there is also just `else`.
The branching is terminated by the `end` statement. You can see the boolean logic
operator `eq` for comparing the variable `.chezmoi.os` with the values. One thing
to call out is the `else if` branch logic. Note that it is checking for both
Linux and MacOS in the one condition. The `chezmoi` template language will test
the variable against the provided values with an implicit `or`.

Speaking of `or` you can use both `and` and `or` operators. For example, if I
have two Linux systems with different host names, I can do something like

```text
[user]
{{ if (and (eq .chezmoi.os "linux") (eq .chezmoi.hostname "kidoni")) }}
    email = "ray@kidoni.dev"
{{ else if (and (eq .chezmoi.os "linux") (eq .chezmoi.hostname "work")) }}
    email = "ray@bogus.com
{{ end }}
```

### Using Sprig Functions

As mentioned, you can use any of the `sprig` functions in your templates. There
are a lot of functions and a lot of use cases, so I won't spend time trying to
come up with anything fancy. It's easy to test the functions using `chezmoi execute-template`
as mentioned earlier. Just a few quick examples ...

```sh
$ chezmoi execute-template "{{ upper .chezmoi.arch }}"
AMD64
$ chezmoi execute-template "{{ trunc 6 .chezmoi.version.commit }}"
48865
$ chezmoi execute-template '{{ replace  "/" "\\" .chezmoi.sourceDir}}'
\home\ray\.local\share\chezmoi
```

## Combining Fragments Into A Larger Template

As mentioned at the start, you can put files in `.chezmoitemplates` and one
use for that is to store pieces of templates that you want to include into
another template, perhaps for re-use.

To do this, name the file whatever you want, just put it in `.chezmoitemplates`.
To include a file into a template, you use the `template` command.

Let's go back to the example of different home and work systems, differentiated
by host name. I have some shell configuration I want only at home, some only at
work, and some in both. So I create three files in `.chezmoitemplates`

```sh
$ ls -1 .chezmoitemplates
 common
 home
 work

$ bat *
───────┬──────────────────────────────────────────
       │ File: common
───────┼──────────────────────────────────────────
   1   │ # starship https://starship.rs/
   2   │ eval "$(starship init zsh)"
───────┴──────────────────────────────────────────
───────┬──────────────────────────────────────────
       │ File: home
───────┼──────────────────────────────────────────
   1   │ # atuin configuration
   2   │ if [ -e $HOME/.atuin/bin/env ]; then
   3   │   . "$HOME/.atuin/bin/env"
   4   │ fi
   5   │ eval "$(atuin init zsh)"
   6   │
───────┴──────────────────────────────────────────
───────┬──────────────────────────────────────────
       │ File: work
───────┼──────────────────────────────────────────
   1   │ . "$HOME/.deno/env"
───────┴──────────────────────────────────────────
```

Now I can create a template that includes these, based on which system I'm on.

```sh
$ bat -p setup.sh.tmpl
{{ if eq .chezmoi.hostname "kidoni" }}
{{ template "home" }}
{{ else if eq .chezmoi.hostname "work" }}
{{ template "work" }}
{{end}}
{{ template "common" }}

$ chezmoi execute-template < setup.sh.tmpl

# atuin configuration

if [ -e $HOME/.atuin/bin/env ]; then
. "$HOME/.atuin/bin/env"
fi
eval "$(atuin init zsh)"

# starship <https://starship.rs/>

eval "$(starship init zsh)"
```

## Wrapping Up

The templating system in `chezmoi` is pretty robust and with custom data fields
via the `chezmoi` config file, you can do quite a lot.

There's also much more you can do with `chezmoi`. One of those is its ability to
integrate with password managers. This is something I will cover in a subsequent
blog post.
